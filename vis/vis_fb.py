"""
Visualize MSOA estimates using self-collected (sc) data.

Written by Ed Oughton

June 2020

"""
import os
import sys
import configparser
import csv
import numpy as np
from scipy import stats
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import seaborn as sns

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), '..', 'scripts', 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']
RESULTS_PATH = CONFIG['file_locations']['results']


def define_geotypes(oa_geotypes):
    """

    """
    output = {}

    for idx, row in oa_geotypes.iterrows():

        output[row['msoa']] = {
            'lad': row['lad'],
            'region': row['region'],
            'population': row['population'],
            'area_km2': row['area_km2'],
            'pop_density_km2': row['pop_density_km2'],
            'geotype': row['geotype'],
            'households': row['households'],
            'prems_residential': row['prems_residential'],
            'prems_residential_floor_area': row['prems_residential_floor_area'],
            'prems_residential_footprint_area': row['prems_residential_footprint_area'],
            'prems_non_residential': row['prems_non_residential'],
            'prems_non_residential_floor_area': row['prems_non_residential_floor_area'],
            'prems_non_residential_footprint_area': row['prems_non_residential_footprint_area'],

        }

    return output


def merge_data(data, oa_geotypes):
    """
    """
    output = []

    for item in data:
        msoa = item['area_code']

        if not msoa in oa_geotypes.keys():
            continue

        lut = oa_geotypes[msoa]

        output.append({
            'msoa': msoa,
            'lad': lut['lad'],
            'region': lut['region'],
            'population': lut['population'],
            'area_km2': lut['area_km2'],
            'pop_density_km2': lut['pop_density_km2'],
            'geotype': lut['geotype'],
            'households': lut['households'],
            'prems_residential': lut['prems_residential'],
            'prems_residential_floor_area': lut['prems_residential_floor_area'],
            'prems_residential_footprint_area': lut['prems_residential_footprint_area'],
            'prems_non_residential': lut['prems_non_residential'],
            'prems_non_residential_floor_area': lut['prems_non_residential_floor_area'],
            'prems_non_residential_footprint_area': lut['prems_non_residential_footprint_area'],
            'total_prems': (
                lut['prems_residential'] +
                lut['prems_non_residential']
            ),
            'total_floor_area': (
                lut['prems_residential_floor_area'] +
                lut['prems_non_residential_floor_area']
            ),
            'total_footprint_area': (
                lut['prems_residential_footprint_area'] +
                lut['prems_non_residential_footprint_area']
            ),
            'total_prems_density_km2': (
                lut['prems_residential'] +
                lut['prems_non_residential']
            ) / lut['area_km2'],
            'number_of_aps': item['number_of_APs'],
            'number_of_aps_density_km2': item['number_of_APs'] / lut['area_km2'],
        })

    return output


def load_results(path):
    """

    """
    data = pd.read_csv(path)

    return data


def plot_results(data, x_axis, y_axis, max_x, max_y, plotname, x_label, y_label, title):
    """

    """
    data = data.loc[data[x_axis] < max_x]
    data = data.loc[data[y_axis] < max_y]

    data = pd.DataFrame({
        x_label: data[x_axis],
        y_label: data[y_axis],
    })

    plot = sns.jointplot(x=x_label, y=y_label, data=data, kind='hex')
    sns.regplot(x=x_label, y=y_label, data=data, ax=plot.ax_joint, scatter=False)

    pearsonr = round(stats.pearsonr(data[x_label], data[y_label])[0],2)
    title = title + ' (Coef: {})'.format(pearsonr)
    plt.subplots_adjust(top=0.9)
    plt.suptitle(title)
    plot.savefig(os.path.join(folder, "hex_{}.png".format(plotname)))
    plt.clf()


def pairwise(data, folder, filename):
    """

    """
    data = data[[
        # 'population',
        # 'pop_density_km2',
        # 'prems_residential',
        # 'prems_non_residential',
        'total_prems',
        'total_prems_density_km2',
        'number_of_aps',
        'number_of_aps_density_km2',
    ]]

    # data = data.loc[data['population'] > 0]
    # data = data.loc[data['pop_density_km2'] > 0]
    # data = data.loc[data['prems_residential'] > 0]
    # data = data.loc[data['prems_non_residential'] > 0]
    data = data.loc[data['total_prems'] > 0]
    data = data.loc[data['total_prems_density_km2'] > 0]
    data = data.loc[data['number_of_aps'] > 0]
    data = data.loc[data['number_of_aps_density_km2'] > 0]

    data.columns = [
        # 'population',
        # 'pop_density_km2',
        # 'prems_residential',
        # 'prems_non_residential',
        'Premises',
        'Premises Density (km^2)',
        'Wi-Fi APs',
        'Wi-FI AP Density (km^2)',
    ]

    # plt.figure()
    # pairplot = sns.pairplot(data, kind = "scatter", palette = 'husl')
    # path = os.path.join(folder, "scatter_buffered_{}.png".format(filename))
    # pairplot.fig.suptitle("Premises Vs Wi-Fi Scatter Plots", y=1.025)
    # pairplot.savefig(path)
    # plt.clf()

    plt.figure()
    pairplot = sns.pairplot(data, kind = "reg", palette = 'husl')
    path = os.path.join(folder, "reg_buffered_{}.png".format(filename))
    pairplot.fig.suptitle("Premises Vs Wi-Fi Linear Regression Plots", y=1.025)
    pairplot.savefig(path)
    plt.clf()


def histograms(data, folder):
    """

    """
    data = data[[
            'msoa',
            # 'lad',
            # 'region',
            # 'population',
            # 'area_km2',
            # 'pop_density_km2',
            'geotype',
            # 'households',
            # 'prems_residential',
            # 'prems_residential_floor_area',
            # 'prems_residential_footprint_area',
            # 'prems_non_residential',
            # 'prems_non_residential_floor_area',
            # 'prems_non_residential_footprint_area',
            'total_prems',
            # 'total_floor_area',
            # 'total_footprint_area',
            'total_prems_density_km2',
            'number_of_aps',
            'number_of_aps_density_km2',
    ]]

    data.loc[data['geotype'] == 'urban', 'geotype'] = 'Urban'
    data.loc[data['geotype'] == 'suburban', 'geotype'] = 'Suburban'
    data.loc[data['geotype'] == 'rural', 'geotype'] = 'Rural'

    max_value = max(data['total_prems'])
    bins = list(range(0, int(max_value), int(max_value/10)))
    bins = [round(x/1e3,1) for x in bins]
    data['total_prems_decile'] =  pd.cut(data['total_prems'] / 1e3, bins)

    max_value = max(data['total_prems_density_km2'])
    bins = list(range(0, int(max_value), int(max_value/10)))
    bins = [round(x/1e3,1) for x in bins]
    data['total_prems_density_km2_decile'] =  pd.cut(data['total_prems_density_km2'] / 1e3, bins)

    data1 = data[[
        'geotype',
        'total_prems_density_km2_decile',
        'number_of_aps',
    ]]

    data1.rename(
        columns = {
            'geotype': 'Geotype',
            'total_prems_density_km2_decile': 'Premises Density by Decile (1000s per km^2)',
            'number_of_aps': 'Value',
            }, inplace = True)
    data1['Metric'] = 'Total Wi-Fi APs'

    data2 = data[[
        'geotype',
        'total_prems_density_km2_decile',
        'number_of_aps_density_km2',
    ]]

    data2.rename(
        columns = {
            'geotype': 'Geotype',
            'total_prems_density_km2_decile': 'Premises Density by Decile (1000s per km^2)',
            'number_of_aps_density_km2': 'Value',
            }, inplace = True)
    data2['Metric'] = 'AP Density (km^2)'

    data = data1.append(data2)
    data['Source'] = 'FB'

    catplot = sns.catplot(x="Premises Density by Decile (1000s per km^2)", y="Value",
        hue="Source", col="Geotype", col_order=['Urban', 'Suburban', 'Rural'],
        row="Metric", capsize=.2, palette="YlGnBu_d", height=6, aspect=.75,
        sharey=False, sharex=False,
        kind="point", data=data)
    catplot.set_xticklabels(rotation=45)
    plt.tight_layout()

    #export
    path = os.path.join(folder, "hist_catplot.png")
    catplot.savefig(path)




    # plt.figure()
    # plot = sns.catplot(x="Premises by Decile", y="Total Wi-Fi APs", col="Geotype",
    #     data=data, kind="bar", col_order=['Urban', 'Suburban', 'Rural'])
    # plot.set_xticklabels(rotation=45)
    # plt.subplots_adjust(top=0.85)
    # plt.suptitle('Premises Count versus Wi-Fi AP Count')
    # path = os.path.join(folder, "histograms_total_prems_vs_total_APs_by_geotype_FB.png")
    # plot.savefig(path)
    # plt.clf()

    # plt.figure()
    # plot = sns.catplot(x="Premises by Decile", y="AP Density (km^2)", col="Geotype",
    #     data=data, kind="bar", col_order=['Urban', 'Suburban', 'Rural'])
    # plot.set_xticklabels(rotation=45)
    # plt.subplots_adjust(top=0.85)
    # plt.suptitle('Premises Count versus Wi-Fi AP Density')
    # path = os.path.join(folder, "histograms_total_prems_vs_AP_density_by_geotype_FB.png")
    # plot.savefig(path)
    # plt.clf()

    # plt.figure()
    # plot = sns.catplot(x="Premises Density by Decile (km^2)", y="AP Density (km^2)",
    #     col="Geotype", data=data, kind="bar", col_order=['Urban', 'Suburban', 'Rural'])
    # plot.set_xticklabels(rotation=45)
    # plt.subplots_adjust(top=0.85)
    # plt.suptitle('Premises Density versus Wi-Fi AP Density')
    # path = os.path.join(folder, "histograms_prem_density_vs_AP_density_by_geotype_FB.png")
    # plot.savefig(path)
    # plt.clf()




if __name__ == '__main__':

    #Create output folder
    folder = os.path.join(BASE_PATH, '..', 'vis', 'figures')
    if not os.path.exists(folder):
        os.makedirs(folder)

    filename = 'oa_lookup.csv'
    path = os.path.join(BASE_PATH, 'intermediate', filename)
    oa_geotypes = pd.read_csv(path)#[:20]
    oa_geotypes = define_geotypes(oa_geotypes)

    path = os.path.join(BASE_PATH, 'fb', 'fb_aps_no_geo.csv')
    data = pd.read_csv(path)#[:1]
    data = data.to_dict('records')
    data = merge_data(data, oa_geotypes)
    data = pd.DataFrame(data)

    ## plot all variables
    # pairwise(data, folder, 'FB')

    # plot_results(data, "number_of_aps", "total_prems", 5000, 12500,
    #     'number_of_aps_vs_total_premises', 'WiFi APs',
    #     'Total Premises', 'Wi-Fi APs vs Total Premises (n={})'.format(len(data)))
    # plot_results(data, "number_of_aps_density_km2", "total_prems_density_km2", 1000, 1000,
    #     'ap_density_vs_premises_density', 'Wi-Fi AP Density (km^2)',
    #     'Premises Density (km^2)', 'Wi-Fi AP Density vs Premises Density (n={})'.format(len(data)))

    #plot histograms
    histograms(data, folder)


    # data = pd.DataFrame(
    #     columns=["Prem Decile", "Value", "Metric", "Geotype"],
    #     data=[
    #             [1, 100, "AP Count", 'Urban'],
    #             [2, 200, "AP Count", 'Urban'],
    #             [3, 300, "AP Count", 'Urban'],
    #             [4, 400, "AP Count", 'Urban'],
    #             [5, 500, "AP Count", 'Urban'],
    #             [1, 200, "AP Count", 'Urban'],
    #             [2, 300, "AP Count", 'Urban'],
    #             [3, 400, "AP Count", 'Urban'],
    #             [4, 500, "AP Count", 'Urban'],
    #             [5, 600, "AP Count", 'Urban'],
    #             [1, 100, "AP Count", 'Suburban'],
    #             [2, 200, "AP Count", 'Suburban'],
    #             [3, 300, "AP Count", 'Suburban'],
    #             [4, 400, "AP Count", 'Suburban'],
    #             [5, 500, "AP Count", 'Suburban'],
    #             [1, 200, "AP Count", 'Suburban'],
    #             [2, 300, "AP Count", 'Suburban'],
    #             [3, 400, "AP Count", 'Suburban'],
    #             [4, 500, "AP Count", 'Suburban'],
    #             [5, 600, "AP Count", 'Suburban'],
    #             [1, 20, "AP Density", 'Urban'],
    #             [2, 30, "AP Density", 'Urban'],
    #             [3, 40, "AP Density", 'Urban'],
    #             [4, 50, "AP Density", 'Urban'],
    #             [5, 10, "AP Density", 'Urban'],
    #             [1, 20, "AP Density", 'Urban'],
    #             [2, 30, "AP Density", 'Urban'],
    #             [3, 40, "AP Density", 'Urban'],
    #             [4, 50, "AP Density", 'Urban'],
    #             [5, 10, "AP Density", 'Urban'],
    #             [1, 20, "AP Density", 'Suburban'],
    #             [2, 30, "AP Density", 'Suburban'],
    #             [3, 40, "AP Density", 'Suburban'],
    #             [4, 50, "AP Density", 'Suburban'],
    #             [5, 10, "AP Density", 'Suburban'],
    #             [1, 20, "AP Density", 'Suburban'],
    #             [2, 30, "AP Density", 'Suburban'],
    #             [3, 40, "AP Density", 'Suburban'],
    #             [4, 50, "AP Density", 'Suburban'],
    #             [5, 60, "AP Density", 'Suburban'],
    #         ]
    #     )

    # # fig, axes = plt.subplots(1,2,figsize=(8,4))
    # # sns.barplot(x="Prem Decile", y="AP Count", col='Geotype', data=data, ax=ax[0])

    # catplot = sns.catplot(x="Prem Decile", y="Value", col="Geotype", row="Metric", data=data, kind="bar", sharey=False)
    # # fig = catplot.get_figure()
    # path = os.path.join(folder, "test.png")
    # catplot.savefig(path)

    # # print(df)
