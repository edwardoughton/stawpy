"""
This script goes into each postcode sector results folder and
imports any data, ready to plot for all areas.

Written by Ed Oughton

June 2020

"""
import os
import sys
import configparser
import csv
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import seaborn as sns

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), '..', 'scripts', 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']
RESULTS_PATH = CONFIG['file_locations']['results']


def load_results(path):
    """

    """
    data = pd.read_csv(path)

    return data


def plot_results(data, x_axis, y_axis, plotname, x_label, y_label):
    """

    """
    plot = sns.jointplot(x=x_axis, y=y_axis, data=data, kind='hex')
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plot.savefig(os.path.join(folder, "hex_{}.png".format(plotname)))
    plt.clf()

    plot = sns.regplot(x=x_axis, y=y_axis, data=data).set_title(plotname)
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    fig = plot.get_figure()
    fig.savefig(os.path.join(folder, "reg_{}.png".format(plotname)))
    plt.clf()


def pairwise(data, folder, filename):
    """

    """
    data = data[[
        'waps_km2',
        'building_count',
        'building_count_km2',
        # 'res_count',
        # 'res_count_km2',
        # 'nonres_count',
        # 'nonres_count_km2',
        'floor_area',
        'floor_area_km2',
        # 'area_km2'
    ]]
    # print(len(data))
    data = data.loc[data['waps_km2'] > 0]
    data = data.loc[data['building_count'] > 0]
    data = data.loc[data['building_count_km2'] > 0]
    data = data.loc[data['floor_area'] > 0]
    data = data.loc[data['floor_area_km2'] > 0]
    # print(len(data))
    data.columns = [
        'Wigle APs (km^2)',
        'Building Count',
        'Building Density (km^2)',
        # 'Resident Count',
        # 'Resident Density (HHs per km^2)',
        # 'Non Residential Count',
        # 'Non Residential Density (km^2)',
        'Total Floor Area (km^2)',
        'Total Floor Area Density (km^2)',
        # 'Area (km^2)'
    ]

    plt.figure()
    pairplot = sns.pairplot(data, kind = "scatter", palette = 'husl')

    path = os.path.join(folder, filename)
    pairplot.savefig(path)


if __name__ == '__main__':

    #Create output folder
    folder = os.path.join(BASE_PATH, '..', 'vis', 'figures')
    if not os.path.exists(folder):
        os.makedirs(folder)

    path = os.path.join(BASE_PATH, 'intermediate', 'pcd_list.csv')
    pcd_sectors = pd.read_csv(path)
    pcd_sectors = pcd_sectors['StrSect'].unique()

    all_data = []

    side_lengths = [50, 100, 200, 300]

    for side_length in side_lengths:

        for pcd_sector in pcd_sectors:

            print('-- Getting data for {}'.format(pcd_sector))

            directory = os.path.join(RESULTS_PATH, pcd_sector)
            filename = 'postcode_aps_{}.csv'.format(side_length)
            path = os.path.join(directory, filename)

            if os.path.exists(path):

                data = pd.read_csv(path)

                data = data.to_dict('records')

                all_data = all_data + data
            else:
                pass

        postcode_aps = pd.DataFrame(all_data)

        plot_results(postcode_aps, "waps_km2", "building_count",
            'aps_vs_building_count_{}'.format(side_length), 'Wigle APs per km^2', 'Building count')
        plot_results(postcode_aps, "waps_km2", "res_count",
            'aps_km2_vs_res_count_{}'.format(side_length), 'Wigle APs per km^2', 'Residential count')
        plot_results(postcode_aps, "waps_km2", "floor_area",
            'aps_km2_vs_floor_area_{}'.format(side_length), 'Wigle APs per km^2', 'Floor area (km^2)')
        plot_results(postcode_aps, "waps_km2", "building_count_km2",
            'aps_vs_building_count_km2_{}'.format(side_length), 'Wigle APs per km^2', 'Building count (km^2)')
        plot_results(postcode_aps, "waps_km2", "res_count_km2",
            'aps_km2_vs_res_count_km2_{}'.format(side_length), 'Wigle APs per km^2', 'Residential count (km^2)')
        plot_results(postcode_aps, "waps_km2", "floor_area_km2",
            'aps_km2_vs_floor_area_km2_{}'.format(side_length), 'Wigle APs per km^2', 'Floor area (km^2)')

        #Plot correlations
        pairwise(postcode_aps, folder, 'pairwise_{}'.format(side_length))
