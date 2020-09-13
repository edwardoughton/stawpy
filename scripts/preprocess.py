"""
Preprocess OA lookup table

"""
import os
import csv
import configparser
import pandas as pd
import geopandas as gpd
import math
import random
from shapely.geometry import mapping, MultiPolygon
from tqdm import tqdm

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

random.seed(43)


def process_shapes(path_output, path_ew, path_scot, lookup):
    """
    Process all shape boundaries for ~8,000 areas.

    """
    folder = os.path.join(BASE_PATH, 'intermediate')

    if not os.path.exists(os.path.join(folder, 'output_areas.csv')):

        data_ew = gpd.read_file(path_ew, crs='epsg:27700')#[:10]
        data_ew = data_ew[['msoa11cd', 'geometry']]
        data_ew.columns = ['msoa', 'geometry']

        data_scot = gpd.read_file(path_scot, crs='epsg:27700')#[:200]
        data_scot = data_scot[['InterZone', 'geometry']]
        data_scot.columns = ['msoa', 'geometry']

        all_data = data_ew.append(data_scot, ignore_index=True)

        all_data['geometry'] = all_data.apply(remove_small_shapes, axis=1)

        all_data['geometry'] = all_data.simplify(
            tolerance = 10,
            preserve_topology=True).buffer(0.0001).simplify(
                tolerance = 10,
                preserve_topology=True
            )

        all_data['area_km2'] = all_data['geometry'].area / 1e6

        lookup = pd.read_csv(lookup)
        lookup = lookup[['MSOA11CD', 'RGN11NM']]
        lookup = lookup.drop_duplicates()
        lookup.columns = ['msoa', 'region']
        all_data = (pd.merge(all_data, lookup, on='msoa'))

        all_data.to_file(path_output, crs='epsg:27700')

        all_data = all_data[['msoa', 'area_km2', 'region']]
        out_path = os.path.join(folder, 'output_areas.csv')
        all_data.to_csv(out_path, index=False)

    else:
        all_data = pd.read_csv(os.path.join(folder, 'output_areas.csv'))

    return all_data


def remove_small_shapes(x):
    """
    Get rid of small geometries.

    """
    # if its a single polygon, just return the polygon geometry
    if x.geometry.geom_type == 'Polygon':
        return x.geometry

    # if its a multipolygon, we start trying to simplify
    # and remove shapes if its too big.
    elif x.geometry.geom_type == 'MultiPolygon':

        area1 = 1e7
        area2 = 5e7

        # don't remove shapes if total area is already very small
        if x.geometry.area < area1:
            return x.geometry

        if x.geometry.area > area2:
            threshold = 5e6
        else:
            threshold = 5e6

        # save remaining polygons as new multipolygon for
        # the specific country
        new_geom = []
        for y in x.geometry:
            if y.area > threshold:
                new_geom.append(y)

        return MultiPolygon(new_geom)


def process_area_features(path_output, data):
    """
    Load shapes and extract required urban/rural information.

    """
    data = all_data.to_dict('records')

    output = {}

    for item in data:
        output[item['msoa']] = {
            'area_km2': item['area_km2'],
            'region': item['region'],
        }

    return output


def get_lads(path):
    """
    Get all unique Local Authority District IDs.

    """
    path_output = os.path.join(BASE_PATH, 'intermediate', 'prems_by_lad_msoa')

    if not os.path.exists(path_output):
        os.makedirs(path_output)

    all_data = pd.read_csv(path)

    all_data = all_data.to_dict('records')

    unique_lads = set()

    for item in all_data:
        unique_lads.add(item['LAD17CD'])

    unique_lads = list(unique_lads)#[:10]

    for lad in list(unique_lads):

        path_lad = os.path.join(path_output, lad)

        if not os.path.exists(path_lad):
            os.makedirs(path_lad)

        lookup = []

        for item in all_data:
            if lad == item['LAD17CD']:
                lookup.append({
                    'OA11CD': item['OA11CD'],
                    'LSOA11CD': item['LSOA11CD'],
                    'MSOA11CD': item['MSOA11CD']
                })

        lookup = pd.DataFrame(lookup)

        lookup.to_csv(os.path.join(path_lad, 'lookup.csv'), index=False)

    return list(unique_lads)


def get_lookup(lad):
    """
    Create a lookup table for all Middle Super Output Areas (area) (~8,000) to
    lower-level Output Areas (~190,000).

    """
    folder = os.path.join(BASE_PATH, 'intermediate', 'prems_by_lad_msoa', lad)
    path = os.path.join(folder, 'lookup.csv')
    all_data = pd.read_csv(path)

    unique_msoas = all_data['MSOA11CD'].unique()

    all_data = all_data.to_dict('records')

    lookup = {}

    for msoa in unique_msoas:
        oa_ids = []
        for item in all_data:
            if msoa == item['MSOA11CD']:
                oa_ids.append(item['OA11CD'])
        lookup[msoa] = oa_ids

    return unique_msoas, lookup


def write_premises_data(lad):
    """
    Aggregate Output Area premises data into Middle Super Output Areas and write.

    """
    path_lad = os.path.join(BASE_PATH, 'prems_by_lad', lad)

    unique_msoas, lookup = get_lookup(lad)

    directory = os.path.join(BASE_PATH, 'intermediate', 'prems_by_lad_msoa', lad)

    for msoa in unique_msoas:

        path_output = os.path.join(directory, msoa + '.csv')

        if os.path.exists(path_output):
            continue

        oas = lookup[msoa]

        prems_by_msoa = []

        for oa in oas:

            path_oa = os.path.join(path_lad, oa + '.csv')

            if not os.path.exists(path_oa):
                continue

            prems = pd.read_csv(path_oa)

            prems = prems.to_dict('records')

            for prem in prems:
                prems_by_msoa.append({
                    'mistral_function_class': prem['mistral_function_class'],
                    'mistral_building_class': prem['mistral_building_class'],
                    'res_count': prem['res_count'],
                    'floor_area': prem['floor_area'],
                    'height_toroofbase': prem['height_toroofbase'],
                    'height_torooftop': prem['height_torooftop'],
                    'nonres_count': prem['nonres_count'],
                    'number_of_floors': prem['number_of_floors'],
                    'footprint_area': prem['footprint_area'],
                    'geometry': prem['geom'],
                })

        prems_by_msoa = pd.DataFrame(prems_by_msoa)
        prems_by_msoa.to_csv(path_output, index=False)


def write_hh_data(lad):
    """
    Get the estimated household demographics for each area.

    """
    filename = 'ass_{}_area11_2018.csv'.format(lad)
    path = os.path.join(BASE_PATH, 'hh_demographics_msoa_2018', filename)

    if not os.path.exists(path):
        return

    unique_msoas, lookup = get_lookup(lad)

    directory = os.path.join(BASE_PATH, 'intermediate', 'hh_by_lad_msoa', lad)

    if not os.path.exists(directory):
        os.makedirs(directory)

    hh_data = pd.read_csv(path)

    for msoa in unique_msoas:

        path_output = os.path.join(directory, msoa + '.csv')

        if os.path.exists(path_output):
            continue

        hh_msoa_data = hh_data.loc[hh_data['Area'] == msoa]

        hh_msoa_data.to_csv(path_output, index=False)


def generate_msoa_lookup(unique_lads, area_features):
    """
    Load in all data for each area to generate a single lookup table.

    """
    output = []

    for lad in unique_lads:#[:1]:

        hh_folder = os.path.join(BASE_PATH, 'intermediate', 'hh_by_lad_msoa', lad)
        prems_folder = os.path.join(BASE_PATH, 'intermediate', 'prems_by_lad_msoa', lad)

        unique_msoas, lookup = get_lookup(lad)

        for msoa in unique_msoas:

            results = get_area_stats(msoa, lad, hh_folder, prems_folder, area_features)

            if not results == 'path does not exist':
                output.append(results)

    return output


def get_area_stats(msoa, lad, hh_folder, prems_folder, area_features):
    """
    Get the area statistics for a single area.

    """
    path = os.path.join(hh_folder, msoa + '.csv')

    if not os.path.exists(path):
        return 'path does not exist'

    hh_data = pd.read_csv(path)
    hh_data = hh_data.to_dict('records')

    households = set()
    population = set()

    for row in hh_data:
        households.add(row['HID'])
        population.add(row['PID'])

    path = os.path.join(prems_folder, msoa + '.csv')

    if not os.path.exists(path):
        return 'path does not exist'

    try:
        prems_data = pd.read_csv(path)
    except:
        return 'path does not exist'

    prems_data = prems_data.to_dict('records')

    residential = 0
    residential_floor_area = 0
    residential_footprint_area = 0
    non_residential = 0
    non_residential_floor_area = 0
    non_residential_footprint_area = 0

    for row in prems_data:
        if row['mistral_function_class'] == 'residential':
            residential += 1
            if not math.isnan(row['floor_area']):
                residential_floor_area += row['floor_area']
            if not math.isnan(row['footprint_area']):
                residential_footprint_area += row['footprint_area']
        else:
            non_residential += 1
            if not math.isnan(row['floor_area']):
                non_residential_floor_area += row['floor_area']
            if not math.isnan(row['footprint_area']):
                non_residential_footprint_area += row['footprint_area']

    area_km2 = area_features[msoa]['area_km2']
    region = area_features[msoa]['region'].lower().replace(' ', '')
    # fb_aps = area_features[msoa]['fb_ap_estimate']

    pop_density_km2 = len(population) / area_km2

    if pop_density_km2 > 7959:
        geotype = 'urban'
    elif pop_density_km2 > 782:
        geotype = 'suburban'
    else:
        geotype = 'rural'

    return {
        'msoa': msoa,
        'lad': lad,
        'region': region,
        'population': len(population),
        'area_km2': area_km2,
        'pop_density_km2': pop_density_km2,
        'geotype': geotype,
        'households': len(households),
        'prems_residential': residential,
        'prems_residential_floor_area': residential_floor_area,
        'prems_residential_footprint_area': residential_footprint_area,
        'prems_non_residential': non_residential,
        'prems_non_residential_floor_area': non_residential_floor_area,
        'prems_non_residential_footprint_area': non_residential_footprint_area,
        # 'fb_aps': fb_aps,
    }


if __name__ == '__main__':

    print('----Working on preprocessing of OA areas')
    print('----')

    print('Processing shape areas')
    filename = 'Middle_Layer_Super_Output_Areas__December_2011__Boundaries.shp'
    path_ew = os.path.join(BASE_PATH, 'msoa_shapes', filename)
    filename = 'SG_IntermediateZone_Bdry_2011.shp'
    path_scot = os.path.join(BASE_PATH, 'scottish_iz_shapes', filename)
    filename = 'Output_Area_to_LSOA_to_area_to_Local_Authority_District__December_2017__Lookup_with_Area_Classifications_in_Great_Britain.csv'
    lookup = os.path.join(BASE_PATH, 'oa_lut', filename)
    path_output = os.path.join(BASE_PATH, 'intermediate', 'output_areas.shp')
    all_data = process_shapes(path_output, path_ew, path_scot, lookup)#[:10]

    print('Processing area features')
    path_output = os.path.join(BASE_PATH, 'intermediate', 'area_features.csv')
    area_features = process_area_features(path_output, all_data)

    print('Getting unique lads')
    filename = 'Output_Area_to_LSOA_to_MSOA_to_Local_Authority_District__December_2017__Lookup_with_Area_Classifications_in_Great_Britain.csv'
    path = os.path.join(BASE_PATH, 'oa_lut', filename)
    unique_lads = get_lads(path)#[:1]

    for lad in tqdm(unique_lads):

        print('Writing lower area premises data into each LAD folder')
        write_premises_data(lad)

        print('Writing household demographic data')
        write_hh_data(lad)

    print('Generating area lookup for all data')
    results = generate_msoa_lookup(unique_lads, area_features)

    print('Exporting area lookup')
    results = pd.DataFrame(results)
    path = os.path.join(BASE_PATH, 'intermediate', 'oa_lookup.csv')
    results.to_csv(path, index=False)
