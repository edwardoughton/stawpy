"""
Calculate AP density.

Written by Ed Oughton.

April 2020

"""
import os
import csv
import configparser
import time
import pandas as pd
import geopandas as gpd
import lxml
from pykml import parser
import osmnx as ox
from shapely.geometry import mapping, Polygon
import numpy as np

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']


def subset_points(folder, files, boundary):
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

    all_data = all_data[all_data.intersects(boundary.unary_union)]

    all_data.to_file(collected_data, crs='epsg:27700')

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
    filename = '{}.shp'.format(pcd_sector[2])
    path = os.path.join(BASE_PATH, 'codepoint', filename)
    codepoint_polys = gpd.read_file(path, crs='epsg:27700')

    filename = '{}_vstreet_lookup.txt'.format(pcd_sector[2])
    path = os.path.join(BASE_PATH, 'codepoint', filename)
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
    filename = '{}.csv'.format(pcd_sector[2])
    path = os.path.join(BASE_PATH, 'codepoint', filename)
    codepoint_lut = pd.read_csv(path)
    codepoint_lut = codepoint_lut.to_records().tolist()

    output = []

    for item in interim:
        for lut_item in codepoint_lut:
            # print(lut_item)
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
    f = lambda x:np.sum(all_data.intersects(x))
    grid['waps_collected'] = grid['geometry'].apply(f)

    grid['area_km2'] = grid['geometry'].area / 1e6

    grid['waps_km2'] = grid['waps_collected'] / grid['area_km2']


    f = lambda x:np.sum(codepoint_polys.intersects(x))
    grid['total_rmdps'] = grid['geometry'].apply(f)

    grid['rmdps_km2'] = grid['total_rmdps'] / grid['area_km2']

    return grid


def intersect_buffer_w_polys(aps_buffered, codepoint_polys):
    """

    """

    aps_buffered = gpd.overlay(
        aps_buffered, codepoint_polys, how='intersection')

    aps_buffered['area_km2'] = aps_buffered['geometry'].area / 1e6

    aps_buffered['waps_km2'] = aps_buffered['waps_km2'] * aps_buffered['area_km2']

    aps_buffered['rmdps_km2'] = aps_buffered['total_rmdps'] / aps_buffered['area_km2']

    aps_buffered = aps_buffered[['geometry', 'POSTCODE', 'area_km2', 'waps_km2', 'total_rmdps', 'rmdps_km2']]

    return aps_buffered


def subset_buildings(pcd_sector, boundary):
    """

    """
    filename = '{}.shp'.format(pcd_sector[1])
    path = os.path.join(BASE_PATH, 'buildings', filename)
    buildings = gpd.read_file(path, crs='epsg:27700')

    buildings = buildings[buildings.intersects(boundary.unary_union)]

    mask = buildings['geometry'].area > 10

    buildings = buildings.loc[mask]

    return buildings


def estimate_building_ap_density(buildings, codepoint_polys):
    """

    """
    buildings = gpd.overlay(buildings, codepoint_polys, how='intersection')
    buildings['building_area_km2'] = buildings['geometry'].area / 1e6

    all_postcodes = buildings['POSTCODE'].unique()

    bulding_area_lut = []

    for postcode in all_postcodes:

        postcode_building_area_km2 = 0

        for idx, building in buildings.iterrows():
            if postcode == building['POSTCODE'] :
                postcode_building_area_km2 += building['building_area_km2']

        bulding_area_lut.append({
            'POSTCODE': postcode,
            'postcode_building_area_km2': postcode_building_area_km2,
        })

    output = []

    for idx, building in buildings.iterrows():
        for item in bulding_area_lut:
            if building['POSTCODE'] == item['POSTCODE']:

                rmdps = (building['building_area_km2'] /
                    item['postcode_building_area_km2']) * building['total_rmdps']

                output.append({
                    'type': 'Feature',
                    'geometry': building['geometry'],
                    'properties': {
                        # 'fid': building['fid'],
                        # 'POSTCODE': building['POSTCODE'],
                        # 'building_area_m': building['building_area_m'],
                        # 'postcode_building_area_m': item['postcode_building_area_m'],
                        # 'total_delivery_points': building['total'],
                        'rmdps': rmdps,
                        # 'waps'
                        # 'rmdps_km2': ap_estimate / (building['building_area_km2']),
                    }
                })

    output = gpd.GeoDataFrame.from_features(output)

    return output


def intersect_buffer_w_buildings(aps_buffered, buildings):
    """

    """
    aps_buffered = gpd.overlay(
        aps_buffered, buildings, how='intersection')

    return aps_buffered


def aggregate(intersected_buildings):
    """

    """
    df = intersected_buildings[['POSTCODE', 'rmdps']]

    df = df.groupby(['POSTCODE'], as_index=True).sum()

    return df


def plot_results(data, pcd_sector):
    """

    """
    import seaborn as sns; sns.set()
    import matplotlib.pyplot as plt

    data = data.loc[data['ap_density_km2'] > 0]

    title = 'Collected Versus Predicted WiFi APs: {}'.format(pcd_sector[3])

    plot = sns.regplot(x="waps_km2", y="rmdps_km2", data=data).set_title(title)

    plt.xlabel('Density of Collected WiFi APs (km^2)')
    plt.ylabel('Density of Postal Delivery Points (km^2)')
    fig = plot.get_figure()
    fig.savefig(os.path.join(results, pcd_sector[0], "plot.png"))
    plt.clf()

if __name__ == '__main__':

    pcd_sectors = [
        # ('N78', 'london', 'n', 'N78 - Urban'),
        ('W1G6', 'london', 'w', 'W1G6 - Dense Urban'),
        ('W1H2', 'london', 'w', 'W1H2 - Dense Urban'),
        ('CB41', 'cambridge', 'cb', 'CB41 - Suburban'),
    ]

    results = os.path.join(BASE_PATH, '..', 'results')
    if not os.path.exists(results):
        os.makedirs(results)

    path = os.path.join(BASE_PATH, 'shapes', 'PostalSector.shp')
    pcd_sector_shapes = gpd.read_file(path)
    pcd_sector_shapes.crs = 'epsg:27700'
    pcd_sector_shapes = pcd_sector_shapes.to_crs('epsg:27700')

    folder_kml = os.path.join(BASE_PATH, 'wigle', 'all_kml_data')
    files = os.listdir(folder_kml)

    for pcd_sector in pcd_sectors:

        print('Getting data')
        folder = os.path.join(BASE_PATH, '..', 'results', str(pcd_sector[0]))
        if not os.path.exists(folder):
            os.makedirs(folder)

        print('Getting boundary')
        path = os.path.join(folder, 'boundary.shp')
        if not os.path.exists(path):
            boundary = pcd_sector_shapes.loc[pcd_sector_shapes['StrSect'] == pcd_sector[0]]
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
            all_data = subset_points(folder_kml, files, boundary)
        else:
            all_data = gpd.read_file(collected_data, crs='epsg:27700')

        print('Subsetting codepoint')
        path = os.path.join(folder, 'codepoint_polys.shp')
        if not os.path.exists(path):
            codepoint_polys = subset_codepoint(pcd_sector, boundary)
            codepoint_polys.to_file(path, crs='epsg:27700')
        else:
            codepoint_polys = gpd.read_file(path, crs='epsg:27700')

        print('Intersecting grid with points')
        path = os.path.join(folder, 'grid_with_points.csv')
        if not os.path.exists(path):
            postcode_aps = intersect_grid_w_points(grid, all_data, codepoint_polys)
            postcode_aps.to_file( os.path.join(folder, 'postcode_aps.shp'), crs='epsg:27700')
            postcode_aps.to_csv(os.path.join(folder, 'postcode_aps.csv'), index=False)
        else:
            postcode_aps = pd.read_csv(path)

        print('Plot results')
        plot_results(postcode_aps, pcd_sector)

        print('Getting bounding box')
        bbox = boundary
        bbox.crs = 'epsg:27700'
        bbox = bbox.to_crs('epsg:4326')
        bbox = bbox['geometry'].bounds

        print('Getting OSM graph')
        #bbox needs to be North South East West
        G = ox.graph_from_bbox(
            bbox.maxy.values[0],
            bbox.miny.values[0],
            bbox.maxx.values[0],
            bbox.minx.values[0],
            network_type='drive')

        print('Converting to geopandas dataframe')
        graph = ox.graph_to_gdfs(G, nodes=False, edges=True)

        print('Getting geometries')
        graph = graph[['geometry']]

        print('Change crs to local projected coordinate system')
        graph.crs = 'epsg:4326'
        graph = graph.to_crs('epsg:27700')

        print('Getting roads within boundary')
        graph = graph[graph.intersects(boundary.unary_union)]

        print('Writing road network')
        filename = 'road_network.shp'
        graph.to_file(os.path.join(folder, filename), crs='epsg:27700')

        print('Subsetting buildings')
        path = os.path.join(folder, 'buildings.shp')
        if os.path.exists(path):
            buildings = gpd.read_file(path, crs='epsg:27700')
        else:
            buildings = subset_buildings(pcd_sector, boundary)
            buildings.to_file(path, crs='epsg:27700')

    print('Completed script')
