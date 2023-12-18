#!/bin/bash

# Run the coverage
coverage run --source=../ibm_appconfiguration/ -m unittest discover -s unit_tests

# Report on the screen
coverage report -m

# Create the html page
coverage html -d htmlpage