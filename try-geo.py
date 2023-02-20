import requests
import json
from requests.structures import CaseInsensitiveDict

lat1 = 1.4471437206974116
lon1 = 110.45102315640258

lat2 = 1.4560609713111177
lon2 = 110.42437033120086

lat3 = 1.543127818033014 # 1.543127818033014
lon3 = 110.33950758881247 # 110.33950758881247

apiKey = "aad49482771c41c8bd927acac874e28a"


def get_address(lat,lon):
    url = "https://api.geoapify.com/v1/geocode/reverse?lat="+str(lat)+"&lon="+str(lon)+"&apiKey="+apiKey

    headers = CaseInsensitiveDict()
    headers["Accept"] = "application/json"
    resp = requests.get(url, headers=headers)
    # print(resp.status_code)
    data = json.loads(resp.text)
    # print(resp.json().items())
    try:
        print("Name:"       , data['features'][0]['properties']['name'])
        print("Country:"    , data['features'][0]['properties']['country'])
        print("Formatted:"  , data['features'][0]['properties']['formatted'])
        print("Address 1:"  , data['features'][0]['properties']['address_line1'])
        print("Address 2:"  , data['features'][0]['properties']['address_line2'])
        print("\n")
    except KeyError as e:
        print("Failed to retrieved info due to ", e)

get_address(lat1,lon1)
get_address(lat2,lon2)
get_address(lat3,lon3)