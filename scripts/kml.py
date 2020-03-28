"""
Read KML file.

Written by Ed Oughton.

March 2020 (amid coronavirus lockdown)

"""
import os
import csv
import configparser
import time
import pandas as pd
import geopandas as gpd
import lxml
from pykml import parser

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']


def load_data(path):
    """

    """
    with open(path) as f:
        folder = parser.parse(f).getroot().Document.Folder

    plnm=[]
    cordi=[]
    for pm in folder.Placemark:
        plnm1 = pm.name
        plcs1 = pm.Point.coordinates
        plnm.append(plnm1.text)
        cordi.append(plcs1.text)

    db = pd.DataFrame()
    db['place_name'] = plnm
    db['cordinates'] = cordi

    db['Longitude'], db['Latitude'] = zip(*db['cordinates'].apply(lambda x: x.split(',', 2)))

    return db

if __name__ == '__main__':

    path = os.path.join(BASE_PATH, '20200328-00032.kml')
    data = load_data(path)
    data.to_csv(os.path.join(BASE_PATH, '20200328-00032.csv'))
