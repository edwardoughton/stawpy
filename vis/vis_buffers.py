"""
This script goes into each postcode sector results folder and
imports any buffered data, ready to plot for all areas.

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


def define_geotypes(pcd_sector_geotypes):
    """

    """
    output = {}

    for idx, row in pcd_sector_geotypes.iterrows():

        pop_density_km2 = round(row['population'] / row['area_km2'])

        if pop_density_km2 > 7959:
            row['geotype'] = 'urban'
        # elif pop_density_km2 > 3119:
        #     row['geotype'] = 'suburban 1'
        elif pop_density_km2 > 782:
            row['geotype'] = 'suburban' #'suburban 2'
        # elif pop_density_km2 > 112:
        #     row['geotype'] = 'rural 1'
        # elif pop_density_km2 > 47:
        #     row['geotype'] = 'rural 2'
        # elif pop_density_km2 > 25:
        #     row['geotype'] = 'rural 3'
        # elif pop_density_km2 > 0:
        #     row['geotype'] = 'rural 4'
        else:
            row['geotype'] = 'rural' #'rural 5'

        output[row['id']] = {
            'lad': row['lad'],
            'population': row['population'],
            'area_km2': row['area_km2'],
            'pop_density_km2': pop_density_km2,
            'geotype': row['geotype'],
        }

    return output


def load_results(path):
    """

    """
    data = pd.read_csv(path)

    return data


def plot_results(data, x_axis, y_axis, plotname, x_label, y_label, title):
    """

    """
    plot = sns.jointplot(x=x_axis, y=y_axis, data=data, kind='hex')
    # plt.title(title)
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plot.savefig(os.path.join(folder, "hex_{}.png".format(plotname)))
    plt.clf()

    # plot = sns.regplot(x=x_axis, y=y_axis, data=data).set_title(title)
    # plt.xlabel(x_label)
    # plt.ylabel(y_label)
    # fig = plot.get_figure()
    # fig.savefig(os.path.join(folder, "reg_{}.png".format(plotname)))
    # plt.clf()


def pairwise(data, folder, filename):
    """

    """
    if not 'adjusted_floor_area' in data.columns:
        data['adjusted_floor_area'] = 0

    data = data[[
        'waps_collected',
        'waps_km2',
        'building_count',
        # 'building_count_km2',
        # 'res_count',
        # 'res_count_km2',
        # 'nonres_count',
        # 'nonres_count_km2',
        'floor_area',
        'adjusted_floor_area',
        # 'area_km2'
    ]]

    data = data.loc[data['waps_km2'] > 0]
    data = data.loc[data['building_count'] > 0]
    # data = data.loc[data['building_count_km2'] > 0]
    data = data.loc[data['floor_area'] > 0]
    data = data.loc[data['adjusted_floor_area'] > 0]

    data.columns = [
        'Wigle APs',
        'Wigle APs (km^2)',
        'Building Count',
        # 'Building Density (km^2)',
        # 'Resident Count',
        # 'Resident Density (HHs per km^2)',
        # 'Non Residential Count',
        # 'Non Residential Density (km^2)',
        'Total Floor Area (km^2)',
        'Total Floor Area Adjusted (km^2)',
        # 'Area (km^2)'
    ]

    plt.figure()
    pairplot = sns.pairplot(data, kind = "scatter", palette = 'husl')
    path = os.path.join(folder, "scatter_buffered_{}.png".format(filename))
    pairplot.savefig(path)
    plt.clf()

    plt.figure()
    pairplot = sns.pairplot(data, kind = "reg", palette = 'husl')
    path = os.path.join(folder, "reg_buffered_{}.png".format(filename))
    pairplot.savefig(path)
    plt.clf()



def histograms(data, folder, side_length):
    """

    """
    data = data[[
        'waps_collected',
        # 'waps_km2',
        'building_count',
        # 'building_count_km2',
        # 'res_count',
        # 'res_count_km2',
        # 'nonres_count',
        # 'nonres_count_km2',
        'floor_area',
        # 'adjusted_floor_area',
        # 'area_km2'
        'geotype',
    ]]
    max_value = max(data['building_count'])
    bins = list(range(0, int(max_value), int(max_value/10)))
    data['building_count_decile'] =  pd.cut(data['building_count'], bins)

    plt.figure()
    plot = sns.catplot(x="building_count_decile", y="waps_collected", col="geotype", data=data, kind="bar")
    plot.set_xticklabels(rotation=45)
    path = os.path.join(folder, "histograms_building_count_buffered_geotype_{}.png".format(side_length))
    plot.savefig(path)
    plt.clf()

    plt.figure()
    plot = sns.catplot(x="building_count", y="waps_collected", data=data, kind="bar")
    plot.set_xticklabels(rotation=90)
    path = os.path.join(folder, "histograms_building_count_buffered_{}.png".format(side_length))
    plot.savefig(path)
    plt.clf()

    max_value = max(data['floor_area'])
    bins = list(range(0, int(max_value), int(max_value/10)))
    data['floor_area'] =  pd.cut(data['floor_area'], bins)

    # data.columns = [
    #     'Wigle APs',
    #     # 'Wigle APs (km^2)',
    #     'Building Count',
    #     # 'Building Density (km^2)',
    #     # 'Resident Count',
    #     # 'Resident Density (HHs per km^2)',
    #     # 'Non Residential Count',
    #     # 'Non Residential Density (km^2)',
    #     # 'Total Floor Area (km^2)',
    #     # 'Total Floor Area Adjusted (km^2)',
    #     # 'Area (km^2)'
    # ]

    plt.figure()
    plot = sns.catplot(x="floor_area", y="waps_collected", col="geotype", data=data, kind="bar")
    plot.set_xticklabels(rotation=45)
    path = os.path.join(folder, "histograms_floor_area_buffered_{}.png".format(side_length))
    plot.savefig(path)
    plt.clf()


if __name__ == '__main__':

    #Create output folder
    folder = os.path.join(BASE_PATH, '..', 'vis', 'figures')
    if not os.path.exists(folder):
        os.makedirs(folder)

    path = os.path.join(BASE_PATH, 'intermediate', 'pcd_list.csv')
    pcd_sectors = pd.read_csv(path)
    pcd_sectors = pcd_sectors['StrSect'].unique()

    filename = 'pcd_sector_geotypes.csv'
    path = os.path.join(BASE_PATH, 'pcd_sector_geotypes', filename)
    pcd_sector_geotypes = pd.read_csv(path)
    all_pcd_sector_data = define_geotypes(pcd_sector_geotypes)

    all_data = []

    side_lengths = [100, 300]

    for side_length in side_lengths:

        for pcd_sector in pcd_sectors:

            # if not pcd_sector == 'CB11':
            #     continue

            directory = os.path.join(RESULTS_PATH, pcd_sector)
            filename = 'postcode_aps_buffered_{}.csv'.format(side_length)
            path = os.path.join(directory, filename)

            if pcd_sector in [p for p in all_pcd_sector_data.keys()]:
                pcd_sector_data = all_pcd_sector_data[pcd_sector]
            else:
                continue

            # if not geotype == 'urban':
            #     continue
            # if not pcd_sector_data['lad'] == 'E07000008':
            #     continue

            print('-- Getting data for {}'.format(pcd_sector))

            if os.path.exists(path):

                data = pd.read_csv(path)

                geotype =  pcd_sector_data['geotype']
                data['geotype'] = geotype

                data = data.to_dict('records')

                all_data = all_data + data
            else:
                pass

        postcode_aps = pd.DataFrame(all_data)

        postcode_aps.to_csv(os.path.join(RESULTS_PATH, 'all_buffered_points_{}m.csv'.format(side_length)))

        sample_size = len(postcode_aps)

        plot_results(postcode_aps, "waps_collected", "building_count",
            'waps_vs_building_count_{}'.format(side_length), 'Wigle APs',
            'Building count', 'WiFi APs vs Building Count (n={})'.format(sample_size))
        plot_results(postcode_aps, "waps_km2", "building_count",
            'aps_vs_building_count_{}'.format(side_length), 'Wigle APs per km^2',
            'Building count', 'WiFi APs vs Building Count (n={})'.format(sample_size))
        # plot_results(postcode_aps, "waps_km2", "res_count",
        #     'aps_km2_vs_res_count_{}'.format(side_length), 'Wigle APs per km^2', 'Residential count')
        # plot_results(postcode_aps, "waps_km2", "floor_area",
        #     'aps_km2_vs_floor_area_{}'.format(side_length), 'Wigle APs per km^2', 'Floor area (km^2)')
        # plot_results(postcode_aps, "waps_km2", "building_count_km2",
        #     'aps_vs_building_count_km2_{}'.format(side_length), 'Wigle APs per km^2', 'Building count (km^2)')
        # plot_results(postcode_aps, "waps_km2", "res_count_km2",
        #     'aps_km2_vs_res_count_km2_{}'.format(side_length), 'Wigle APs per km^2', 'Residential count (km^2)')
        # plot_results(postcode_aps, "waps_km2", "floor_area_km2",
        #     'aps_km2_vs_floor_area_km2_{}'.format(side_length), 'Wigle APs per km^2', 'Floor area (km^2)')

        #Plot correlations
        pairwise(postcode_aps, folder, 'pairwise_buffered_{}'.format(side_length))

        #plot histograms
        histograms(postcode_aps, folder, side_length)
