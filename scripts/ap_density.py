"""
Calculate AP density.

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
import numpy as np
import seaborn as sns; sns.set()
import matplotlib.pyplot as plt

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']


def subset_points(folder, files):
    """

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


def grid_area(boundary):
    """

    """
    xmin, ymin, xmax, ymax = boundary['geometry'].total_bounds

    length = 50
    wide = 50

    cols = list(range(int(np.floor(xmin)), int(np.ceil(xmax)), wide))
    rows = list(range(int(np.floor(ymin)), int(np.ceil(ymax)), length))
    rows.reverse()

    polygons = []
    for x in cols:
        for y in rows:
            polygons.append(Polygon([(x, y), (x+wide, y), (x+wide, y-length), (x, y-length)]))

    grid = gpd.GeoDataFrame({'geometry':polygons})

    return grid


def union_of_points(data):
    """

    """
    buffer = data.buffer(30)
    union = buffer.unary_union
    geom = mapping(union)

    interim = []

    if geom['type'] == 'MultiPolygon':
        for idx, item in enumerate(geom['coordinates']):
                interim.append({
                    'geometry': {
                        'type': 'Polygon',
                        'coordinates': item,
                    },
                    'properties': {
                    }
                })
    else:
        interim.append({
            'geometry': geom,
            'properties': {
            }
        })

    union = gpd.GeoDataFrame.from_features(interim)

    return union


def create_general_buffer(collected_aps, aps_buffered, codepoint_polys):
    """

    """
    f = lambda x:np.sum(collected_aps.intersects(x))
    aps_buffered['waps_collected'] = aps_buffered['geometry'].apply(f)

    aps_buffered['area_km2'] = aps_buffered['geometry'].area / 1e6

    aps_buffered['waps_km2'] = (
        aps_buffered['waps_collected'] / aps_buffered['area_km2'])

    f = lambda x:np.sum(codepoint_polys.intersects(x))
    aps_buffered['rmdps'] = aps_buffered['geometry'].apply(f)

    aps_buffered['rmdps_km2'] = (
        aps_buffered['rmdps'] / aps_buffered['area_km2'])

    return aps_buffered


def subset_codepoint(pcd_sector, boundary):
    """

    """
    pcd_area = pcd_sector[:2]
    pcd_area = ''.join([i for i in pcd_area if not i.isdigit()])

    filename = '{}.shp'.format(pcd_area)
    path = os.path.join(BASE_PATH, 'codepoint', 'shapes', filename)
    codepoint_polys = gpd.read_file(path, crs='epsg:27700')

    filename = '{}_vstreet_lookup.txt'.format(pcd_area)
    path = os.path.join(BASE_PATH, 'codepoint', 'shapes',filename)
    verticals = open(path, "r")

    v_lookup = {}

    for vertical in verticals:

        pcd_id = vertical.split(',')[0]
        pcd_id = pcd_id[1:8].replace('"', '')
        vertical_id = vertical.split(',')[1]
        vertical_id = vertical_id[1:9].replace('"', '')
        v_lookup[vertical_id] = pcd_id

    centroids = codepoint_polys.copy()
    centroids['geometry'] = centroids['geometry'].representative_point()
    centroids = centroids[centroids.intersects(boundary.unary_union)]

    interim = []

    for idx, poly in codepoint_polys.iterrows():

        if poly['POSTCODE'] in centroids['POSTCODE'].unique():
            if poly['POSTCODE'].startswith('V'): # and poly['POSTCODE'] in v_lookup.keys()
                pcd = v_lookup[poly['POSTCODE']]
                poly['POSTCODE'] = pcd

            interim.append({
                'type': 'Feature',
                'geometry': mapping(poly['geometry'].representative_point()),
                'properties': {
                    'POSTCODE': poly['POSTCODE'],
                }
            })

    #import codepoint delivery point data from csv and merge
    filename = '{}.csv'.format(pcd_area)
    path = os.path.join(BASE_PATH, 'codepoint', 'csvs', filename)
    codepoint_lut = pd.read_csv(path)
    codepoint_lut = codepoint_lut.to_records().tolist()

    output = []

    for item in interim:
        for lut_item in codepoint_lut:
            if item['properties']['POSTCODE'] == lut_item[1]:
                output.append({
                    'type': item['type'],
                    'geometry': item['geometry'],
                    'properties': {
                        'POSTCODE': item['properties']['POSTCODE'],
                        # 'po_box': lut_item[3],
                        'total_rmdps': lut_item[4],
                        # 'domestic': lut_item[6],
                        # 'non_domestic': lut_item[7],
                        # 'po_boxes': lut_item[8],
                        # 'type': lut_item[19]
                    }
                })

    output = gpd.GeoDataFrame.from_features(output)

    return output


def intersect_grid_w_points(grid, all_data, codepoint_polys):
    """

    """
    print('Intersecting grid with collected waps data')
    f = lambda x:np.sum(all_data.intersects(x))
    grid['waps_collected'] = grid['geometry'].apply(f)

    grid['area_km2'] = grid['geometry'].area / 1e6

    grid['waps_km2'] = grid['waps_collected'] / grid['area_km2']

    print('Total grid squares {}'.format(len(grid)))
    grid = grid.loc[grid['waps_km2'] > 0]
    print('Subset of grid squares without waps data {}'.format(len(grid)))

    print('Intersecting grid with rmdps data')
    f = lambda x:np.sum(codepoint_polys.intersects(x))
    grid['total_rmdps'] = grid['geometry'].apply(f)

    grid['rmdps_km2'] = grid['total_rmdps'] / grid['area_km2']

    print('Total grid squares {}'.format(len(grid)))
    grid = grid.loc[grid['total_rmdps'] > 0]
    print('Subset of grid squares without rmdps data {}'.format(len(grid)))
    return grid


def plot_results(data, pcd_sector):
    """

    """
    data = data.loc[data['waps_km2'] > 0]

    title = 'Collected Versus Predicted WiFi APs: {}'.format(pcd_sector)

    plot = sns.regplot(x="waps_km2", y="rmdps_km2", data=data).set_title(title)

    plt.xlabel('Density of Collected WiFi APs (km^2)')
    plt.ylabel('Density of Postal Delivery Points (km^2)')
    fig = plot.get_figure()
    fig.savefig(os.path.join(results, pcd_sector, "plot.png"))
    plt.clf()

if __name__ == '__main__':

    path = os.path.join(BASE_PATH, 'intermediate', 'pcd_list.csv')
    pcd_sectors = pd.read_csv(path)

    # pcd_sectors = [
    #     # ('N78', 'london', 'n', 'N78 - Urban'),
    #     ('W1G6', 'london', 'w', 'W1G6 - Dense Urban'),
    #     ('W1H2', 'london', 'w', 'W1H2 - Dense Urban'),
    #     ('CB41', 'cambridge', 'cb', 'CB41 - Suburban'),
    # ]

    path = os.path.join(BASE_PATH, 'shapes', 'PostalSector.shp')
    pcd_sector_shapes = gpd.read_file(path)
    pcd_sector_shapes.crs = 'epsg:27700'
    pcd_sector_shapes = pcd_sector_shapes.to_crs('epsg:27700')

    folder_kml = os.path.join(BASE_PATH, 'wigle', 'all_kml_data')
    files = os.listdir(folder_kml)

    results = os.path.join(BASE_PATH, '..', 'results')
    if not os.path.exists(results):
        os.makedirs(results)

    path = os.path.join(BASE_PATH, 'intermediate', 'all_collected_points.shp')
    if not os.path.exists(path):
        all_data = subset_points(folder_kml, files)
    else:
        all_data = gpd.read_file(path, crs='epsg:27700')

    for idx, row in pcd_sectors.iterrows():

        pcd_sector = row['StrSect']

        if not pcd_sector == 'CB11':
            continue

        print('-- Working on {}'.format(pcd_sector))

        print('Getting data')
        folder = os.path.join(BASE_PATH, '..', 'results', str(pcd_sector))
        if not os.path.exists(folder):
            os.makedirs(folder)

        print('Getting boundary')
        path = os.path.join(folder, 'boundary.shp')
        if not os.path.exists(path):
            boundary = pcd_sector_shapes.loc[pcd_sector_shapes['StrSect'] == pcd_sector]
            boundary.to_file(path, crs='epsg:27700')
        else:
            boundary = gpd.read_file(path, crs='epsg:27700')

        print('Create grid')
        path = os.path.join(folder, 'grid.shp')
        if not os.path.exists(path):
            grid = grid_area(boundary)
            grid.to_file(path, crs='epsg:27700')
        else:
            grid = gpd.read_file(path, crs='epsg:27700')

        print('Processing collected points')
        collected_data = os.path.join(folder, 'collected_points.shp')
        if not os.path.exists(collected_data):
            points_subset = all_data[all_data.intersects(boundary.unary_union)]
            points_subset.to_file(collected_data, crs='epsg:27700')
        else:
            points_subset = gpd.read_file(collected_data, crs='epsg:27700')

        print('Subsetting codepoint')
        path = os.path.join(folder, 'codepoint_polys.shp')
        if not os.path.exists(path):
            codepoint_polys = subset_codepoint(pcd_sector, boundary)
            if len(codepoint_polys) > 0:
                codepoint_polys.to_file(path, crs='epsg:27700')
            else:
                print('Unable to match postcode polys to codepoint rmdps data')
                continue
        else:
            codepoint_polys = gpd.read_file(path, crs='epsg:27700')

        print('Intersecting grid with points')
        path = os.path.join(folder, 'grid_with_points.csv')
        if not os.path.exists(path):
            if len(codepoint_polys) > 0:
                postcode_aps = intersect_grid_w_points(grid, points_subset, codepoint_polys)
                postcode_aps.to_file( os.path.join(folder, 'postcode_aps.shp'), crs='epsg:27700')
                postcode_aps.to_csv(os.path.join(folder, 'postcode_aps.csv'), index=False)
            else:
                pass
        else:
            postcode_aps = pd.read_csv(path)

        print('Plot results')
        plot_results(postcode_aps, pcd_sector)

    print('Completed script')
