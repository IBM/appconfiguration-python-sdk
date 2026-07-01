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
Utility module for handling progressive rollout configurations.
"""

from datetime import datetime
from sortedcontainers import SortedDict
from .logger import Logger


def parse_rollout_configuration_phases(configuration: dict) -> SortedDict:
    """
    Parse progressive rollout phases into a SortedDict for efficient timestamp-to-percentage lookups.
    
    Args:
        configuration: Rollout configuration dict with 'start_at' and 'phases' keys
        
    Returns:
        SortedDict with timestamps (ms) as keys and percentages as values, or None if parsing fails
    """
    if not configuration or 'start_at' not in configuration or 'phases' not in configuration:
        return None
    
    if not isinstance(configuration['phases'], list) or len(configuration['phases']) == 0:
        return None
    
    try:
        # Parse start timestamp
        start_time = datetime.fromisoformat(configuration['start_at'].replace('Z', '+00:00'))
        transition_time = int(start_time.timestamp() * 1000)  # Convert to milliseconds
        
        # Create SortedDict for efficient lookups
        result = SortedDict()
        result[0] = 0
        
        # Duration multipliers in milliseconds
        multipliers = {
            'days': 86400000,  # days
            'hours': 3600000,  # hours
            'minutes': 60000,  # minutes
        }
        
        for phase in configuration['phases']:
            if not isinstance(phase, dict) or 'percentage' not in phase:
                continue
            
            # Add phase entry
            result[transition_time] = phase['percentage']
            
            # Calculate next transition time if duration is specified
            duration = phase.get('duration')
            if duration:
                transition_time += multipliers.get(phase.get('duration_type')) * duration

        return result
    
    except (ValueError, AttributeError) as e:
        Logger.error(f"Invalid start_at timestamp: {configuration.get('start_at')}, error: {str(e)}")
        return None
    except Exception as e:
        Logger.error(f"Error parsing rollout configuration: {str(e)}")
        return None


def get_current_rollout_percentage(rollout_map: SortedDict) -> int:
    """
    Returns the current rollout percentage based on current time.
    
    Args:
        rollout_map: SortedDict containing timestamp-to-percentage mappings
        
    Returns:
        The current rollout percentage, or 0 if rollout_map is None or empty
    """
    if not rollout_map or len(rollout_map) == 0:
        return 0
    
    current_time = int(datetime.now().timestamp() * 1000)  # Current time in milliseconds
    
    # Find the entry with the largest timestamp that is <= current_time
    # SortedDict.bisect_right returns the index where current_time would be inserted
    # We want the item just before that position
    idx = rollout_map.bisect_right(current_time)
    if idx > 0:
        key = rollout_map.keys()[idx - 1]
        return rollout_map[key]
    
    return 0
