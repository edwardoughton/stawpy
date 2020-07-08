"""
Calculate AP density using circular buffers.

Written by Ed Oughton.

April 2020

"""
import os
import csv
import configparser
import pandas as pd
import geopandas as gpd
from pykml import parser
from shapely.geometry import mapping, Polygon
from shapely import wkt
import numpy as np
import seaborn as sns; sns.set()
import matplotlib.pyplot as plt

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']


def define_geotypes(oa_geotypes):
    """

    """
    output = {}

    for idx, row in oa_geotypes.iterrows():

        output[row['msoa']] = {
            'lad': row['lad'],
            'region': row['region'],
            'population': row['population'],
            'area_km2': row['area_km2'],
            'pop_density_km2': row['pop_density_km2'],
            'households': row['households'],
            'geotype': row['geotype'],
        }

    return output


def load_collected_ap_data(folder, files):
    """
    Load existing AP data collected.

    """
    all_data = []

    for filename in files:

        if not filename.endswith('.kml'):
            continue

        print('Loading {}'.format(filename))
        path = os.path.join(folder, filename)

        data = load_data(path)

        all_data = all_data + data

    all_data = gpd.GeoDataFrame.from_features(all_data)
    all_data.crs = 'epsg:4326'
    all_data = all_data.to_crs('epsg:27700')

    return all_data


def load_data(path):
    """
    Load existing AP data collected from Wigle to geojson.

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


def process_points(points, buffer_size):
    """
    First, merge very close points with a union. Second, add
    desired buffer to points.

    """
    points['geometry'] = points['geometry'].buffer(2)

    points_union = points.unary_union

    if points_union.geom_type == 'MultiPolygon':
        points = list(points_union)
    if points_union.geom_type == 'Polygon':
        points = []
        points.append(points_union)

    points = gpd.GeoDataFrame.from_features(
        [
            {'geometry': geom, 'properties':{'FID': idx}}
            for idx, geom in enumerate(points)
        ],
        crs='epsg:27700'
    )

    points['geometry'] = points['geometry'].representative_point()

    points['geometry'] = points['geometry'].buffer(buffer_size)

    return points


def get_geojson_buildings(loaded_buildings):
    """

    """
    output = []

    for idx, building in loaded_buildings.iterrows():
        geom = wkt.loads(building['geometry'])
        output.append({
            'geometry': geom.representative_point(),
            'properties': {
                'mfc': building['mistral_function_class'], #mistral_function_class
                'mbc': building['mistral_building_class'], #
                'rc': building['res_count'], #res_count
                'fa': building['floor_area'], #res_count
                'htrb': building['height_toroofbase'], #height_toroofbase
                'htrt': building['height_torooftop'], #height_torooftop
                'nrc': building['nonres_count'], #nonres_count
                'nof': building['number_of_floors'], #number_of_floors
                'fpa': building['footprint_area'], #footprint_area
            }
        })

    return output

def intersect_w_points(buffered_points, all_data, buildings, oa_data):
    """
    Convert point data to buffered points by intersecting.

    """
    print('Intersecting buffers with collected waps data')
    f = lambda x:np.sum(all_data.intersects(x))
    buffered_points['waps_collected'] = buffered_points['geometry'].apply(f)

    buffered_points['area_km2'] = buffered_points['geometry'].area / 1e6

    buffered_points['waps_km2'] = buffered_points['waps_collected'] / buffered_points['area_km2']

    print('Total buffered_points {}'.format(len(buffered_points)))
    buffered_points = buffered_points.loc[buffered_points['waps_km2'] > 0]
    print('Subset of buffered_points with waps data {}'.format(len(buffered_points)))

    print('Add buffered_points ids to building layer')
    try:
        merged = gpd.overlay(buildings, buffered_points, how='intersection')
    except:
        return 'Unable to complete intersection'
    print(merged.columns)
    merged = merged[[
        'mfc',
        'mbc',
        'rc',
        'fa',
        'htrb',
        'htrt',
        'nrc',
        'nof',
        'fpa',
        'FID',
        'waps_collected',
        'area_km2',
        'waps_km2'
    ]]
    merged = merged[merged["fa"] > 100]
    merged = merged.to_dict('records')

    buffered_points_aggregated = []

    for idx, buffered_point in buffered_points.iterrows():
        res_count = 0
        floor_area = 0
        adjusted_floor_area = 0
        building_count = 0
        nonres_count = 0

        for merged_points in merged:
            if buffered_point['FID'] == merged_points['FID']:
                res_count += merged_points['rc']
                if merged_points['nof'] <= 2: #if number of floors < 2
                    floor_area += merged_points['fa']
                    adjusted_floor_area += merged_points['fa']
                else:
                    floor_area += merged_points['fa']
                    #assume APs at or above 3 floors can't be accessed
                    adjusted_floor_area += (merged_points['fpa'] * 2)

                building_count += 1
                nonres_count += merged_points['nrc']

        area_km2 = buffered_point['geometry'].area / 1e6

        buffered_points_aggregated.append({
            'geometry': buffered_point['geometry'],
            'properties': {
                'res_count': res_count,
                'floor_area': floor_area,
                'adjusted_floor_area': adjusted_floor_area,
                'building_count': building_count,
                'nonres_count': nonres_count,
                'waps_collected': buffered_point['waps_km2'] * area_km2,
                'waps_km2': buffered_point['waps_km2'],
                'area_km2': area_km2,
                'FID': buffered_point['FID'],
                'geotype': oa_data['geotype'],
                'lad': oa_data['lad'],
                'population': oa_data['population'],
                'area_km2': oa_data['area_km2'],
                'pop_density_km2': oa_data['pop_density_km2'],
                'geotype': oa_data['geotype'],
            }
        })

    buffered_points_aggregated = gpd.GeoDataFrame.from_features(buffered_points_aggregated, crs='epsg:27700')
    buffered_points_aggregated.to_file(os.path.join(folder, 'merged.shp'), crs='epsg:27700')

    print('Total buffers {}'.format(len(buffered_points_aggregated)))
    buffered_points_aggregated = buffered_points_aggregated.loc[buffered_points_aggregated['floor_area'] > 0]
    print('Subset of buffers without rmdps data {}'.format(len(buffered_points_aggregated)))

    return buffered_points_aggregated


if __name__ == '__main__':

    path = os.path.join(BASE_PATH, 'intermediate', 'oa_list.csv')
    oa_data = pd.read_csv(path)
    oa_data = oa_data.iloc[::-1]

    path = os.path.join(BASE_PATH, 'intermediate', 'output_areas.shp')
    oa_shapes = gpd.read_file(path)
    oa_shapes.crs = 'epsg:27700'
    oa_shapes = oa_shapes.to_crs('epsg:27700')

    path = os.path.join(BASE_PATH, 'shapes', 'lad_uk_2016-12.shp')
    lad_shapes = gpd.read_file(path)
    lad_shapes.crs = 'epsg:27700'
    lad_shapes = lad_shapes.to_crs('epsg:27700')

    filename = 'oa_lookup.csv'
    path = os.path.join(BASE_PATH, 'intermediate', filename)
    oa_geotypes = pd.read_csv(path)
    oa_geotypes = define_geotypes(oa_geotypes)

    folder_kml = os.path.join(BASE_PATH, 'wigle', 'all_kml_data')
    files = os.listdir(folder_kml)

    results = os.path.join(BASE_PATH, '..', 'results')
    if not os.path.exists(results):
        os.makedirs(results)

    path = os.path.join(BASE_PATH, 'intermediate', 'all_collected_points.shp')
    if not os.path.exists(path):
        all_data = load_collected_ap_data(folder_kml, files)
    else:
        all_data = gpd.read_file(path, crs='epsg:27700')

    buffer_sizes = [100]#[50, 100, 200]
    problem_oa_data = []

    #W1H 2
    #W1G 6
    #W1G 8

    for buffer_size in buffer_sizes:

        for idx, row in oa_data.iterrows():

            oa = row['msoa']

            # if not oa == 'E02003731':
            #     continue

            print('-- Working on {} with {}m buffer'.format(oa, buffer_size))

            oa_geotype = oa_geotypes[oa]

            # if not oa_geotype['lad'] == 'E07000008':
            #     continue

            print('Creating a results folder (if one does not exist already)')
            folder = os.path.join(BASE_PATH, '..', 'results', str(oa))
            if not os.path.exists(folder):
                os.makedirs(folder)

            print('Getting output area boundary')
            path = os.path.join(folder, 'boundary.shp')
            if not os.path.exists(path):
                boundary = oa_shapes.loc[oa_shapes['msoa'] == oa]
                boundary.to_file(path, crs='epsg:27700')
            else:
                boundary = gpd.read_file(path, crs='epsg:27700')

            print('Getting the LAD(s) which intersect the output area')
            bbox = boundary.envelope
            geo = gpd.GeoDataFrame()
            geo = gpd.GeoDataFrame({'geometry': bbox}, crs='epsg:27700')
            merged = gpd.overlay(geo, lad_shapes, how='intersection')

            print('Catch overlaps across lad boundaries')
            lad_ids = []
            for idx, row in merged.iterrows():
                lad_ids.append(row['name'])
            print('Need data for the following LADs {}'.format(lad_ids))

            print('Subsetting the collected points for the output area')
            collected_data = os.path.join(folder, 'collected_points.shp')
            if not os.path.exists(collected_data):
                points_subset = all_data[all_data.intersects(boundary.unary_union)]
                points_subset = points_subset.drop_duplicates('network_id')
                points_subset.to_file(collected_data, crs='epsg:27700')
            else:
                points_subset = gpd.read_file(collected_data, crs='epsg:27700')

            print('Getting buffered points')
            collected_data = os.path.join(folder, 'buffered_points_{}.shp'.format(buffer_size))
            if not os.path.exists(collected_data):
                print('Processing buffered points')
                buffered_points = process_points(points_subset, buffer_size)
                buffered_points.to_file(collected_data, crs='epsg:27700')
            else:
                buffered_points = gpd.read_file(collected_data, crs='epsg:27700')

            print('Subsetting the premises data for the output area')
            path = os.path.join(folder, 'buildings.shp')
            buildings = gpd.GeoDataFrame()
            if not os.path.exists(path):
                for lad_id in lad_ids:
                    directory = os.path.join(BASE_PATH, 'intermediate', 'prems_by_lad_msoa', lad_id)
                    path_buildings = os.path.join(directory, oa + '.csv')

                    if not os.path.exists(path_buildings):
                        print('Unable to find building data for {}'.format(oa))
                        continue
                    else:
                        loaded_buildings = pd.read_csv(path_buildings)
                        loaded_buildings = get_geojson_buildings(loaded_buildings)
                        loaded_buildings = gpd.GeoDataFrame.from_features(loaded_buildings)
                        buildings = buildings.append(loaded_buildings, ignore_index=True)

                    if len(buildings) > 0:
                        buildings.to_file(path, crs='epsg:27700')
                    else:
                        print('Unable to find building data for {}'.format(oa))
                        continue
                buildings.crs = 'epsg:27700'
            else:
                buildings = gpd.read_file(path, crs='epsg:27700')

            print('Intersecting buffered points with collected and building points layers')
            if len(buildings) > 0:
                oa_aps = intersect_w_points(buffered_points, points_subset, buildings, oa_geotype)
                oa_aps['msoa'] = oa
                if len(oa_aps) > 0:
                    if not type(oa_aps) is str:
                        oa_aps.to_file( os.path.join(folder, 'oa_aps_buffered_{}.shp'.format(buffer_size)), crs='epsg:27700')
                        oa_aps.to_csv(os.path.join(folder, 'oa_aps_buffered_{}.csv'.format(buffer_size)), index=False)
                    else:
                        print('Unable to process {}'.format(oa))
                        problem_oa_data.append(str(oa))
            else:
                pass
