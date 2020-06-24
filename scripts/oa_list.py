"""
This code reads in all data and generates a list
for postcode sectors where data have been collected.

Written by Ed Oughton

May 2020

"""
import os
import csv
import configparser
import pandas as pd
import geopandas as gpd
from pykml import parser
import numpy as np

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']


def load_collected_data(folder, files):
    """
    Load all collected data.

    """
    all_data = []

    for filename in files:

        if not filename.endswith('.kml'):
            continue

        print('Loading {}'.format(filename))
        path = os.path.join(folder, filename)

        data = load_single_file(path)

        all_data = all_data + data

    all_data = gpd.GeoDataFrame.from_features(all_data)
    all_data.crs = 'epsg:4326'
    all_data = all_data.to_crs('epsg:27700')

    return all_data


def load_single_file(path):
    """
    Load a single kml file.

    """
    with open(path) as f:
        folder = parser.parse(f).getroot().Document.Folder

    output = []

    for ap_id, pm in enumerate(folder.Placemark):
        device_type = str(pm.description).split('\n')[5]
        if device_type.split(' ')[1] == 'WIFI':
            output.append({
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    'coordinates': (
                        float(str(pm.Point.coordinates).split(',')[0]),
                        float(str(pm.Point.coordinates).split(',')[1])
                    )
                },
                'properties': {
                    'ap_id': ap_id,
                    'name': str(pm.name),
                    'network_id': str(pm.description).split('\n')[0],
                    'encryption': str(pm.description).split('\n')[1],
                    'time': str(pm.description).split('\n')[2],
                    'signal': str(pm.description).split('\n')[3],
                    'accuracy': str(pm.description).split('\n')[4],
                    'type': str(device_type),
                },
            })

    return output


def get_oa_list(collected_data, shapes):
    """
    Count data points per postcode and subset those with data.

    """
    f = lambda x:np.sum(collected_data.intersects(x))
    shapes['waps_collected'] = shapes['geometry'].apply(f)

    shapes = shapes.loc[shapes['waps_collected'] > 0]

    pcd_list = shapes['lower_id'].unique()

    return pcd_list


if __name__ == '__main__':

    folder = os.path.join(BASE_PATH, 'intermediate')
    if not os.path.exists(folder):
        os.makedirs(folder)

    folder_kml = os.path.join(BASE_PATH, 'wigle', 'all_kml_data')
    files = os.listdir(folder_kml)

    path = os.path.join(folder, 'all_collected_points.shp')
    if not os.path.exists(path):
        print('Processing collected points')
        collected_data = load_collected_data(folder_kml, files)
        collected_data.to_file(path, crs='epsg:27700')
        path = os.path.join(folder, 'all_collected_points.csv')
        collected_data.to_csv(path)
    else:
        print('Loading existing processed collected points')
        collected_data = gpd.read_file(path, crs='epsg:27700')#[:1000]

    print('Loading os area shapes')
    path = os.path.join(folder, 'output_areas.shp')
    shapes = gpd.read_file(path)#[:100]
    shapes.crs = 'epsg:27700'
    shapes = shapes.to_crs('epsg:27700')

    print('Getting oa list')
    #subset just cambridge postcodes for speed up
    #shapes = shapes.loc[shapes['StrSect'].str.startswith('CB')]
    oa_list = get_oa_list(collected_data, shapes)

    print('Writing list')
    path = os.path.join(folder, 'oa_list.csv')
    oa_list = pd.DataFrame({'lower_id':oa_list})
    oa_list.to_csv(path, index=False)
