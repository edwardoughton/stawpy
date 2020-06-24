"""
Process premises information into output areas.

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


def subset_areas_with_data(oa_areas, oa_area_shapes):
    """

    """
    shapes = []
    points = []

    for idx, oa_area_shape in oa_area_shapes.iterrows():
        if oa_area_shape['lower_id'] in oa_areas:
            shapes.append({
                'type': 'Feature',
                'geometry': mapping(oa_area_shape['geometry']),
                'properties': {
                    'lower_id': oa_area_shape['lower_id'],
                }
            })
            points.append({
                'type': 'Feature',
                'geometry': mapping(oa_area_shape['geometry'].representative_point()),
                'properties': {
                    'lower_id': oa_area_shape['lower_id'],
                }
            })

    shapes = gpd.GeoDataFrame.from_features(shapes)
    points = gpd.GeoDataFrame.from_features(points)

    return shapes, points


def get_lad_list(lads, oa_points):
    """

    """
    oa_points = gpd.overlay(oa_points, lads, how='intersection')

    lad_list = oa_points['name'].to_list()

    return oa_points, lad_list


def get_oa_area_boundaries(lad_id, oa_points, oa_shapes):
    """

    """
    pcd_subset = oa_points.loc[oa_points['name'] == lad_id]

    pcds_in_lad_list = pcd_subset['lower_id'].to_list()

    oa_shapes_subset = []

    for idx, pcd_shape in oa_shapes.iterrows():
        if pcd_shape['lower_id'] in pcds_in_lad_list:
            oa_shapes_subset.append({
                'type': 'Feature',
                'geometry': mapping(pcd_shape['geometry']),
                'properties': {
                    'lower_id': pcd_shape['lower_id'],
                }
            })

    oa_shapes_subset = gpd.GeoDataFrame.from_features(oa_shapes_subset)

    return oa_shapes_subset


if __name__ == '__main__':

    # print('Loading oa list')
    # path = os.path.join(BASE_PATH, 'intermediate', 'oa_list.csv')
    # oa_areas = pd.read_csv(path)
    # oa_areas = oa_areas['lower_id'].tolist()

    print('Load and subset oa areas')
    path = os.path.join(BASE_PATH, 'intermediate', 'output_areas.shp')
    oa_shapes = gpd.read_file(path)
    oa_shapes.crs = 'epsg:27700'
    oa_shapes = oa_shapes.to_crs('epsg:27700')
    oa_shapes, oa_points = subset_areas_with_data(oa_areas, oa_shapes)

    print('Load and subset lads')
    path = os.path.join(BASE_PATH, 'shapes', 'lad_uk_2016-12.shp')
    lads = gpd.read_file(path, crs='epsg:27700')
    oa_points.crs = 'epsg:27700'

    oa_points, lad_list = get_lad_list(lads, oa_points)

    for lad_id in lad_list:

        print('Loading data for {}'.format(lad_id))

        path = os.path.join(BASE_PATH, 'prems_by_lad', lad_id)

        # if not os.path.exists(path):

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

        oa_shapes_subset = get_oa_area_boundaries(lad_id, oa_points, oa_shapes)

        lad_folder = os.path.join(BASE_PATH, 'intermediate', 'prems', lad_id)
        if not os.path.exists(lad_folder):
            os.makedirs(lad_folder)

        for oa_shape_id in oa_shapes_subset['lower_id'].unique():

            # if not oa_shape_id == 'CB41':
            #     continue

            path = os.path.join(BASE_PATH, 'intermediate', 'prems', lad_id, oa_shape_id + '.csv')

            if not os.path.exists(path):

                print('Working on {}'.format(oa_shape_id))

                curent_oa = oa_shapes_subset.loc[oa_shapes_subset['lower_id'] == oa_shape_id]

                prems_within_oa = gpd.overlay(prems_by_lad, curent_oa, how='intersection')

                prems_within_oa.to_csv(path, index=False)

                path = os.path.join(BASE_PATH, 'intermediate', 'prems', lad_id, oa_shape_id + '.shp')
                prems_within_oa.to_file(path, crs='epsg:27700')
