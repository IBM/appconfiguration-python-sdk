# Run the sample apps

To run the examples, you will need an appropriate App Configuration service instance
   
   1. Go to the IBM Cloud Dashboard page. 
   2. Either click an existing App Configuration service instance or click Create resource > Developer Tools and create a service instance.
   3. Copy the guid and apikey from the Service credentials page.
   4. Create a new Environment or use the "dev".
   5. Create a collection and copy the Id value.

 Create a file name `config.py` in the same folder, and add the above created values in it as shown below
 Example:
 ```python
# config.py

GUID = "paste-the-guid"
APIKEY = "paste-the-apikey"
COLLECTION = "collection_id"
ENVIRONMENT = "environment-id"
```