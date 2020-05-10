"""
WiGLE API

Written by Ed Oughton.

March 2020

"""
import requests
import configparser
import os
import pandas as pd
import geopandas as gpd
import math
import numpy as np
from shapely.geometry import Point, mapping, Polygon
from datetime import datetime
import random

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']
RESULTS = os.path.join(BASE_PATH, '..', 'results')

if __name__ == '__main__':

    locales = [
        # 'Central London',
        'City of London'
    ]

    pcd_sectors = [
        # 'W1G6',
        'W1H2',
        # 'N1C4', #King's Cross Station
        # 'NW12', #Euston Station
        # 'SE18', #Waterloo Station
        # 'W1C1', #Oxford Street
        # 'W1C2', #Oxford Street
        # 'W1K5', #Bond Street
        # 'E144', #Canary Wharf
        # 'E145', #Canary Wharf
    ]

    # results = os.path.join(BASE_PATH, '..', 'results')
    # if not os.path.exists(results):
    #     os.makedirs(results)

    for pcd_sector in pcd_sectors:

        print('Working on {}'.format(pcd_sector))

        path = os.path.join(RESULTS, pcd_sector, 'postcode_aps.shp')

        if not os.path.exists(path):
            continue

        grid_squares = gpd.read_file(path)

        grid_squares = grid_squares.loc[
            grid_squares['waps_km2'] > 0]#[:1]

        if not len(grid_squares) > 0:
            continue

        for idx, grid_square in grid_squares.iterrows():

            print('Working on grid square {}'.format(grid_square['geometry'].bounds))

            folder = os.path.join(BASE_PATH, 'wigle', 'postcode_sectors', str(pcd_sector))
            if not os.path.exists(folder):
                os.makedirs(folder)

            #minx, miny, maxx, maxy
            xmin, ymin, xmax, ymax = grid_square['geometry'].bounds

            length = 25
            wide = 25

            cols = list(range(int(np.floor(xmin)), int(np.ceil(xmax)), wide))
            rows = list(range(int(np.floor(ymin - length)), int(np.ceil(ymax - length)), length))

            rows.reverse()

            polygons = []
            for x in cols:
                for y in rows:
                    polygons.append(Polygon([(x, y), (x+wide, y), (x+wide, y-length), (x, y-length)]))

            grid = gpd.GeoDataFrame({'geometry': polygons})
            grid.crs = 'epsg:27700'
            grid = grid.to_crs('epsg:4326')
            path = os.path.join(folder, '{}_{}_{}_{}.shp'.format(xmin, ymin, xmax, ymax))
            grid.to_file(path, crs='epsg:4326')

            for idx, geom in grid.iterrows():

                results = []

                bbox = geom['geometry'].bounds
                xmin, ymin, xmax, ymax = geom['geometry'].bounds
                # print(xmin, ymin, xmax, ymax)
                response = requests.get('https://api.wigle.net//api//v2//network//search',
                    auth=('AIDf99511eff6a2976fbba7e482e9e8a193', '6f6c2f043c6c350117f12cbf79c71c54'),

                    params={
                        # "region":"England",
                        # 'country': 'GB',
                        'latrange1': ymin, #bbox['miny'].values[0],
                        'latrange2': ymax, #bbox['maxy'].values[0],
                        'longrange1': xmin, #bbox['minx'].values[0],
                        'longrange2': xmax, #bbox['maxx'].values[0],
                        'startTransID': '20170000-00000',
                        'resultsPerPage': 1000,
                    }
                )
                # fields:
                # # {'trilat': 51.51363373, 'trilong': -0.15803051, 'ssid': None, 'qos': 0,
                # # 'transid': '20200128-00000', 'firsttime': '2020-01-28T17:00:00.000Z',
                # # 'lasttime': '2020-01-28T09:00:00.000Z', 'lastupdt': '2020-01-28T09:00:00.000Z',
                # # 'netid': '00:27:90:4D:EA:44', 'name': None, 'type': 'infra', 'comment': None,
                # # 'wep': '2', 'bcninterval': 0, 'freenet': '?', 'dhcp': '?', 'paynet': '?',
                # # 'userfound': False, 'channel': 11, 'encryption': 'wpa2', 'country': 'GB',
                # # 'region': 'England', 'city': 'London', 'housenumber': None,
                # # 'road': 'Oxford Street', 'postalcode': 'W1H 7AL'}

                for item in response.json()['results']:
                    # item['coordinates'] = geom['geometry']['coordinates']
                    # item['area_m'] = geom['geometry'].area
                    results.append(item)

                print('Number of results is {}'.format(len(results)))

                output = pd.DataFrame(results)
                filename = '{}_{}_{}_{}.csv'.format(xmin, ymin, xmax, ymax)

                print('Writing {}'.format(pcd_sector))
                output.to_csv(os.path.join(folder, filename), index=False)
