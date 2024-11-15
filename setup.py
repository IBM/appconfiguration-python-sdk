# (C) Copyright IBM Corp. 2021.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with
# the License. You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on
# an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the
# specific language governing permissions and limitations under the License.

from setuptools import setup, find_packages

NAME = "ibm-appconfiguration-python-sdk"
VERSION = "0.3.6"
# To install the library, run the following
#
# python setup.py install
#
# prerequisite: setuptools
# http://pypi.python.org/pypi/setuptools

REQUIRES = [
    "python-dateutil>=2.8,<3.0.0",
    "requests>=2.32.2,<3.0",
    "websocket-client>=1.8.0,<2.0.0",
    "ibm-cloud-sdk-core>=3.20.3,<4.0.0",
    "pyyaml>=5.4.1",
    "schema>=0.7.5",
    "mmh3==5.0.1"
]
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name=NAME,
    version=VERSION,
    author="IBM",
    license='Apache 2.0',
    author_email="mdevsrvs@in.ibm.com",
    description="IBM Cloud App Configuration Python SDK",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/IBM/appconfiguration-python-sdk",
    packages=find_packages(),
    install_requires=REQUIRES,
    include_package_data=True,
    keywords=['python', 'ibm_appconfiguration', 'ibm', 'ibm cloud', 'feature_flags'],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: Apache Software License",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3"
    ],
    python_requires='>=3.0'
)
