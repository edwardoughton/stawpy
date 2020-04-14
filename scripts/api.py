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
from shapely.geometry import Point, mapping
from datetime import datetime
import random

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

if __name__ == '__main__':

    locales = [
        # 'Central London',
        'City of London'
    ]

    results = os.path.join(BASE_PATH, '..', 'results')
    if not os.path.exists(results):
        os.makedirs(results)

    path = os.path.join(BASE_PATH, 'shapes', 'PostalSector.shp')
    pcd_sector_shapes = gpd.read_file(path)
    # pcd_sector_shapes.crs = 'epsg:27700'
    # pcd_sector_shapes = pcd_sector_shapes.to_crs('epsg:4326')

    for locale in locales:

        print('Working on {}'.format(locale))

        boundaries = pcd_sector_shapes.loc[pcd_sector_shapes['Locale'] == locale]
        # boundaries.crs = 'epsg:27700'
        # boundaries = boundaries.to_crs('epsg:4326')

        for idx, boundary in boundaries.iterrows():

            pcd_sector = boundary['StrSect']

            # if not pcd_sector == 'W1C1':
            #     continue

            print('Working on {}'.format(pcd_sector))

            print('Getting data')
            folder = os.path.join(BASE_PATH, 'wigle', 'postcode_sectors', str(pcd_sector))
            if not os.path.exists(folder):
                os.makedirs(folder)

            #minx, miny, maxx, maxy
            geom = boundary['geometry']
            minx, miny, maxx, maxy = geom.bounds

            # id_number = 0

            # x_axis = np.linspace(
            #     minx, maxx, num=(
            #         int(math.sqrt(geom.area) / (math.sqrt(geom.area)/10))
            #         )
            #     )
            # y_axis = np.linspace(
            #     miny, maxy, num=(
            #         int(math.sqrt(geom.area) / (math.sqrt(geom.area)/10))
            #         )
            #     )

            # sample_points = []

            # xv, yv = np.meshgrid(x_axis, y_axis, sparse=False, indexing='ij')
            # for i in range(len(x_axis)):
            #     for j in range(len(y_axis)):
            #         receiver = Point((xv[i,j], yv[i,j]))
            #         indoor_outdoor_probability = np.random.rand(1,1)[0][0]
            #         if geom.contains(receiver):
            #             sample_points.append({
            #                 'type': "Feature",
            #                 'geometry': {
            #                     "type": "Point",
            #                     "coordinates": [xv[i,j], yv[i,j]],
            #                 },
            #                 'properties': {
            #                 }
            #             })
            #             id_number += 1

            #         else:
            #             pass


            sample_points = []

            print('Generating sample points')
            for i in range(1, int(geom.area/1000) + 1):

                x = random.uniform(minx, maxx)
                y = random.uniform(miny, maxy)

                sample_points.append({
                    'type': "Feature",
                    'geometry': {
                        "type": "Point",
                        "coordinates": (x, y),
                    },
                    'properties': {
                        'id': i,
                    }
                })

            print('Number of sample points is {}'.format(len(sample_points)))

            # path = os.path.join(folder, 'boundary.shp')
            # # print(boundary['geometry'])
            # boundary_gdf = gpd.GeoDataFrame(geometry=gpd.GeoSeries(boundary))
            # # print(boundary_gdf)
            # boundary_gdf.to_file(path, crs='epsg:4326')

            # print('Getting boundary')
            # boundary = pcd_sector_shapes.loc[pcd_sector_shapes['StrSect'] == pcd_sector]

            print('Generating results')

            results = []

            for idx, point in enumerate(sample_points):

                # if idx > 1:
                #     continue

                geom = Point(point['geometry']['coordinates'])

                df = pd.DataFrame({'point': [idx]})
                gdf = gpd.GeoDataFrame(df, geometry = [geom])

                gdf['geometry'] = gdf['geometry'].buffer(50)
                gdf['geometry'] = gdf['geometry'].envelope

                area_m = gdf['geometry'].area.values[0]

                gdf.crs = 'epsg:27700'
                gdf = gdf.to_crs('epsg:4326')

                # gdf.to_file(os.path.join(folder, str(idx) + '.shp'))

                bbox = gdf['geometry'].bounds

                response = requests.get('https://api.wigle.net//api//v2//network//search',
                    auth=('AIDf99511eff6a2976fbba7e482e9e8a193', '6f6c2f043c6c350117f12cbf79c71c54'),

                    params={
                        # "region":"England",
                        # 'country': 'GB',
                        'latrange1': bbox['miny'].values[0],
                        'latrange2': bbox['maxy'].values[0],
                        'longrange1': bbox['minx'].values[0],
                        'longrange2': bbox['maxx'].values[0],
                        'startTransID': '20170000-00000',
                        'resultsPerPage': 1000,
                    }
                )

                # # {'trilat': 51.51363373, 'trilong': -0.15803051, 'ssid': None, 'qos': 0,
                # # 'transid': '20200128-00000', 'firsttime': '2020-01-28T17:00:00.000Z',
                # # 'lasttime': '2020-01-28T09:00:00.000Z', 'lastupdt': '2020-01-28T09:00:00.000Z',
                # # 'netid': '00:27:90:4D:EA:44', 'name': None, 'type': 'infra', 'comment': None,
                # # 'wep': '2', 'bcninterval': 0, 'freenet': '?', 'dhcp': '?', 'paynet': '?',
                # # 'userfound': False, 'channel': 11, 'encryption': 'wpa2', 'country': 'GB',
                # # 'region': 'England', 'city': 'London', 'housenumber': None,
                # # 'road': 'Oxford Street', 'postalcode': 'W1H 7AL'}

                for item in response.json()['results']:
                    item['coordinates'] = point['geometry']['coordinates']
                    item['area_m'] = area_m
                    results.append(item)

                print('Number of results is {}'.format(len(results)))

            output = pd.DataFrame(results)
            output = output.drop_duplicates(subset=['netid'])

            # date = str(datetime.now(tz=None))[:10]
            # time = str(datetime.now(tz=None)).split(' ')[1][:5]
            random_number = round(random.uniform(0,1e9))
            filename = str('data_{}.csv'.format(random_number))

            print('Writing {}'.format(pcd_sector))
            output.to_csv(str(os.path.join(folder, filename + '.csv')), index=False)
