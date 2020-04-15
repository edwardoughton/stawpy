"""
Calculate AP density by postcode.

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
import numpy as np
import seaborn as sns; sns.set()
import matplotlib.pyplot as plt

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']


def load_data(path):
    """

    """
    output = {}

    data = pd.read_csv(path)

    for idx, item in data.iterrows():
        key = item['postcode_sector'].replace(' ', '')
        output[key] = int(item['domestic_delivery_points'])

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


def plot_results(data):
    """

    """


    data = data.loc[data['ap_density_km2'] > 0]

    plot = sns.scatterplot(x="delivery_point_density_km2", y="ap_density_km2", data=data)
    plot.set(xlabel='Delivery Point Density (km^2)', ylabel='WiFi Access Point Density (km^2)')
    plt.title('Relationship Between Delivery Point Density and AP density')

    fig = plot.get_figure()
    fig.savefig(os.path.join(BASE_PATH, '..', 'vis', 'figures', 'ap_density_vs_delivery_point_density.png'))



    # plot = sns.scatterplot(x="delivery_point_density_km2", y="ap_density_km2", data=data)
    # plot.set(xlabel='Delivery Point Density (km^2)', ylabel='WiFi Access Point Density (km^2)')
    # plt.title('Relationship Between Delivery Point Density and AP density')

    # fig = plot.get_figure()
    # fig.savefig(os.path.join(BASE_PATH, '..', 'vis', 'figures', 'ap_density_vs_delivery_point_density.png'))




if __name__ == '__main__':

    results = os.path.join(BASE_PATH, '..', 'results')
    if not os.path.exists(results):
        os.makedirs(results)

    path = os.path.join(BASE_PATH, 'codepoint', 'domestic_delivery_points.csv')
    codepoint = load_data(path)

    path = os.path.join(BASE_PATH, 'shapes', 'PostalSector.shp')
    pcd_sector_shapes = gpd.read_file(path)
    pcd_sector_shapes.crs = 'epsg:27700'
    pcd_sector_shapes = pcd_sector_shapes.to_crs('epsg:27700')

    folders = os.listdir(os.path.join(BASE_PATH, 'wigle', 'postcode_sectors'))
    files = []
    for pcd_sector in folders:

        data = os.listdir(os.path.join(BASE_PATH, 'wigle', 'postcode_sectors', pcd_sector))
        for data_file in data:
            files.append(
                os.path.join(BASE_PATH, 'wigle', 'postcode_sectors', pcd_sector, data_file)#[:-4])
            )

    data_to_plot = []

    for pcd_sector_path in files:

        pcd_sector = pcd_sector_path.split('\\')[3]

        print('Getting boundary')
        boundary = pcd_sector_shapes.loc[pcd_sector_shapes['StrSect'] == pcd_sector]

        all_data = pd.read_csv(pcd_sector_path)
        all_data = gpd.GeoDataFrame(all_data, geometry=gpd.points_from_xy(all_data.trilong, all_data.trilat))
        all_data.crs = 'epsg:4326'
        all_data = all_data.to_crs('epsg:27700')

        print('AP count is {}'.format(len(all_data)))
        print('Boundary is {} km^2'.format(round(boundary['geometry'].area.values[0] / 1e6, 2)))
        print('AP density is {} km^2'.format(round(len(all_data) / (boundary['geometry'].area.values[0] / 1e6), 2)))
        delivery_points = codepoint[pcd_sector]
        print('Total Royal Mail delivery points {}'.format(delivery_points))
        delivery_point_density_km2 = (delivery_points / (boundary['geometry'].area.values[0] / 1e6))

        f = lambda x:np.sum(all_data.intersects(x))
        count = boundary['geometry'].apply(f)

        data_to_plot.append({
            'aps': count.values[0],
            'area_km2': round(boundary['geometry'].area.values[0] / 1e6, 2),
            'ap_density_km2': round(len(all_data) / (boundary['geometry'].area.values[0] / 1e6), 2),
            'delivery_points': delivery_points,
            'delivery_point_density_km2': delivery_point_density_km2,
        })

    data_to_plot = pd.DataFrame(data_to_plot)

    print('Plot results')
    plot_results(data_to_plot)

    print('Writing AP density results')
    filename = 'density_results.csv'
    data_to_plot.to_csv(os.path.join(BASE_PATH, '..', 'results', filename), index=False)

    print('Completed script')
