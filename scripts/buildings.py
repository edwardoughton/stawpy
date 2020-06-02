"""
Process building information into postcode sectors.

Written by Ed Oughton

May 2020

"""
import os
import csv
import configparser
import pandas as pd
import geopandas as gpd
from shapely.geometry import mapping, Polygon
from shapely import wkt
import numpy as np

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']


def subset_areas_with_data(pcd_sectors, pcd_sector_shapes):
    """

    """
    shapes = []
    points = []

    for idx, pcd_sector_shape in pcd_sector_shapes.iterrows():
        if pcd_sector_shape['StrSect'] in pcd_sectors:
            shapes.append({
                'type': 'Feature',
                'geometry': mapping(pcd_sector_shape['geometry']),
                'properties': {
                    'StrSect': pcd_sector_shape['StrSect'],
                }
            })
            points.append({
                'type': 'Feature',
                'geometry': mapping(pcd_sector_shape['geometry'].representative_point()),
                'properties': {
                    'StrSect': pcd_sector_shape['StrSect'],
                }
            })

    shapes = gpd.GeoDataFrame.from_features(shapes)
    points = gpd.GeoDataFrame.from_features(points)

    return shapes, points


def get_lad_list(lads, pcd_points):
    """

    """
    pcd_points = gpd.overlay(pcd_points, lads, how='intersection')

    lad_list = pcd_points['name'].to_list()

    return pcd_points, lad_list


def get_postcode_sector_boundaries(lad_id, pcd_points, pcd_shapes):
    """

    """
    pcd_subset = pcd_points.loc[pcd_points['name'] == lad_id]

    pcds_in_lad_list = pcd_subset['StrSect'].to_list()

    pcd_shapes_subset = []

    for idx, pcd_shape in pcd_shapes.iterrows():
        if pcd_shape['StrSect'] in pcds_in_lad_list:
            pcd_shapes_subset.append({
                'type': 'Feature',
                'geometry': mapping(pcd_shape['geometry']),
                'properties': {
                    'StrSect': pcd_shape['StrSect'],
                }
            })

    pcd_shapes_subset = gpd.GeoDataFrame.from_features(pcd_shapes_subset)

    return pcd_shapes_subset


if __name__ == '__main__':

    print('Loading postcode list')
    path = os.path.join(BASE_PATH, 'intermediate', 'pcd_list.csv')
    pcd_sectors = pd.read_csv(path)
    pcd_sectors = pcd_sectors['StrSect'].tolist()

    print('Load and subset postcode sectors')
    path = os.path.join(BASE_PATH, 'shapes', 'PostalSector.shp')
    pcd_shapes = gpd.read_file(path)
    pcd_shapes.crs = 'epsg:27700'
    pcd_shapes = pcd_shapes.to_crs('epsg:27700')
    pcd_shapes, pcd_points = subset_areas_with_data(pcd_sectors, pcd_shapes)

    print('Load and subset lads')
    path = os.path.join(BASE_PATH, 'shapes', 'lad_uk_2016-12.shp')
    lads = gpd.read_file(path, crs='epsg:27700')
    pcd_points.crs = 'epsg:27700'
    pcd_points, lad_list = get_lad_list(lads, pcd_points)

    for lad_id in lad_list:

        print('Loading data for {}'.format(lad_id))

        path = os.path.join(BASE_PATH, 'prems_by_lad', lad_id)

        prems_by_lad = []

        for file in os.listdir(path):
            if file.endswith(".csv"):

                prems = pd.read_csv(os.path.join(path, file))

                for idx, prem in prems.iterrows():
                    geom = wkt.loads(prem['geom'])
                    prems_by_lad.append({
                        'type': 'Feature',
                        'geometry': geom.representative_point(),
                        'properties': {
                            'mistral_function_class': prem['mistral_function_class'],
                            'mistral_building_class': prem['mistral_building_class'],
                            'res_count': prem['res_count'],
                            'floor_area': prem['floor_area'],
                            'height_toroofbase': prem['height_toroofbase'],
                            'height_torooftop': prem['height_torooftop'],
                            'nonres_count': prem['nonres_count'],
                            'number_of_floors': prem['number_of_floors'],
                            'footprint_area': prem['footprint_area'],
                        }
                    })

        prems_by_lad = gpd.GeoDataFrame.from_features(prems_by_lad)

        pcd_shapes_subset = get_postcode_sector_boundaries(lad_id, pcd_points, pcd_shapes)

        lad_folder = os.path.join(BASE_PATH, 'intermediate', 'prems', lad_id)
        if not os.path.exists(lad_folder):
            os.makedirs(lad_folder)

        for pcd_shape_id in pcd_shapes_subset['StrSect'].unique():

            # if not pcd_shape_id == 'CB41':
            #     continue

            print('Working on {}'.format(pcd_shape_id))

            curent_pcd_sector = pcd_shapes_subset.loc[pcd_shapes_subset['StrSect'] == pcd_shape_id]

            prems_within_pcd = gpd.overlay(prems_by_lad, curent_pcd_sector, how='intersection')

            path = os.path.join(BASE_PATH, 'intermediate', 'prems', lad_id, pcd_shape_id + '.shp')
            prems_within_pcd.to_file(path, crs='epsg:27700')
            path = os.path.join(BASE_PATH, 'intermediate', 'prems', lad_id, pcd_shape_id + '.csv')
            prems_within_pcd.to_csv(path, index=False)
