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
    Only return those output area shapes for which we have data for.

    """
    shapes = []
    points = []

    for idx, oa_area_shape in oa_area_shapes.iterrows():
        if oa_area_shape['msoa'] in oa_areas:
            shapes.append({
                'type': 'Feature',
                'geometry': mapping(oa_area_shape['geometry']),
                'properties': {
                    'msoa': oa_area_shape['msoa'],
                }
            })
            points.append({
                'type': 'Feature',
                'geometry': mapping(oa_area_shape['geometry'].representative_point()),
                'properties': {
                    'msoa': oa_area_shape['msoa'],
                }
            })

    shapes = gpd.GeoDataFrame.from_features(shapes)
    points = gpd.GeoDataFrame.from_features(points)

    return shapes, points


def get_lad_list(lads, oa_points):
    """
    Get a list of the local authority districts for which we have data for.

    """
    oa_points = gpd.overlay(oa_points, lads, how='intersection')

    lad_list = oa_points['name'].to_list()

    return oa_points, lad_list


def get_oa_area_boundaries(lad_id, oa_points, oa_shapes):
    """
    Return only the output area shapes in a single local authority district.

    """
    subset = oa_points.loc[oa_points['name'] == lad_id]

    oas_in_lad_list = subset['msoa'].to_list()

    oa_shapes_subset = []

    for idx, oa_shape in oa_shapes.iterrows():
        if oa_shape['msoa'] in oas_in_lad_list:
            oa_shapes_subset.append({
                'type': 'Feature',
                'geometry': mapping(oa_shape['geometry']),
                'properties': {
                    'msoa': oa_shape['msoa'],
                }
            })

    oa_shapes_subset = gpd.GeoDataFrame.from_features(oa_shapes_subset)

    return oa_shapes_subset


if __name__ == '__main__':

    print('Loading oa list')
    path = os.path.join(BASE_PATH, 'intermediate', 'oa_list.csv')
    oa_areas = pd.read_csv(path)
    oa_areas = oa_areas['msoa'].tolist()

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

        lad_folder = os.path.join(BASE_PATH, 'intermediate', 'prems_by_lad_msoa', lad_id)
        if not os.path.exists(lad_folder):
            os.makedirs(lad_folder)

        for oa_shape_id in oa_shapes_subset['msoa'].unique():

            path = os.path.join(lad_folder, oa_shape_id + '.csv')

            if not os.path.exists(path):

                print('Working on {}'.format(oa_shape_id))

                curent_oa = oa_shapes_subset.loc[oa_shapes_subset['msoa'] == oa_shape_id]

                prems_within_oa = gpd.overlay(prems_by_lad, curent_oa, how='intersection')

                prems_within_oa.to_csv(path, index=False)
