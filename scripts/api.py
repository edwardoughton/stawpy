"""
WiGLE API

Written by Ed Oughton.

March 2020

"""
import requests

from uuid import getnode
import re

import requests

# 2. quantitative: our API can help you do this simply and quickly
# (https://api.wigle.net/swagger#/Network_search_and_information_tools/search_2)
#     - lay out your "grid" size and translate it to a list of coordinates (preferably using
#           haversine to compensate for your latitude's effect on the longitude::distance ratio)
#     - iterate through the API querying single-result "boxes" for each cell in your grid -
#           use the parameters for latitude, longitude bounds, "lastupdt" to exclude old data, and set
#           your "resultsPerPage" to one (limiting number of network records returned)
#     - check the totalResults field in the returned object to get the number of networks
#           matching your criteria per-cell.

bounds = (0.11103, 0.14223, 52.2014, 52.22058)

response = requests.get('https://api.wigle.net//api//v2//network//search',
    auth=('AIDf99511eff6a2976fbba7e482e9e8a193', '6f6c2f043c6c350117f12cbf79c71c54'),

# {"trilat":57.19687271,"trilong":-2.18424797,"ssid":null,"qos":0,"transid":"20140313-00000",
# "firsttime":"2014-03-13T06:00:00.000Z","lasttime":"2014-03-13T14:00:00.000Z",
# "lastupdt":"2014-03-13T12:00:00.000Z","netid":"00:00:00:4C:D7:13","name":null,"type":"????",
# "comment":null,"wep":"?","bcninterval":0,"freenet":"?","dhcp":"?","paynet":"?",
# "userfound":false,"channel":0,"encryption":"unknown","country":"GB","region":"Scotland",
# "city":null,"housenumber":null,"road":"A947","postalcode":"AB21 7AZ"}],"searchAfter":"5035795",
# "search_after":5035795}

    params={
        "region":"England",
        "city": 'Leeds',
        # 'country': 'GB',
        # 'latrange1': bounds[0],
        # 'latrange2': bounds[1],
        # 'longrange1': bounds[2],
        # 'longrange2': bounds[3],
    }
)

# # 2013 is the closest year the NOAA maintains
# for year in [2013]:
#     year = str(year)
#     url = 'https://ngdc.noaa.gov/eog/data/web_data/v4composites/F18' + year + '.v4.tar'
#     target = os.path.join(NIGHTLIGHTS_DIR, year)
#     os.makedirs(target, exist_ok=True)
#     target += '/nightlights_data'
#     response = requests.get(url, stream=True)
#     if response.status_code == 200:
#         with open(target, 'wb') as f:
#             f.write(response.raw.read())
#             print(f'Saved to {target}')

print(response.text)
