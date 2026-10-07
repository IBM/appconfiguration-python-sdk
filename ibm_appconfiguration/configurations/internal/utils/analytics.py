# Copyright 2021 IBM All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
This module provides methods that perform analytics related operations.
"""
from datetime import datetime, timezone
from threading import Event, Lock, Thread
from time import time
from typing import Any

from ibm_appconfiguration.configurations.internal.common import config_messages
from ibm_appconfiguration.configurations.internal.utils.analytics_record import AnalyticsRecord, EventType
from ibm_appconfiguration.configurations.internal.utils.api_manager import APIManager
from ibm_appconfiguration.configurations.internal.utils.logger import Logger


class Analytics:
    """Class to send the Analytic data.

    Thread-safety model
    -------------------
    One lock (``__record_lock``) serialises all reads and writes on
    ``__record``.  ``AnalyticsRecord`` itself is intentionally NOT
    thread-safe — the lock lives here so we can do atomic check-then-act
    sequences (e.g. *exceeds_limit → split_head*) without TOCTOU gaps.

    A second lock (``__flush_lock``) ensures that at most one thread is
    running the drain/flush pipeline at a time.  This prevents the
    background job and a concurrent ``flush()`` call from both splitting
    the same data and sending it twice.
    """

    __send_interval = 5 * 60  # mandatory flush every 5 minutes
    __batch_size = 30         # max usages the server accepts per request
    __instance = None

    @staticmethod
    def get_instance():
        """ Static access method. """
        if Analytics.__instance is None:
            return Analytics()
        return Analytics.__instance

    def __init__(self):
        """ Virtually private constructor. """
        if Analytics.__instance is not None:
            raise Exception("Analytics " + config_messages.SINGLETON_EXCEPTION)
        self.__environment_id = None
        self.__collection_id = None
        self.__analytics_url = None
        # Guards all access to __record.
        self.__record_lock = Lock()
        self.__record = AnalyticsRecord()
        self.__job_flag = False
        # Wakes the background flush thread early (batch-full or stop).
        self.__flush_event = Event()
        # Serialises concurrent drain/flush pipelines (background vs flush()).
        self.__flush_lock = Lock()
        Analytics.__instance = self

    def set_context(self, environment_id: str, collection_id: str):
        self.__environment_id = environment_id
        self.__collection_id = collection_id

    def set_analytics_url(self, url: str):
        """Set the analytics url."""
        self.__analytics_url = url

    def add_metric(self, metric: dict[str, Any], metric_type: EventType):
        metric["timestamp"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        with self.__record_lock:
            self.__record.add(metric, metric_type)
            if self.__record.exceeds_limit(Analytics.__batch_size):
                self.__flush_event.set()

    def __send_to_server(self, record: AnalyticsRecord, previous_delay: int = 0) -> int:
        """POST *record* to the server.  Returns 0 on success or seconds to
        wait before retrying."""
        api_manager = APIManager.get_instance()
        response = api_manager.prepare_api_request(
            method="POST",
            url=self.__analytics_url,
            data=record.get_request_body(self.__environment_id, self.__collection_id)
        )
        status_code = response.get_status_code()
        if 200 <= status_code < 300:
            Logger.info("Successfully posted analytics data")
            return 0
        if status_code == 429:
            Logger.warning("Analytics endpoint has been rate-limited, retrying after 30 sec")
            return 30
        next_delay = min(600, previous_delay * 2 if previous_delay > 0 else 60)
        Logger.error(f"Error while posting analytics data, retrying after {next_delay}sec")
        return next_delay

    def __send_batch(self, batch: AnalyticsRecord):
        """Send *batch* with retry + merge-back on failure.

        On each failure:
          1. Merge the failed batch back into the live record (under lock)
             so no data is stranded while we sleep.
          2. Sleep for the back-off delay (woken early by flush_event).
          3. Re-split from the now-merged (and possibly larger) live record
             so any entries added during the sleep are included next time.
        """
        if len(batch) == 0:
            return
        previous_delay = 0
        while True:
            delay = self.__send_to_server(batch, previous_delay)
            if delay == 0:
                return
            # Merge back before sleeping so data is never orphaned.
            with self.__record_lock:
                self.__record.merge(batch)
            previous_delay = delay
            self.__flush_event.wait(timeout=delay)
            self.__flush_event.clear()
            # Re-split including any entries that arrived during the sleep.
            # Guard: if another flush() drained the record while we slept,
            # there is nothing left to send — exit cleanly.
            with self.__record_lock:
                if len(self.__record) == 0:
                    return
                batch = self.__record.split_head(Analytics.__batch_size)

    def __drain_chunks(self):
        """Send all full batches (≥ batch_size) one at a time, oldest first.

        Must be called while holding ``__flush_lock``.
        Leaves any remainder below batch_size in the live record.
        """
        while True:
            with self.__record_lock:
                if not self.__record.exceeds_limit(Analytics.__batch_size):
                    break
                batch = self.__record.split_head(Analytics.__batch_size)
            self.__send_batch(batch)

    def __flush_remainder(self):
        """Send whatever is left in the record (< batch_size entries).

        Must be called while holding ``__flush_lock``.
        """
        with self.__record_lock:
            n = len(self.__record)
            if n == 0:
                return
            batch = self.__record.split_head(n)
        self.__send_batch(batch)

    def __send_analytic_job(self):
        last_flush = time()

        while self.__job_flag:
            remaining = Analytics.__send_interval - (time() - last_flush)
            # Skip sleep entirely when the record is already at the limit.
            with self.__record_lock:
                already_full = self.__record.exceeds_limit(Analytics.__batch_size)
            if remaining > 0 and not already_full:
                self.__flush_event.wait(timeout=remaining)
                self.__flush_event.clear()

            if not self.__job_flag:
                break

            five_min_due = (time() - last_flush) >= Analytics.__send_interval

            # Re-check under lock — state may have changed while we slept.
            with self.__record_lock:
                is_full = self.__record.exceeds_limit(Analytics.__batch_size)
                has_data = len(self.__record) > 0

            if is_full:
                with self.__flush_lock:
                    self.__drain_chunks()
            elif five_min_due and has_data:
                with self.__flush_lock:
                    self.__flush_remainder()
            last_flush = time()
            # Woken early but record < batch_size and 5-min not due: loop
            # back and sleep for the remaining interval.

    def start(self):
        if self.__job_flag:
            return
        self.__job_flag = True
        Thread(target=self.__send_analytic_job, daemon=True).start()

    def stop(self):
        self.__job_flag = False
        self.__flush_event.set()  # unblock any active sleep

    def flush(self):
        """Immediately flush all pending analytics data.

        Safe to call concurrently with the background job — ``__flush_lock``
        ensures only one drain/flush pipeline runs at a time.
        """
        with self.__flush_lock:
            self.__drain_chunks()
            self.__flush_remainder()
