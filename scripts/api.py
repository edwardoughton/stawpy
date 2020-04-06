"""
WiGLE API

Written by Ed Oughton.

March 2020

"""
import requests
import configparser
import os
import pandas as pd

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

bounds = (0.11103, 0.14223, 52.2014, 52.22058)

response = requests.get('https://api.wigle.net//api//v2//network//search',
    auth=('AIDf99511eff6a2976fbba7e482e9e8a193', '6f6c2f043c6c350117f12cbf79c71c54'),

    params={
        "region":"England",
        # 'country': 'GB',
        # 'latrange1': bounds[0],
        # 'latrange2': bounds[1],
        # 'longrange1': bounds[2],
        # 'longrange2': bounds[3],
    }
)

output = pd.DataFrame(response.json()['results'])
output.to_csv(os.path.join(BASE_PATH, 'wigle', 'bulk.csv'), index=False)
