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

import tkinter as tk
from ibm_appconfiguration import AppConfiguration, Feature, ConfigurationType
import config


class Window(tk.Tk):
    def __init__(self):
        super().__init__()

        self.__hasData = False
        self.title("App Configuration sample")
        self.label_text = tk.StringVar()
        self.label_text.set('Get your Configuration values after data is loaded')

        self.label = tk.Label(self, textvar=self.label_text)
        self.label.pack(fill=tk.BOTH, expand=1, padx=100, pady=30)

        hello_button = tk.Button(self, text="Get String Feature", command=lambda: self.fetch_feature('featurestring'))
        hello_button.pack(side=tk.LEFT, padx=(10, 20), pady=(0, 20))

        numeric_button = tk.Button(self, text="Get Numeric Feature",
                                   command=lambda: self.fetch_feature('featurenumeric'))
        numeric_button.pack(side=tk.LEFT, padx=(10, 20), pady=(0, 20))

        bool_button = tk.Button(self, text="Get Boolean Feature", command=lambda: self.fetch_feature('featurebool'))
        bool_button.pack(side=tk.LEFT, padx=(10, 20), pady=(0, 20))

        property_button = tk.Button(self, text="Property", command=lambda: self.fetch_property('numericproperty'))
        property_button.pack(side=tk.RIGHT, padx=(10, 20), pady=(0, 20))

        self.initialize_app()

    def fetch_property(self, property_id: str):
        if self.__hasData:
            self.label.configure(background="red")
            app_config = AppConfiguration.get_instance()
            property_obj = app_config.get_property(property_id)

            try:
                if property_obj:

                    entity_attributes = {
                        'city': 'Bangalore',
                        'country': 'India'
                    }
                    if property_obj.get_property_data_type() == ConfigurationType.NUMERIC:
                        val = property_obj.get_current_value("pvQr45", entity_attributes)
                        self.label_text.set(F"Your configurations property value is {val}")
                        self.configure(background="yellow")
                else:
                    print("No configurations")
            except Exception as err:
                print(err)
        else:
            self.label_text.set("Not loaded")
            self.label.configure(background="grey")

    def fetch_feature(self, feature_id: str):
        if self.__hasData:
            self.label.configure(background="red")
            app_config = AppConfiguration.get_instance()
            feature = app_config.get_feature(feature_id)
            try:
                if feature:

                    entity_attributes = {
                        'city': 'Bangalore',
                        'country': 'India'
                    }
                    if feature.get_feature_data_type() == ConfigurationType.STRING:
                        val = feature.get_current_value("pvQr45", entity_attributes)
                        self.label_text.set(F"Your configurations value is {val}")
                        self.configure(background="yellow")
                    elif feature.get_feature_data_type() == ConfigurationType.BOOLEAN:
                        val = feature.get_current_value("pvQr45", entity_attributes)
                        self.label_text.set(F"Your configurations value is {val}")
                        self.configure(background="green")
                    elif feature.get_feature_data_type() == ConfigurationType.NUMERIC:
                        val = feature.get_current_value("pvQr45", entity_attributes)
                        self.label_text.set(F"Your configurations value is {val}")
                        self.configure(background="black")
                else:
                    print("No configurations")
            except Exception as err:
                print(err)

        else:
            self.label_text.set("Not loaded")
            self.label.configure(background="red")

    def response(self):
        self.__hasData = True
        self.label_text.set('Get your Feature value NOW')

    def initialize_app(self):
        appconfig_client = AppConfiguration.get_instance()
        AppConfiguration.enable_debug(True)
        appconfig_client.init(region=AppConfiguration.REGION_US_SOUTH,
                              guid=config.GUID,
                              apikey=config.APIKEY)
        appconfig_client.set_context(collection_id=config.COLLECTION, environment_id=config.ENVIRONMENT)
        appconfig_client.register_configuration_update_listener(self.response)
        self.response()


if __name__ == "__main__":
    window = Window()
    window.mainloop()
