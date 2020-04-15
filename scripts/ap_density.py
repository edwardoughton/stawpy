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
import glob
import osmnx as ox

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']


def subset_points(files, boundary):
    """

    """
    all_data = []

    for filename in files:

        if not filename.endswith('.kml'):
            continue

        print('Loading {}'.format(filename))
        path = os.path.join(BASE_PATH, 'wigle', '2020_4_7', filename)

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


def calculate_density(graph, all_data, delivery_point_density_km2):
    """

    """
    output = []

    seen = set()

    for idx, poly in graph.iterrows():

        geom = poly['geometry'].buffer(10)

        intersecting = all_data[all_data.intersects(geom)]

        count = []

        for idx, row in intersecting.iterrows():

            row['coords'] = (row['trilong'], row['trilat'])

            if row['coords'] in seen:
                continue
            else:
                count.append(row['coords'])

            seen.add(row['coords'])

        geom = poly['geometry'].buffer(100)

        output.append({
            'count': len(count),
            'area_km2': geom.area / 1e6,
            'ap_density_km2': len(count) / (geom.area / 1e6),
            'delivery_point_density_km2': delivery_point_density_km2 * (geom.area / 1e6),
        })

    output = pd.DataFrame(output)

    return output


def plot_results(data, pcd_sector):
    """

    """
    import seaborn as sns; sns.set()
    import matplotlib.pyplot as plt

    data = data.loc[data['ap_density_km2'] > 0]

    plot = sns.scatterplot(x="delivery_point_density_km2", y="ap_density_km2", data=data)

    fig = plot.get_figure()
    fig.savefig(os.path.join(results, pcd_sector, "plot.png"))


if __name__ == '__main__':

    pcd_sectors = [
        'EC1M3',
        'EC1N2',
        'EC1N6',
        'EC1N7',
        'EC1N8',
        'EC1R5',
        'EC4A1',
        'EC4A2',
        'EC4A3',
        'EC4Y0',
        'EC4Y1',
        'EC4Y7',
        'EC4Y8',
        'EC4Y9',
        'N1C4',
        'NW15',
        # 'N78'
    ]

    results = os.path.join(BASE_PATH, '..', 'results')
    if not os.path.exists(results):
        os.makedirs(results)

    path = os.path.join(BASE_PATH, 'shapes', 'PostalSector.shp')
    pcd_sector_shapes = gpd.read_file(path)
    pcd_sector_shapes.crs = 'epsg:27700'
    pcd_sector_shapes = pcd_sector_shapes.to_crs('epsg:27700')

    # files = os.listdir(os.path.join(BASE_PATH, 'wigle', '2020_4_7'))

    for pcd_sector in pcd_sectors:

        print('Getting data')
        folder = os.path.join(BASE_PATH, '..', 'results', str(pcd_sector))
        if not os.path.exists(folder):
            os.makedirs(folder)

        print('Getting boundary')
        boundary = pcd_sector_shapes.loc[pcd_sector_shapes['StrSect'] == pcd_sector]
        boundary.to_file(os.path.join(folder, 'boundary.shp'), crs='epsg:27700')

        # # collected_data = os.path.join(folder, 'collected_points.shp')
        # # if not os.path.exists(collected_data):
        # #     all_data = subset_points(files, boundary)
        # # else:
        # #     all_data = gpd.read_file(collected_data)

        # collected_data = os.path.join(folder, 'collected_points.shp')
        # if not os.path.exists(collected_data):
        path = os.path.join(BASE_PATH, 'wigle', 'postcode_sectors', pcd_sector, 'data_547486008')
        all_files = os.listdir(os.path.join(BASE_PATH, 'wigle', 'postcode_sectors', pcd_sector))
        files = []
        for file_name in all_files:
            files.append(
                os.path.join(BASE_PATH, 'wigle', 'postcode_sectors', pcd_sector, file_name)
            )
        all_data = pd.concat((pd.read_csv(f) for f in files))
        all_data = gpd.GeoDataFrame(all_data, geometry=gpd.points_from_xy(all_data.trilong, all_data.trilat))
        all_data.crs = 'epsg:4326'
        all_data = all_data.to_crs('epsg:27700')
        all_data.to_file(os.path.join(folder, 'collected_points.shp'), crs='epsg:27700')
        # else:
        #     all_data = gpd.read_file(collected_data)


        print('AP count is {}'.format(len(all_data)))
        print('Boundary is {} km^2'.format(round(boundary['geometry'].area.values[0] / 1e6, 2)))
        print('AP density is {} km^2'.format(round(len(all_data) / (boundary['geometry'].area.values[0] / 1e6), 2)))
        print('Total Royal Mail delivery points {}'.format(5121))
        delivery_point_density_km2 = (5121 / (boundary['geometry'].area.values[0] / 1e6))

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

        print('Getting AP density')
        density_results = calculate_density(graph, all_data, delivery_point_density_km2)

        print('Plot results')
        plot_results(density_results, pcd_sector)

        print('Writing AP density results')
        filename = 'density_results.csv'
        density_results.to_csv(os.path.join(folder, filename), index=False)

        print('Writing road network')
        filename = 'buffered_road_network.shp'
        graph['geometry'] = graph['geometry'].buffer(10)
        graph.to_file(os.path.join(folder, filename), crs='epsg:27700')

        print('Completed {}'.format(pcd_sector))

    print('Completed script')
