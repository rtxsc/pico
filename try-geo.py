import requests
import json
from requests.structures import CaseInsensitiveDict
from requests.exceptions import HTTPError


lat1 = 1.4471437206974116
lon1 = 110.45102315640258

lat2 = 1.4560609713111177
lon2 = 110.42437033120086

lat3 = 1.543127818033014 # 1.543127818033014
lon3 = 110.33950758881247 # 110.33950758881247

apiKey = "aad49482771c41c8bd927acac874e28a"


locationiq_key = "pk.b82fc9de1d0f74c8d99cca7292290fe2"

def request_demo():
    try:
        response = requests.get('https://httpbin.org/get')
        response.raise_for_status()
        # access JSOn content
        jsonResponse = response.json()
        # print("Entire JSON response")
        # print(jsonResponse)
        print(jsonResponse["origin"])
        print(jsonResponse["headers"]["Host"])
        print(jsonResponse["headers"]["User-Agent"])

        data = json.loads(response.text)
        print("Origin Public IP: " , data["origin"])
        
    except HTTPError as http_err:
        print(f'HTTP error occurred: {http_err}')
    except Exception as err:
        print(f'Other error occurred: {err}')


def try_geocode():
    # api-endpoint
    URL = "http://maps.googleapis.com/maps/api/geocode/json"
    
    # location given here
    location = "UiTM Samarahan"
    
    # defining a params dict for the parameters to be sent to the API
    PARAMS = {'address':location}
    
    # sending get request and saving the response as response object
    r = requests.get(url = URL, params = PARAMS)
    
    # extracting data in json format
    data = r.json()
    print(data)
    
    # extracting latitude, longitude and formatted address 
    # of the first matching location
    # latitude = data['results'][0]['geometry']['location']['lat']
    # longitude = data['results'][0]['geometry']['location']['lng']
    # formatted_address = data['results'][0]['formatted_address']
    
    # # printing the output
    # print("Latitude:%s\nLongitude:%s\nFormatted Address:%s"
    #     %(latitude, longitude,formatted_address))



def get_address(lat,lon):
    url = "https://api.geoapify.com/v1/geocode/reverse?lat="+str(lat)+"&lon="+str(lon)+"&apiKey="+apiKey
    url_iq = "https://us1.locationiq.com/v1/reverse?key="+locationiq_key+"&lat="+str(lat)+"&lon="+str(lon)+"&format=json"

    headers = CaseInsensitiveDict()
    # headers["Accept"] = "application/json"
    headers = {'Accept': 'application/json'}
    # resp = requests.get(url, headers=headers)
    resp = requests.get(url) # minimal request
    resp_iq = requests.get(url_iq) # minimal request


    print(resp.status_code) # returns 200 HTTP OK
    data = json.loads(resp.text)
    data_iq = json.loads(resp_iq.text)
    # print(resp.json().items()) # spit out json dict
    # print(resp_iq.json().items()) # spit out json dict
    # jsonResponse = resp.json() # spit out json dict
    # print(jsonResponse) 
    # print(type(data))  # returns <class 'dict'>
    try:
        print("Name:"       , data_iq["display_name"])
        print("Road:"       , data_iq["address"]["road"])
        print("Address:"       , data_iq["address"]["hospital"])
        print("Postcode:"      , data_iq["address"]["postcode"])


        print("Name:"       , data["features"][0]["properties"]["name"])
        print("Country:"    , data["features"][0]["properties"]["country"])
        print("Formatted:"  , data["features"][0]["properties"]["formatted"])
        
        print("Address 1:"  , data["features"][0]["properties"]["address_line1"])
        print("Address 2:"  , data["features"][0]["properties"]["address_line2"])
        print("\n")
    except KeyError as e:
        print("Failed to retrieved info due to ", e)

# get_address(lat1,lon1)
# get_address(lat2,lon2)
get_address(lat3,lon3)
# try_geocode()
# request_demo()
