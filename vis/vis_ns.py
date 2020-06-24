"""
Visualize OA estimates using national statistics (ns).

Written by Ed Oughton.

June 2020

"""
import os
import csv
import configparser
import seaborn as sns; sns.set()
import matplotlib.pyplot as plt
import pandas as pd
import geopandas as gpd
import contextily as ctx

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), '..', 'scripts', 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

RESULTS = os.path.join(BASE_PATH, '..', 'results')

def load_results(path):
    """
    Load MSOA results.

    """
    data = pd.read_csv(path)

    data = data[['Area', 'hh_wifi_access', 'perc_hh_wifi_access']]

    data = data.rename({
        'Area': 'id',
        'hh_wifi_access': 'hh_wifi_access',
        'perc_hh_wifi_access': 'perc_hh_wifi_access',
        }, axis='columns')

    return data


def load_shapes(path):
    """
    Load MSOA and Scottish IZ output area shapes.

    """
    data = gpd.read_file(path)

    data = data[['lower_id', 'region', 'area_km2', 'geometry']]

    data = data.rename({
        'lower_id': 'id',
        'region': 'region',
        'area_km2': 'area_km2',
        'geometry': 'geometry'
        }, axis='columns')

    return data


def combine_data(data, outputs_areas):
    """
    Add data to outputs_areas.

    """
    data = pd.merge(data, outputs_areas,  how='left', left_on=['id'], right_on = ['id'])

    data['ap_density_km2'] = data['hh_wifi_access'] / data['area_km2']

    return data


def plot_results(data, x_axis, y_axis, plotname, x_label, y_label, title):
    """

    """
    plot = sns.jointplot(x=x_axis, y=y_axis, data=data, kind='hex')

    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plot.savefig(os.path.join(folder, "hex_{}.png".format(plotname)))
    plt.clf()


def histograms(data, folder):
    """

    """
    data = data[[
        'hh_wifi_access',
        'perc_hh_wifi_access',
        'ap_density_km2',
        'region'
    ]]

    max_value = data['ap_density_km2'].quantile(.975)
    min_value = data['ap_density_km2'].quantile(.025)
    increment = (max_value - min_value) / 10

    bins = list(range(int(min_value), int(max_value), int(increment)))
    # bins = [75, 75.5, 76, 76.5, 77, 77.5, 78, 78.5, 79]

    data['ap_density_km2_decile'] =  pd.cut(data['ap_density_km2'], bins)

    # plt.figure()
    # plot = sns.catplot(x="perc_hh_wifi_access_decile", y="perc_hh_wifi_access", data=data, kind="bar")
    # plot.set_xticklabels(rotation=45)
    # path = os.path.join(folder, "histograms_perc_wifi_access.png")
    # plot.savefig(path)
    # plt.clf()

    plt.figure()
    plot = sns.catplot(x="ap_density_km2_decile", y="perc_hh_wifi_access", data=data, kind="bar")
    plot.set_xticklabels(rotation=90)
    path = os.path.join(folder, "histograms_perc_wifi_access_vs_ap_density.png")
    plot.savefig(path)
    plt.clf()


if __name__ == '__main__':

    folder = os.path.join(BASE_PATH, '..', 'vis', 'figures')

    path = os.path.join(RESULTS, 'household_adoption.csv')
    data = load_results(path)#[:100]

    path = os.path.join(BASE_PATH, 'intermediate', 'output_areas.shp')
    outputs_areas = load_shapes(path)#[:1000]

    data = combine_data(data, outputs_areas)

    plot_results(data,
        "hh_wifi_access", "ap_density_km2",
        'wifi_access_vs_ap_density',
        'wifi aps', 'ap density (km2)',
        'WiFi APs vs Building Count (n={})'.format(len(data)))

    #plot histograms
    histograms(data, folder)
