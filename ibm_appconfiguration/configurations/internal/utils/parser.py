import json
from typing import Any, Dict, List, Set


def extract_environment_data(data: Dict[str, Any], environment_id: str) -> Dict[str, Any]:
    """
    Prepares config data for extraction with validation.

    :param data: The full JSON configuration as a dictionary.
    :param environment_id: The environment ID to extract.
    :return: A dictionary containing 'features', 'properties', and 'segments'.
    :raises: Exception if the format is invalid or environment not found.
    """
    if not isinstance(data.get("segments"), list) or not isinstance(data.get("environments"), list):
        raise Exception("Improper Data format present in configuration")

    for environment in data["environments"]:
        if environment.get("environment_id") == environment_id:
            return {
                "features": environment.get("features", []),
                "properties": environment.get("properties", []),
                "segments": data["segments"]
            }

    raise Exception("Matching environment not found in configuration")


def validate_resource(resource: Dict[str, Any], collection: str) -> bool:
    """
    Validates if the feature/property belongs to the given collection.

    :param resource: The feature or property dictionary.
    :param collection: The collection ID to match.
    :return: True if valid, False otherwise.
    :raises: Exception if collection format is invalid.
    """
    if "collections" not in resource:
        return True

    collections = resource["collections"]
    if not isinstance(collections, list):
        raise Exception("Improper collection format in resource data")

    for col in collections:
        if col.get("collection_id") == collection:
            return True

    return False


def append_segment_ids(resource: Dict[str, Any], segment_ids: Set[str]):
    """
    Appends segment IDs from the resource's segment rules into the given set.

    :param resource: The feature or property dictionary.
    :param segment_ids: A set to accumulate segment IDs.
    """
    for segment_rule in resource.get("segment_rules", []):
        for rule in segment_rule.get("rules", []):
            for segment_id in rule.get("segments", []):
                segment_ids.add(segment_id)


def extract_resources(resource_data: Dict[str, Any], collection: str) -> Dict[str, List[Any]]:
    """
    Extracts features, properties, and segments after validation.

    :param resource_data: The environment-specific data.
    :param collection: The collection ID to validate against.
    :return: A dictionary with keys 'features', 'properties', and 'segments'.
    :raises: Exception if any required segment is missing.
    """
    features = []
    properties = []
    segments = []
    required_segment_ids = set()

    for feature in resource_data.get("features", []):
        if validate_resource(feature, collection):
            append_segment_ids(feature, required_segment_ids)
            features.append(feature)

    for property_ in resource_data.get("properties", []):
        if validate_resource(property_, collection):
            append_segment_ids(property_, required_segment_ids)
            properties.append(property_)

    available_segments = resource_data.get("segments", [])
    for segment in available_segments:
        if segment.get("segment_id") in required_segment_ids:
            segments.append(segment)
            required_segment_ids.remove(segment.get("segment_id"))

    if len(required_segment_ids) > 0:
        raise Exception(f"Required segment doesn't exist in provided segments")

    return {
        "features": features,
        "properties": properties,
        "segments": segments
    }


def extract_configurations(data: str, environment: str, collection: str) -> Dict[str, List[Any]]:
    """
    Unified parser for app-config data for new SDK/export/promote format.

    :param data: Raw JSON string of the config.
    :param environment: The environment ID.
    :param collection: The collection ID.
    :return: A dictionary with 'features', 'properties', and 'segments'.
    :raises: Exception on any validation or format error.
    """
    try:
        configurations = json.loads(data)

        if "collections" not in configurations or not isinstance(configurations["collections"], list):
            raise Exception("Improper/Missing collections in configuration")

        if not any(col.get("collection_id") == collection for col in configurations["collections"]):
            raise Exception("Required collection not found in collections")

        config_data = extract_environment_data(configurations, environment)
        return extract_resources(config_data, collection)

    except Exception as e:
        raise Exception(f"Extraction of configurations failed with error:\n {str(e)}")


def format_config(res: Dict[str, List[Any]], environment_id: str, collection_id: str) -> str:
    """
    Formats the extracted resources into unified config format.

    :param res: The extracted config (from `extract_configurations`).
    :param environment_id: The environment ID to include.
    :param collection_id: The collection ID to include.
    :return: A formatted configuration dictionary.
    """
    return json.dumps({
        "environments": [
            {
                "environment_id": environment_id,
                "features": res.get("features", []),
                "properties": res.get("properties", [])
            }
        ],
        "collections": [{"collection_id": collection_id}],
        "segments": res.get("segments", [])
    })
