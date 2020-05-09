"""
Identify daytime and nighttime population.

Written by Ed Oughton

March 2020 (Amid coronavirus lockdown)

"""
import os
import sys
import configparser
import csv
import fiona
import time

from shapely.geometry import shape, Point, LineString, mapping
from shapely.ops import  cascaded_union
from tqdm import tqdm

from rtree import index

from collections import OrderedDict

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

#####################################
# READ MAIN DATA
#####################################


def read_area_shapes(path_ew, path_s):
    """
    Read in all area shapes.

    """
    output = []

    with fiona.open(path_ew, 'r') as reader:
        for lsoa in reader:
            output.append({
                'type': lsoa['type'],
                'geometry': lsoa['geometry'],
                'properties': {
                    'code': lsoa['properties']['LSOA11CD'],
                    # 'LSOA11NM': lsoa['properties']['LSOA11NM'],
                }
            })

    with fiona.open(path_s, 'r') as reader:
        for datazone in reader:
            output.append({
                'type': datazone['type'],
                'geometry': datazone['geometry'],
                'properties': {
                    'code': datazone['properties']['DataZone'],
                    # 'LSOA11NM': lsoa['properties']['LSOA11NM'],
                }
            })

    return output


def load_employment_data(paths):
    """
    Load BRES employment data for areas.

    """
    output = []

    for path in paths:
        with open(path, 'r') as source:
            reader = csv.DictReader(source)
            for line in reader:
                output.append({
                    'code': line['code'],
                    # 'name': line['name'],
                    'count': line['count'],
                })

    return output


def combine_data(areas, employment):
    """
    Combine areas and employment data.

    """
    output = []

    for item in employment:
        for area in areas:
            if item['code'] == area['properties']['code']:
                geom = shape(area['geometry'])
                output.append({
                    'type': area['type'],
                    'geometry': mapping(geom.representative_point()),
                    'properties': {
                        'code': area['properties']['code'],
                        # 'LSOA11NM': area['properties']['LSOA11NM'],
                        'employment': item['count']
                    }
                })

    return output


def read_postcode_sectors(path):
    """
    Read all postcode sector shapes.

    """
    with fiona.open(path, 'r') as pcd_sector_shapes:
        return [pcd for pcd in pcd_sector_shapes]


def add_employment_to_pcd_sectors(postcode_sectors, areas):
    """
    Add the LAD indicator(s) to the relevant postcode sector.

    """
    lut = []

    idx = index.Index(
        (i, shape(postcode_sector['geometry']).bounds, postcode_sector)
        for i, postcode_sector in enumerate(postcode_sectors)
    )

    for area in tqdm(areas):
        employment = 0
        for n in idx.intersection((shape(area['geometry']).bounds), objects=True):
            postcode_sector_centroid = shape(area['geometry']).centroid
            lad_shape = shape(n.object['geometry'])
            if postcode_sector_centroid.intersects(lad_shape):
                lut.append({
                    'area': area['properties']['code'],
                    'postcode_sector': n.object['properties']['StrSect'],
                    'employment': int(area['properties']['employment']),
                    })

    output = []

    for postcode_sector in postcode_sectors:
        employment = 0
        for item in lut:
            if postcode_sector['properties']['StrSect'] == item['postcode_sector']:
                employment += item['employment']
        output.append({
            'StrSect': postcode_sector['properties']['StrSect'],
            'employment': employment,
        })

    return output


def csv_writer(data, directory, filename):
    """
    Write data to a CSV file path

    """
    if not os.path.exists(directory):
        os.makedirs(directory)

    fieldnames = []
    for name, value in data[0].items():
        fieldnames.append(name)

    with open(os.path.join(directory, filename), 'w') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames, lineterminator = '\n')
        writer.writeheader()
        writer.writerows(data)


if __name__ == "__main__":

    start = time.time()

    directory_intermediate = os.path.join(BASE_PATH, 'daytime_employment')
    print('Output directory will be {}'.format(directory_intermediate))

    print('Loading area shapes')
    area_shapes_ew = os.path.join(BASE_PATH, 'shapes', 'lsoas_ew_27700.shp')
    area_shapes_s = os.path.join(BASE_PATH, 'shapes', 'SG_DataZone_Bdry_2011.shp')
    areas = read_area_shapes(area_shapes_ew, area_shapes_s)#[:2000]

    print('Loading employment data')
    paths = [
        os.path.join(BASE_PATH, 'employment', 'employment_ew.csv'),
        os.path.join(BASE_PATH, 'employment', 'employment_s.csv')
        ]
    employment = load_employment_data(paths)#[:2000]

    print('Combine areas with employment data')
    areas = combine_data(areas, employment)

    print('Loading postcode sector shapes')
    path = os.path.join(BASE_PATH, 'shapes', 'PostalSector.shp')
    postcode_sectors = read_postcode_sectors(path)#[:2000]

    print('Adding employment to postcode sectors')
    postcode_sectors = add_employment_to_pcd_sectors(postcode_sectors, areas)

    print('Writing postcode sectors to .csv')
    csv_writer(postcode_sectors, directory_intermediate, 'daytime_employment.csv')

    end = time.time()
    print('time taken: {} minutes'.format(round((end - start) / 60,2)))
