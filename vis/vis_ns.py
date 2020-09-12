"""
Visualize MSOA estimates using national statistics (ns).

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

    return data


def process_msoa_shapes(results):
    """
    Load in the output area shapes, merge with the MSOA lookup table.

    """
    path_shapes = os.path.join(BASE_PATH, 'intermediate', 'output_areas.shp')
    oa_shapes = gpd.read_file(path_shapes, crs='epsg:27700')
    oa_shapes.set_index('msoa')
    oa_shapes = oa_shapes[['msoa', 'geometry']]

    results.set_index('msoa')

    output = (pd.merge(oa_shapes, results, on='msoa'))

    return output


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


def pairwise(data, folder):
    """

    Column titles include:
        'msoa', 'area_km2', 'population', 'population_km2', 'urban_rural',
        'households', 'households_km2', 'hh_fixed_access', 'hh_wifi_access',
        'hh_fixed_access_km2', 'hh_wifi_access_km2', 'perc_hh_fixed_access',
        'perc_hh_wifi_access', 'region', 'lad_id', 'businesses',
        'business_density_km2', 'ba_micro', 'ba_small', 'ba_medium', 'ba_large',
        'ba_very_large', 'bafa_micro', 'bafa_small', 'bafa_medium',
        'bafa_large', 'bafa_very_large', 'bafa_total', 'baps_micro',
        'baps_small', 'baps_medium', 'baps_large', 'baps_very_large',
        'baps_total', 'baps_density_km2', 'total_ap_density_km2

    """
    data = data[[
        'area_km2',
        'population_km2',
        'households_km2',
        'business_density_km2',
        'hh_wifi_access_km2',
        'baps_density_km2',
        'total_ap_density_km2'
    ]]

    plt.figure()
    pairplot = sns.pairplot(data, kind = "scatter", palette = 'husl')
    path = os.path.join(folder, "scatter_buffered.png")
    pairplot.savefig(path)
    plt.clf()

    plt.figure()
    pairplot = sns.pairplot(data, kind = "reg", palette = 'husl')
    path = os.path.join(folder, "reg_buffered.png")
    pairplot.savefig(path)
    plt.clf()


def histograms(data, folder):
    """
    'msoa', 'area_km2', 'population', 'population_km2', 'urban_rural',
    'households', 'households_km2', 'hh_fixed_access', 'hh_wifi_access',
    'hh_fixed_access_km2', 'hh_wifi_access_km2', 'perc_hh_fixed_access',
    'perc_hh_wifi_access', 'region', 'lad_id', 'ba_micro', 'ba_small',
    'ba_medium', 'ba_large', 'ba_very_large', 'ba_total', 'bafa_micro',
    'bafa_small', 'bafa_medium', 'bafa_large', 'bafa_very_large',
    'bafa_total', 'baps_micro', 'baps_small', 'baps_medium', 'baps_large',
    'baps_very_large', 'baps_total', 'baps_density_km2', 'total_ap_density_km2

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

    data = data[[
        'area_km2',
        'population_km2',
        'households_km2',
        'business_density_km2',
        'hh_wifi_access_km2',
        'baps_density_km2',
        'total_ap_density_km2'
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

    folder = os.path.join(BASE_PATH, '..', 'vis', 'figures')

    print('Read area results')
    path = os.path.join(RESULTS, 'estimated_adoption_ns.csv')
    data = load_results(path)#[:100]

    # print('Add data to area shapes')
    # shapes = process_msoa_shapes(data)
    # path = os.path.join(BASE_PATH, '..', 'results', 'oa_shapes_with_data.shp')
    # shapes.to_file(path, crs='epsg:27700')

    print('Getting FB data')
    path = os.path.join(BASE_PATH, 'fb', 'fb_aps_no_geo.csv')
    data_fb = pd.read_csv(path)#[:1]
    data = pd.merge(data, data_fb, left_on='msoa', right_on='area_code')

    # #plot histograms
    # histograms(data, folder)

    #plot pairwise
    # pairwise(data, folder)



    # sns.scatterplot(x="area_km2", y="population_km2", data=data)
    # plt.show()



    # # plot_results(data,
    # #     "area_km2", "population_km2",
    # #     'area_vs_pop_density',
    # #     'area (km2)', 'pop density (km2)',
    # #     'Area vs Population Density (n={})'.format(len(data)))

    # # plot_results(data,
    # #     "hh_wifi_access", "ap_density",
    # #     'wifi_access_vs_ap_density',
    # #     'wifi aps', 'ap density (km2)',
    # #     'WiFi APs vs Building Count (n={})'.format(len(data)))
