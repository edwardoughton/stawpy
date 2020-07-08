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


def process_rail_stations(path_output):
    """
    Find MSOA areas with rail stations.

    """
    path = os.path.join(BASE_PATH, 'rail_stations', 'rail_stations_27700.shp')
    rail_stations = gpd.read_file(path, crs='epsg:27700')#[:100]

    path = os.path.join(BASE_PATH, 'shapes', 'lad_uk_2016-12.shp')
    lads = gpd.read_file(path, crs='epsg:27700')

    rail_stations = gpd.overlay(rail_stations, lads, how='intersection')
    rail_stations = rail_stations[['geometry', 'StationNam', 'name', 'desc']]

    path = os.path.join(BASE_PATH, 'intermediate', 'output_areas.shp')
    output_areas = gpd.read_file(path, crs='epsg:27700')#[:2000]
    output_areas = output_areas[['geometry', 'msoa', 'region']]
    rail_stations = gpd.overlay(rail_stations, output_areas, how='intersection')

    rail_stations.to_file(path_output)

    return rail_stations


def get_msoas(rail_stations, lad):
    """
    Get output area list for a specific lad.

    """
    msoas_to_target = []

    for idx, station in rail_stations.iterrows():
        if station['name'] == lad:
            msoas_to_target.append(station['msoa'])

    return msoas_to_target


def grid_area(boundary, length, width):
    """

    """
    xmin, ymin, xmax, ymax = boundary['geometry'].total_bounds

    cols = list(range(int(np.floor(xmin)), int(np.ceil(xmax)), width))
    rows = list(range(int(np.floor(ymin)), int(np.ceil(ymax)), length))
    rows.reverse()

    polygons = []
    for x in cols:
        for y in rows:
            polygons.append(Polygon([(x, y), (x+width, y), (x+width, y-length), (x, y-length)]))

    grid_squares = gpd.GeoDataFrame({'geometry': polygons}, crs='epsg:27700')

    return grid_squares


def make_api_request(bbox):
    """
    Make the API request and return results.

    """
    #make API request
    response = requests.get(
        'https://api.wigle.net//api//v2//network//search',
        auth=(
            'AIDf99511eff6a2976fbba7e482e9e8a193',
            '6f6c2f043c6c350117f12cbf79c71c54'),
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

    # # example fields:
    # # # {'trilat': 51.51363373, 'trilong': -0.15803051, 'ssid': None, 'qos': 0,
    # # # 'transid': '20200128-00000', 'firsttime': '2020-01-28T17:00:00.000Z',
    # # # 'lasttime': '2020-01-28T09:00:00.000Z', 'lastupdt': '2020-01-28T09:00:00.000Z',
    # # # 'netid': '00:27:90:4D:EA:44', 'name': None, 'type': 'infra', 'comment': None,
    # # # 'wep': '2', 'bcninterval': 0, 'freenet': '?', 'dhcp': '?', 'paynet': '?',
    # # # 'userfound': False, 'channel': 11, 'encryption': 'wpa2', 'country': 'GB',
    # # # 'region': 'England', 'city': 'London', 'housenumber': None,
    # # # 'road': 'Oxford Street', 'postalcode': 'W1H 7AL'}

    results = []

    for item in response.json()['results']:
        results.append(item)

    return results


if __name__ == '__main__':

    #set grid length and width
    length = 50
    width = 50

    #set folder export location
    folder = os.path.join(BASE_PATH, 'intermediate')

    #load in output area shapes
    print('Loading oa area shapes')
    path = os.path.join(folder, 'output_areas.shp')
    shapes = gpd.read_file(path)#[:100]
    shapes.crs = 'epsg:27700'
    shapes = shapes.to_crs('epsg:27700')

    #load in rail station locations
    path_output = os.path.join(BASE_PATH, 'intermediate', 'rail_stations.shp')
    if not os.path.exists(path_output):
        rail_stations = process_rail_stations(path_output)
    else:
        rail_stations = gpd.read_file(path_output, crs='epsg:27700')

    #These are mainly all central London LADS, followed nu some other cities
    lads_of_interest = [
        'E09000001',
        'E09000033',
        'E09000013',
        'E09000007',
        'E09000012',
        'E09000022',
        'E09000023',
        'E09000020',
        'E09000019',
        'E09000030',
        'E09000028',
        'E09000032',
        'E08000025', #Birmingham
        'E08000003', #Manchester
        'E08000035', #Leeds
        'S12000046', #Glasgow
        'S12000036', #Edinburgh
        'W06000015', #Cardiff
    ]

    for lad in lads_of_interest:

        msoas = get_msoas(rail_stations, lad)

        folder = os.path.join(BASE_PATH, 'api_results')
        if not os.path.exists(folder):
            os.makedirs(folder)

        for msoa in msoas:#[:1]:

            print('Working on {}'.format(msoa))

            #subset msoa shape
            msoa_shape = shapes.loc[shapes['msoa'] == msoa]#[:1]

            path = os.path.join(folder, msoa)
            if not os.path.exists(path):
                os.makedirs(path)

            #Create a grid across the output area
            grid_squares = grid_area(msoa_shape, length, width)
            grid_squares = gpd.overlay(grid_squares, msoa_shape, how='intersection')

            #Drop grid squares that are below the desired area (area = length * width)
            grid_squares['area_km2'] = grid_squares['geometry'].area / 1e6
            mask = grid_squares['area_km2'] >= ((length * width) / 1e6)
            grid_squares = grid_squares.loc[mask]
            filename = 'grid_squares_{}_{}.shp'.format(length, width)
            grid_squares.to_file(os.path.join(path, filename))

            if not len(grid_squares) > 0:
                continue

            #wigle api requires WGS84 coordinate reference system
            grid_squares.crs = 'epsg:27700'
            grid_squares = grid_squares.to_crs('epsg:4326')

            # I set this up for testing to limit the number of squares
            # grid_squares = grid_squares[:4]

            for idx, grid_square in grid_squares.iterrows():

                #get bounds
                xmin, ymin, xmax, ymax = grid_square['geometry'].bounds

                #specify data export filename and path
                filename = '{}_{}_{}_{}.csv'.format(xmin, ymin, xmax, ymax)
                path = os.path.join(folder, msoa, filename)

                if os.path.exists(path):
                    continue

                #set bounding box
                bbox = grid_square['geometry'].bounds

                #get results
                results = make_api_request(bbox)

                if len(results) < 100:

                    print('Number of results is {}, so <100'.format(len(results)))

                    #export reseults to file
                    output = pd.DataFrame(results)
                    output.to_csv(path, index=False)

                else:
                    print('Number of results is == 100')

                    #if the maximum number of returned results is reached for
                    #the existing bounding box, then chop up into smaller bboxes
                    length_small = int(length / 5)
                    width_small = int(width / 5)

                    #Create a grid across the output area
                    grid_single = gpd.GeoDataFrame({'geometry': grid_square['geometry']}, crs='epsg:4326', index=[0])
                    grid_single = grid_single.to_crs('epsg:27700')
                    smaller_grid_squares = grid_area(grid_single, length_small , width_small)

                    # filename = 'smaller_grid_squares_{}_{}.shp'.format(length_small, width_small)
                    # path = os.path.join(folder, msoa, filename)
                    # smaller_grid_squares.to_file(path, crs='epsg:27700')

                    smaller_grid_squares = smaller_grid_squares.to_crs('epsg:4326')
                    # print(path)
                    if not len(smaller_grid_squares) > 0:
                        continue

                    # smaller_grid_squares = smaller_grid_squares['geometry'].unique()
                    print('Now iterating through smaller grid squares')
                    for idx, smaller_grid_square in smaller_grid_squares.iterrows():

                        #get bounds
                        xmin, ymin, xmax, ymax = smaller_grid_square['geometry'].bounds

                        #specify data export filename and path
                        filename = '{}_{}_{}_{}.csv'.format(xmin, ymin, xmax, ymax)
                        path = os.path.join(folder, msoa, filename)

                        if os.path.exists(path):
                            continue

                        print('Working on {}'.format(filename))

                        #set bounding box
                        bbox = smaller_grid_square['geometry'].bounds

                        results = make_api_request(bbox)

                        #export reseults to file
                        output = pd.DataFrame(results)
                        output.to_csv(path, index=False)
