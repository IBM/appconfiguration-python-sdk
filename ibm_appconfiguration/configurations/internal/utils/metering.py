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
This module provides methods that perform metering and usage related operations.
"""
from threading import Lock, Timer
from datetime import datetime
from .api_manager import APIManager
from .logger import Logger
from ..common import config_messages, config_constants


class Metering:
    """Class to send the metering data."""
    __send_interval = 600
    __instance = None

    @staticmethod
    def get_instance():
        """ Static access method. """
        if Metering.__instance is None:
            return Metering()
        return Metering.__instance

    def __init__(self):
        """ Virtually private constructor. """
        if Metering.__instance is not None:
            raise Exception("Metering " + config_messages.SINGLETON_EXCEPTION)
        self.__metering_url = None
        self.__repeating = True
        self.__lock = Lock()
        self.__metering_feature_data = dict()
        self.__metering_property_data = dict()
        Metering.__instance = self
        self.send_metering()

    def set_repeat_calls(self, repeat):
        """Set the send_metering repeating task

        Args:
            repeat: Bool to set the repeat task.
        """
        self.__repeating = repeat

    def set_metering_url(self, url: str):
        """Set the metering url

        Args:
            url: Url for the metering.
        """
        self.__metering_url = url

    def add_metering(self, guid: str, environment_id: str,
                     collection_id: str, entity_id: str,
                     segment_id: str, feature_id: str = None,
                     property_id: str = None):
        """ Add the Metering values.

        Args:
            guid: GUID of the App Configuration service. Get it from the service credentials section of the dashboard.
            environment_id: Id of the environment created in App Configuration service instance.
            collection_id: Id of the collection created in App Configuration service instance.
            entity_id: Id of the Entity.
            segment_id: Id of the Segment.
            feature_id: Id of the Feature.
            property_id: Id of the Property.
        """

        self.__lock.acquire()
        try:
            time = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
            feature_json = {
                'count': 1,
                'evaluation_time': time
            }

            modify_metering_data = self.__metering_feature_data if property_id is None else self.__metering_property_data
            modify_id = feature_id if property_id is None else property_id

            if guid in modify_metering_data:
                if environment_id in modify_metering_data[guid]:
                    if collection_id in modify_metering_data[guid][environment_id]:
                        if modify_id in modify_metering_data[guid][environment_id][collection_id]:
                            if entity_id in modify_metering_data[guid][environment_id][collection_id][modify_id]:
                                if segment_id in modify_metering_data[guid][environment_id][collection_id][modify_id][entity_id]:
                                    modify_metering_data[guid][environment_id][collection_id][modify_id][entity_id][segment_id]['evaluation_time'] = time
                                    count = modify_metering_data[guid][environment_id][collection_id][modify_id][entity_id][segment_id]['count']
                                    modify_metering_data[guid][environment_id][collection_id][modify_id][entity_id][segment_id]['count'] = count + 1
                                else:
                                    modify_metering_data[guid][environment_id][collection_id][modify_id][entity_id][segment_id] = feature_json
                            else:
                                modify_metering_data[guid][environment_id][collection_id][modify_id][entity_id] = {
                                    segment_id: feature_json
                                }
                        else:
                            modify_metering_data[guid][environment_id][collection_id][modify_id] = {
                                entity_id: {
                                    segment_id: feature_json
                                }
                            }
                    else:
                        modify_metering_data[guid][environment_id][collection_id] = {
                            modify_id: {
                                entity_id: {
                                    segment_id: feature_json
                                }
                            }
                        }
                else:
                    modify_metering_data[guid][environment_id] = {
                        collection_id: {
                            modify_id: {
                                entity_id: {
                                    segment_id: feature_json
                                }
                            }
                        }
                    }
            else:
                modify_metering_data[guid] = {
                    environment_id: {
                        collection_id: {
                            modify_id: {
                                entity_id: {
                                    segment_id: feature_json
                                }
                            }
                        }
                    }
                }
        finally:
            self.__lock.release()

    def __send_to_server(self, guid, data):
        if self.__repeating:
            api_manager = APIManager.get_instance()
            response = api_manager.prepare_api_request(method="POST",
                                                       url=self.__metering_url,
                                                       data=data)
            status_code = response.get_status_code()
            if status_code == 202:
                Logger.info("Successfully posted metering data")
            else:
                Logger.error(f'Failed to send the metering data. Reason - {response.get_result()}')
                """schedule a function to send the same payload after 10 minutes"""
                if status_code is None:
                    """
                    status_code will be None in-case of

                        1. request was retried for [429, 500, 502, 503, 504] status codes which has exceeded the retry count and has raised the exception "requests.exceptions.RetryError".
                        Check api_manager.py for more info.
                        2. request failed due to unknown "Exception".
                    """
                    retry_metering = Timer(self.__send_interval, self.__send_to_server, args=(guid, data))
                    retry_metering.daemon = True
                    retry_metering.start()

    def __build_request_body(self, send_metering_data: dict, result: dict, main_key: str):

        for guid, guid_map in send_metering_data.items():
            if guid not in result:
                result[guid] = []
            for environment_id, environment_map in guid_map.items():
                for collection_id, collection_map in environment_map.items():
                    collections_map = {
                        'collection_id': collection_id,
                        'environment_id': environment_id,
                        'usages': []
                    }
                    for feature_id, feature_map in collection_map.items():
                        for entity_id, entity_map in feature_map.items():
                            for segment_id, segment_map in entity_map.items():
                                feature_json = {
                                    main_key: feature_id,
                                    'entity_id': None if entity_id == config_constants.DEFAULT_ENTITY_ID else entity_id,
                                    'segment_id': None if segment_id == config_constants.DEFAULT_SEGMENT_ID else segment_id,
                                    'evaluation_time': segment_map['evaluation_time'],
                                    "count": segment_map['count']
                                }
                                collections_map['usages'].append(feature_json)
                    result[guid].append(collections_map)

    def send_metering(self):
        """Send the metering."""
        if self.__repeating:
            timer = Timer(self.__send_interval, self.send_metering)
            timer.daemon = True
            timer.start()

        self.__lock.acquire()
        try:
            send_feature_data = self.__metering_feature_data
            send_property_data = self.__metering_property_data
            self.__metering_feature_data = dict()
            self.__metering_property_data = dict()
        finally:
            self.__lock.release()

        if len(send_feature_data) <= 0 and len(send_property_data) <= 0:
            return None

        result = dict()

        if len(send_feature_data) > 0:
            self.__build_request_body(send_feature_data, result, 'feature_id')
        if len(send_property_data) > 0:
            self.__build_request_body(send_property_data, result, 'property_id')

        for guid, values in result.items():
            for data in values:
                count = len(data['usages'])
                if count > config_constants.DEFAULT_USAGE_LIMIT:
                    self.__send_split_metering(guid, data, count)
                else:
                    self.__send_to_server(guid=guid, data=data)
        return result

    def __send_split_metering(self, guid: str, data: dict, count: int):
        limit = 0
        while limit < count:
            collections_map = {
                'collection_id': data['collection_id'],
                'environment_id': data['environment_id'],
                'usages': data['usages'][limit:limit + config_constants.DEFAULT_USAGE_LIMIT]
            }
            self.__send_to_server(guid=guid, data=collections_map)
            limit += config_constants.DEFAULT_USAGE_LIMIT
