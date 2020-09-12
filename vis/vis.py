"""
Visualize all  data.

Written by Ed Oughton

July 2020

"""
import os
import sys
import configparser
import csv
# import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import seaborn as sns
from shapely import wkt

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), '..', 'scripts', 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']
RESULTS_PATH = CONFIG['file_locations']['results']


def process_lookup(lookup):
    """
    # {'lad': 'E07000074', 'region': 'eastofengland', 'population': 10422,
    # 'area_km2': 84.30112889200247, 'pop_density_km2': 123.62823768767728,
    # 'geotype': 'rural', 'households': 4148, 'prems_residential': 1574,
    # 'prems_residential_floor_area': 113288.30291399988,
    # 'prems_residential_footprint_area': 138206.63525599992,
    # 'prems_non_residential': 1737,
    # 'prems_non_residential_floor_area': 76720.47968999988,
    # 'prems_non_residential_footprint_area': 133104.71751899988}

    """
    output = {}

    for idx, row in lookup.iterrows():

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
            'total_prems': (
                row['prems_residential'] + row['prems_non_residential']
            ),
            'total_prems_density_km2': (
                row['prems_residential'] + row['prems_non_residential']
            ) / row['area_km2'],
        }

    return output

def add_lut_data_to_ns(data, lookup, ap_coverage):
    """

    """
    output = []

    for datum in data:
        area = datum['msoa']
        area = lookup[area]

        number_of_aps = datum['hh_wifi_access'] + datum['baps_total_{}'.format(ap_coverage)]
        # number_of_aps_low = datum['hh_wifi_access'] + datum['baps_total_low']
        # number_of_aps_baseline = datum['hh_wifi_access'] + datum['baps_total_baseline']
        # number_of_aps_high = datum['hh_wifi_access'] + datum['baps_total_high']

        output.append({
            'msoa': datum['msoa'],
            'urban_rural': area['geotype'],
            'total_prems': area['total_prems'],
            'total_prems_density_km2': area['total_prems_density_km2'],
            'number_of_aps': number_of_aps ,
            'number_of_aps_density_km2': number_of_aps / area['area_km2'],
            # 'number_of_aps_low': number_of_aps_low ,
            # 'number_of_aps_density_km2_low': number_of_aps_low / area['area_km2'],
            # 'number_of_aps_baseline': number_of_aps_baseline ,
            # 'number_of_aps_density_km2_baseline': number_of_aps_baseline / area['area_km2'],
            # 'number_of_aps_high': number_of_aps_high ,
            # 'number_of_aps_density_km2_high': number_of_aps_high / area['area_km2'],
        })

    output = pd.DataFrame(output)

    return output


def process_sc_data(data):
    """
    ['geometry', 'res_count', 'floor_area', 'adjusted_floor_area',
       'building_count', 'nonres_count', 'waps_collected', 'waps_km2',
       'area_km2', 'FID', 'geotype', 'lad', 'population', 'pop_density_km2',
       'msoa']

    """
    output = []

    unique_areas = data['msoa'].unique()

    data = data.to_dict('records')

    for area in unique_areas:#[:1]:

        n = 0
        floor_area = 0
        adjusted_floor_area = 0
        total_prems = 0
        waps_collected = 0
        area_km2 = 0

        for item in data:
            if area == item['msoa']:
                n += 1
                floor_area += item['floor_area']
                adjusted_floor_area += item['adjusted_floor_area']
                total_prems += item['building_count']
                waps_collected += item['waps_collected']
                area_km2 += wkt.loads(item['geometry']).area / 1e6

        output.append({
            'msoa': area,
            # 'geotype': item['geotype'],
            # 'lad': item['lad'],
            # 'population': item['population'],
            # 'pop_density_km2': item['pop_density_km2'],
            'floor_area': floor_area / n,
            'adjusted_floor_area': adjusted_floor_area / n,
            'total_prems': total_prems / n,
            'total_prems_density_km2': (total_prems / n) / (area_km2 / n),
            'number_of_aps': waps_collected / n,
            'number_of_aps_density_km2': waps_collected / area_km2,
            'area_km2': area_km2 / n,
        })

    return output


def add_lut_data_to_sc(data, lookup):
    """

    """
    output = []

    for datum in data:
        area = datum['msoa']
        area = lookup[area]
        output.append({
            'msoa': datum['msoa'],
            'urban_rural': area['geotype'],
            'total_prems': datum['total_prems'],
            'total_prems_density_km2': datum['total_prems_density_km2'],
            'number_of_aps': datum['number_of_aps'],
            'number_of_aps_density_km2': datum['number_of_aps_density_km2'],
        })

    output = pd.DataFrame(output)

    return output


def histograms(data, folder, buffer_size):
    """

    """
    data = data[[
            'msoa',
            # 'lad',
            # 'region',
            # 'population',
            # 'area_km2',
            # 'pop_density_km2',
            'urban_rural',
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
            'source',
    ]]

    data.loc[data['urban_rural'] == 'urban', 'urban_rural'] = 'Urban'
    data.loc[data['urban_rural'] == 'suburban', 'urban_rural'] = 'Suburban'
    data.loc[data['urban_rural'] == 'rural', 'urban_rural'] = 'Rural'

    # max_value = max(data['total_prems'])
    # bins = list(range(0, int(max_value), int(max_value/10)))
    # bins = [round(x/1e3,1) for x in bins]
    # data['total_prems_decile'] =  pd.cut(data['total_prems'] / 1e3, bins)

    max_value = max(data['total_prems_density_km2'])
    # bins = list(range(0, int(max_value), int(max_value/10)))
    # bins = [round(x/1e3,1) for x in bins]
    bins = list(range(0, 2000, 200))
    bins = [round(x/1e3,1) for x in bins]
    data['total_prems_density_km2_low_decile'] =  pd.cut(data['total_prems_density_km2'] / 1e3, bins)

    max_value = max(data['total_prems_density_km2'])
    bins = list(range(0, int(max_value), int(max_value/10)))
    bins = [round(x/1e3,1) for x in bins]
    data['total_prems_density_km2_high_decile'] =  pd.cut(data['total_prems_density_km2'] / 1e3, bins)

    data1 = data[[
        'urban_rural',
        # 'total_prems_decile',
        'total_prems_density_km2_low_decile',
        'total_prems_density_km2_high_decile',
        'number_of_aps',
        'source'
    ]]

    data1.rename(
        columns = {
            'urban_rural': 'Geotype',
            # 'total_prems_decile': 'Premices by Decile',
            'total_prems_density_km2_low_decile': 'Premises Density by Decile (1000s per km^2) (v1)',
            'total_prems_density_km2_high_decile': 'Premises Density by Decile (1000s per km^2) (v2)',
            'number_of_aps': 'Value',
            'source': 'Source',
            }, inplace = True)
    data1['Metric'] = 'Total Wi-Fi APs'

    data2 = data[[
        'urban_rural',
        # 'total_prems_decile',
        'total_prems_density_km2_low_decile',
        'total_prems_density_km2_high_decile',
        'number_of_aps_density_km2',
        'source'
    ]]

    data2.rename(
        columns = {
            'urban_rural': 'Geotype',
            # 'total_prems_decile': 'Premices by Decile',
            'total_prems_density_km2_low_decile': 'Premises Density by Decile (1000s per km^2) (v1)',
            'total_prems_density_km2_high_decile': 'Premises Density by Decile (1000s per km^2) (v2)',
            'number_of_aps_density_km2': 'Value',
            'source': 'Source',
            }, inplace = True)
    data2['Metric'] = 'AP Density (km^2)'

    data = data1.append(data2)
    # data['Source'] = 'FB'

    catplot = sns.catplot(x="Premises Density by Decile (1000s per km^2) (v1)", y="Value",
        hue="Source", col="Geotype", col_order=['Urban', 'Suburban', 'Rural'],
        row="Metric", capsize=.2, palette="YlGnBu_d", height=6, aspect=.75,
        sharey=False, sharex=False,
        kind="point", data=data)
    catplot.set_xticklabels(rotation=45)
    plt.tight_layout()

    #export
    path = os.path.join(folder, "hist_catplot_all_data_prem_density_low_{}.png".format(buffer_size))
    catplot.savefig(path)

    catplot = sns.catplot(x="Premises Density by Decile (1000s per km^2) (v2)", y="Value",
        hue="Source", col="Geotype", col_order=['Urban', 'Suburban', 'Rural'],
        row="Metric", capsize=.2, palette="YlGnBu_d", height=6, aspect=.75,
        sharey=False, sharex=False,
        kind="point", data=data)
    catplot.set_xticklabels(rotation=45)
    plt.tight_layout()

    #export
    path = os.path.join(folder, "hist_catplot_all_data_prem_density_high_{}.png".format(buffer_size))
    catplot.savefig(path)



def histograms_by_urban_rural(data, folder, buffer_size, urban_rural, bins):
    """

    """
    data = data[[
            'msoa',
            'urban_rural',
            'total_prems',
            'total_prems_density_km2',
            'number_of_aps',
            'number_of_aps_density_km2',
            'source',
            'buffer_size',
    ]]

    data.loc[data['urban_rural'] == 'urban', 'urban_rural'] = 'Urban'
    data.loc[data['urban_rural'] == 'suburban', 'urban_rural'] = 'Suburban'
    data.loc[data['urban_rural'] == 'rural', 'urban_rural'] = 'Rural'

    data = data[data['urban_rural'] == urban_rural]

    wardriving_data = data[data['source'] == 'Wardriving']
    unique_wardriving_areas = wardriving_data['msoa'].unique()

    data = data[data['msoa'].isin(unique_wardriving_areas)]

    data = data.drop_duplicates()

    # n_predicted = len(data[data['source'] == 'Predicted'])
    # n_wardriving = len(data[data['source'] == 'Wardriving'])

    # data['source'] = data['source'].replace(['Predicted'], 'Predicted (n={})'.format(n_predicted))
    # data['source'] = data['source'].replace(['Wardriving'], 'Wardriving (n={})'.format(n_wardriving))

    # bins = list(range(0, int(max_value), int(max_value/10)))
    # bins = [round(x/1e3,1) for x in bins]
    bins = [round(x/1e3,1) for x in bins]
    data['total_prems_density_km2_decile'] =  pd.cut(data['total_prems_density_km2'] / 1e3, bins)

    # data.to_csv(os.path.join(BASE_PATH, '..', 'vis', 'all_data_to_plot_{}.csv'.format(urban_rural)), index=False)

    data = data[[
        'urban_rural',
        'total_prems_density_km2_decile',
        'number_of_aps_density_km2',
        'source',
        'buffer_size',
    ]]

    source_label = 'Data Source (n={})'.format(len(unique_wardriving_areas))

    data.rename(
        columns = {
            'urban_rural': 'Geotype',
            'total_prems_density_km2_decile': 'Premises Density by Decile (1000s per km^2)',
            'number_of_aps_density_km2': 'AP Density (km^2)',
            'source': source_label,
            'buffer_size': 'Buffer Size (m)'
            }, inplace = True)

    catplot = sns.catplot(x="Premises Density by Decile (1000s per km^2)",
        y='AP Density (km^2)',
        hue=source_label, col='Buffer Size (m)', #row_order=['Urban', 'Suburban', 'Rural'],
        row="Geotype", capsize=.2,
        # palette="YlGnBu_d",
        height=6, aspect=.75,
        sharey=True, sharex=False,
        kind="point",
        data=data,
        legend_out=False,
        palette=sns.color_palette(['red', 'black'])
        )
    # plt.legend(loc='upper left')
    catplot.set_xticklabels(rotation=45)
    plt.tight_layout()

    #export
    path = os.path.join(folder, "hist_catplot_all_data_prem_density_{}.png".format(urban_rural))
    catplot.savefig(path)

if __name__ == '__main__':

    print('Loading area lut')
    filename = 'oa_lookup.csv'
    path = os.path.join(BASE_PATH, 'intermediate', filename)
    lookup = pd.read_csv(path)#[:20]
    lookup = process_lookup(lookup)

    buffer_sizes = [
        100,
        200,
        300,
        400
        ]
    ap_coverage_levels = [
        'low',
        'baseline',
        'high'
    ]

    all_data = pd.DataFrame()

    for buffer_size in buffer_sizes:

        print('Working on buffer size: {}'.format(buffer_size))

        for ap_coverage in ap_coverage_levels:

            print('Working on AP coverage: {}'.format(ap_coverage))

            path = os.path.join(RESULTS_PATH, 'estimated_adoption_ns.csv')
            data_ns = pd.read_csv(path)#[:5]
            data_ns = data_ns.to_dict('records')
            data_ns = add_lut_data_to_ns(data_ns, lookup, ap_coverage)
            data_ns = pd.DataFrame(data_ns)
            data_ns = data_ns[['msoa', 'urban_rural', 'total_prems', 'total_prems_density_km2',
            'number_of_aps', 'number_of_aps_density_km2'
            # 'number_of_aps_low',
            # 'number_of_aps_density_km2_low',
            # 'number_of_aps_baseline',
            # 'number_of_aps_density_km2_baseline',
            # 'number_of_aps_high',
            # 'number_of_aps_density_km2_high',
            ]]
            data_ns['ap_coverage'] = ap_coverage
            data_ns['source'] = 'Predictive Model'
            data_ns['buffer_size'] = buffer_size

            # print('Loading self collected estimates')
            filename = 'all_buffered_points_{}m.csv'.format(buffer_size)
            path = os.path.join(RESULTS_PATH, filename)
            data_sc = pd.read_csv(path)#[:3]
            data_sc = process_sc_data(data_sc)
            data_sc = add_lut_data_to_sc(data_sc, lookup) #'msoa', 'urban_rural',  'total_ap_density_km2'
            data_sc = data_sc[['msoa', 'urban_rural', 'total_prems',
                'total_prems_density_km2', 'number_of_aps', 'number_of_aps_density_km2']]
            data_sc['source'] = 'Wardriving'
            data_sc['buffer_size'] = buffer_size
            data_sc['ap_coverage'] = ap_coverage
            data_sc = data_sc.append(data_sc)

            all_data = all_data.append(data_ns)
            all_data = all_data.append(data_sc)

    all_data.to_csv(os.path.join(BASE_PATH, '..', 'vis', 'all_data_to_plot.csv'), index=False)

    print('Plot histograms')
    folder = os.path.join(BASE_PATH, '..', 'vis', 'figures')
    # histograms(all_data, folder, buffer_size)

    bins = list(range(0, 8500, 750))
    histograms_by_urban_rural(all_data, folder, buffer_size, 'Urban', bins)

    bins = list(range(0, 2500, 500))
    histograms_by_urban_rural(all_data, folder, buffer_size, 'Suburban', bins)

    bins = list(range(0, 1000, 250))
    histograms_by_urban_rural(all_data, folder, buffer_size, 'Rural', bins)

    print('Completed')
    print('---------')
