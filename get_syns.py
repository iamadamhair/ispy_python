import urllib
import json
import requests
from sql_driver import sql_driver

url = "http://maps.googleapis.com/maps/api/geocode/json?address=googleplex&sensor=false"

response = urllib.urlopen(url)
r = requests.get('http://words.bighugelabs.com/api/2/a4053f74ffb26837480643a18933bc24/basketball/json')
print r.json()['adjective']['syn']
data = json.load(response)
print data