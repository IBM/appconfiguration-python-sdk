# IBM Cloud App Configuration Python server SDK

IBM Cloud App Configuration SDK is used to perform feature flag and property evaluation based on the configuration on IBM Cloud App Configuration service.

## Table of Contents

  - [Overview](#overview)
  - [Installation](#installation)
  - [Import the SDK](#import-the-sdk)
  - [Initialize SDK](#initialize-sdk)
  - [License](#license)

## Overview

IBM Cloud App Configuration is a centralized feature management and configuration service on [IBM Cloud](https://www.cloud.ibm.com) for use with web and mobile applications, microservices, and distributed environments.

Instrument your applications with App Configuration Python SDK, and use the App Configuration dashboard, CLI or API to define feature flags or properties, organized into collections and targeted to segments. Toggle feature flag states in the cloud to activate or deactivate features in your application or environment, when required. You can also manage the properties for distributed applications centrally.

## Installation

To install, use `pip` or `easy_install`:

```sh
pip install --upgrade ibm-appconfiguration-python-sdk
```

or

```sh
 easy_install --upgrade ibm-appconfiguration-python-sdk
```

## Import the SDK

```py
from ibm_appconfiguration import AppConfiguration, Feature, Property, ConfigurationType
```

## Initialize SDK

```py
appconfig_client = AppConfiguration.get_instance()
appconfig_client.init(region='region', guid='guid', apikey='apikey')
appconfig_client.set_context(collection_id='airlines-webapp', environment_id='dev')
```

:red_circle: **Important** :red_circle:

The **`init()`** and **`set_context()`** are the initialisation methods and should be invoked **only once** using
appconfig_client. The appconfig_client, once initialised, can be obtained across modules
using **`AppConfiguration.get_instance()`**.  [See this example below](#fetching-the-appconfig_client-across-other-modules).

- region : Region name where the App Configuration service instance is created. Use
  - `AppConfiguration.REGION_US_SOUTH` for Dallas
  - `AppConfiguration.REGION_EU_GB` for London
  - `AppConfiguration.REGION_AU_SYD` for Sydney
  - `AppConfiguration.REGION_US_EAST` for Washington DC
  - `AppConfiguration.REGION_EU_DE` for Frankfurt
- guid : GUID of the App Configuration service. Obtain it from the service credentials section of the dashboard
- apikey : ApiKey of the App Configuration service. Obtain it from the service credentials section of the dashboard
- collection_id : Id of the collection created in App Configuration service instance under the **Collections** section.
- environment_id : Id of the environment created in App Configuration service instance under the **Environments**
  section.

### Connect using private network connection (optional)

Set the SDK to connect to App Configuration service by using a private endpoint that is accessible only through the IBM
Cloud private network.

```py
appconfig_client.use_private_endpoint(True);
```

This must be done before calling the `init` function on the SDK.

### (Optional)

In order for your application and SDK to continue its operations even during the unlikely scenario of App Configuration
service across your application restarts, you can configure the SDK to work using a persistent cache. The SDK uses the
persistent cache to store the App Configuration data that will be available across your application restarts.

```python
# 1. default (without persistent cache)
appconfig_client.set_context(collection_id='airlines-webapp', environment_id='dev')

# 2. optional (with persistent cache)
appconfig_client.set_context(collection_id='airlines-webapp', environment_id='dev', options={
  'persistent_cache_dir': '/var/lib/docker/volumes/'
})
```

* persistent_cache_dir: Absolute path to a directory which has read & write permission for the user. The SDK will create
  a file - `appconfiguration.json` in the specified directory, and it will be used as the persistent cache to store the
  App Configuration service information.

When persistent cache is enabled, the SDK will keep the last known good configuration at the persistent cache. In the
case of App Configuration server being unreachable, the latest configurations at the persistent cache is loaded to the
application to continue working.

Please ensure that the cache file created in the given directory is not lost or deleted in any case. For example,
consider the case when a kubernetes pod is restarted and the cache file (appconfiguration.json) was stored in ephemeral
volume of the pod. As pod gets restarted, kubernetes destroys the ephermal volume in the pod, as a result the cache file
gets deleted. So, make sure that the cache file created by the SDK is always stored in persistent volume by providing
the correct absolute path of the persistent directory.

### (Optional)

The SDK is also designed to serve configurations, perform feature flag & property evaluations without being connected to
App Configuration service.

```python
appconfig_client.set_context(collection_id='airlines-webapp', environment_id='dev', options={
  'bootstrap_file': 'saflights/flights.json',
  'live_config_update_enabled': False
})
```

* bootstrap_file: Absolute path of the JSON file which contains configuration details. Make sure to provide a proper
  JSON file. You can generate this file using `ibmcloud ac config` command of the IBM Cloud App Configuration CLI.
* live_config_update_enabled: Live configuration update from the server. Set this value to `False` if the new
  configuration values shouldn't be fetched from the server. By default, this parameter (`live_config_update_enabled`)
  is set to True.

## Get single feature

```py
feature = appconfig_client.get_feature('online-check-in')  # feature can be None incase of an invalid feature id

if feature is not None:
    print(f'Feature Name : {0}'.format(feature.get_feature_name()))
    print(f'Feature Id : {0}'.format(feature.get_feature_id()))
    print(f'Feature Data Type : {0}'.format(feature.get_feature_data_type()))
    if feature.is_enabled():
        # feature flag is enabled
    else:
        # feature flag is disabled

```

## Get all features

```py
features_dictionary = appconfig_client.get_features()
```

## Evaluate a feature

Use the `feature.get_current_value(entity_id=entity_id, entity_attributes=entity_attributes)` method to evaluate the
value of the feature flag. This method returns one of the Enabled/Disabled/Overridden value based on the evaluation. The
data type of returned value matches that of feature flag.

```py
entity_id = "john_doe"
entity_attributes = {
    'city': 'Bangalore',
    'country': 'India'
}
feature_value = feature.get_current_value(entity_id=entity_id, entity_attributes=entity_attributes)
```

- entity_id: Id of the Entity. This will be a string identifier related to the Entity against which the feature is
  evaluated. For example, an entity might be an instance of an app that runs on a mobile device, a microservice that
  runs on the cloud, or a component of infrastructure that runs that microservice. For any entity to interact with App
  Configuration, it must provide a unique entity ID.
- entity_attributes: A dictionary consisting of the attribute name and their values that defines the specified entity.
  This is an optional parameter if the feature flag is not configured with any targeting definition. If the targeting is
  configured, then entity_attributes should be provided for the rule evaluation. An attribute is a parameter that is
  used to define a segment. The SDK uses the attribute values to determine if the specified entity satisfies the
  targeting rules, and returns the appropriate feature flag value.

## Get single Property

```py
property = appconfig_client.get_property('check-in-charges')  # property can be None incase of an invalid property id
if property is not None:
    print(f'Property Name : {0}'.format(property.get_property_name()))
    print(f'Property Id : {0}'.format(property.get_property_id()))
    print(f'Property Data Type : {0}'.format(property.get_property_data_type()))
```

## Get all Properties

```py
properties_dictionary = appconfig_client.get_properties()
```

## Evaluate a property

Use the `property.get_current_value(entity_id=entity_id, entity_attributes=entity_attributes)` method to evaluate the
value of the property. This method returns the default property value or its overridden value based on the evaluation.
The data type of returned value matches that of property.

```py
entity_id = "john_doe"
entity_attributes = {
    'city': 'Bangalore',
    'country': 'India'
}
property_value = property.get_current_value(entity_id=entity_id, entity_attributes=entity_attributes)
```

- entity_id: Id of the Entity. This will be a string identifier related to the Entity against which the property is
  evaluated. For example, an entity might be an instance of an app that runs on a mobile device, a microservice that
  runs on the cloud, or a component of infrastructure that runs that microservice. For any entity to interact with App
  Configuration, it must provide a unique entity ID.
- entity_attributes: A dictionary consisting of the attribute name and their values that defines the specified entity.
  This is an optional parameter if the property is not configured with any targeting definition. If the targeting is
  configured, then entity_attributes should be provided for the rule evaluation. An attribute is a parameter that is
  used to define a segment. The SDK uses the attribute values to determine if the specified entity satisfies the
  targeting rules, and returns the appropriate property value.

## Fetching the appconfig_client across other modules

Once the SDK is initialized, the appconfig_client can be obtained across other modules as shown below:

```python
# **other modules**

from ibm_appconfiguration import AppConfiguration

appconfig_client = AppConfiguration.get_instance()
feature = appconfig_client.get_feature('online-check-in')
enabled = feature.is_enabled()
feature_value = feature.get_current_value(entity_id, entity_attributes)
```

## Supported Data types

App Configuration service allows to configure the feature flag and properties in the following data types : Boolean,
Numeric, String. The String data type can be of the format of a TEXT string , JSON or YAML. The SDK processes each
format accordingly as shown in the below table.
<details><summary>View Table</summary>

| **Feature or Property value**                                                                                      | **DataType** | **DataFormat** | **Type of data returned <br> by `GetCurrentValue()`** | **Example output**                                                   |
| ------------------------------------------------------------------------------------------------------------------ | ------------ | -------------- | ----------------------------------------------------- | -------------------------------------------------------------------- |
| `true`                                                                                                             | BOOLEAN      | not applicable | `bool`                                                | `true`                                                               |
| `25`                                                                                                               | NUMERIC      | not applicable | `int`                                             | `25`                                                                 |
| "a string text"                                                                                                    | STRING       | TEXT           | `string`                                              | `a string text`                                                      |
| <pre>{<br>  "firefox": {<br>    "name": "Firefox",<br>    "pref_url": "about:config"<br>  }<br>}</pre> | STRING       | JSON           | `Dictionary or List of Dictionary`                              | `{'firefox': {'name': 'Firefox', 'pref_url': 'about:config'}}` |
| <pre>men:<br>  - John Smith<br>  - Bill Jones<br>women:<br>  - Mary Smith<br>  - Susan Williams</pre>  | STRING       | YAML           | `Dictionary`                              | `{'men': ['John Smith', 'Bill Jones'], 'women': ['Mary Smith', 'Susan Williams']}` |
</details>

<details><summary>Feature flag</summary>

  ```py
  feature = appconfig_client.get_feature('json-feature')
  feature.get_feature_data_type() // STRING
  feature.get_feature_data_format() // JSON
  feature.get_current_value(entityId, entityAttributes) // returns single dictionary object or list of dictionary object

  // Example Below
  // input json :- [{"role": "developer", "description": "do coding"},{"role": "tester", "description": "do testing"}]
  // expected output :- "do coding"

  tar_val = feature.get_current_value(entityId, entityAttributes)
  expected_output = tar_val[0]['description']

  // input json :- {"role": "tester", "description": "do testing"}
  // expected output :- "tester"

  tar_val = feature.get_current_value(entityId, entityAttributes)
  expected_output = tar_val['role']

  feature = appconfig_client.getFeature('yaml-feature')
  feature.get_feature_data_type() // STRING
  feature.get_feature_data_format() // YAML
  feature.get_current_value(entityId, entityAttributes) // returns dictionary object

  // Example Below
  // input yaml string :- "---\nrole: tester\ndescription: do_testing"
  // expected output :- "do_testing"

  tar_val = feature.get_current_value(entityId, entityAttributes)
  expected_output = tar_val['description']
  ```
</details>
<details><summary>Property</summary>

  ```py
  property = appconfig_client.get_property('json-property')
  property.get_property_data_type() // STRING
  property.get_property_data_format() // JSON
  property.get_current_value(entityId, entityAttributes) // returns single dictionary object or list of dictionary object

  // Example Below
  // input json :- [{"role": "developer", "description": "do coding"},{"role": "tester", "description": "do testing"}]
  // expected output :- "do coding"

  tar_val = property.get_current_value(entityId, entityAttributes)
  expected_output = tar_val[0]['description']

  // input json :- {"role": "tester", "description": "do testing"}
  // expected output :- "tester"

  tar_val = property.get_current_value(entityId, entityAttributes)
  expected_output = tar_val['role']

  property = appconfig_client.get_property('yaml-property')
  property.get_property_data_type() // STRING
  property.get_property_data_format() // YAML
  property.get_current_value(entityId, entityAttributes) // returns dictionary object 

  // Example Below
  // input yaml string :- "---\nrole: tester\ndescription: do_testing"
  // expected output :- "do_testing"

  tar_val = property.get_current_value(entityId, entityAttributes)
  expected_output = tar_val['description']
  ```
</details>

## Set listener for the feature and property data changes

The SDK provides mechanism to notify you in real-time when feature flag's or property's configuration changes. You can
subscribe to configuration changes using the same appconfig_client.

```py
def configuration_update(self):
    print('Received updates on configurations')
    # **add your code**
    # To find the effect of any configuration changes, you can call the feature or property related methods

    # feature = appconfig_client.getFeature('online-check-in')
    # new_value = feature.get_current_value(entity_id, entity_attributes)

appconfig_client.register_configuration_update_listener(configuration_update)
```

## Fetch latest data

Fetch the latest configuration data. 

```py
appconfig_client.fetch_configurations()
```

## Enable debugger (Optional)

Use this method to enable/disable the logging in SDK.

```py
appconfig_client.enable_debug(True)
```

## Examples

The [examples](https://github.com/IBM/appconfiguration-python-sdk/tree/master/examples) folder has the examples.

## License

This project is released under the Apache 2.0 license. The license's full text can be found
in [LICENSE](https://github.com/IBM/appconfiguration-python-sdk/blob/master/LICENSE)