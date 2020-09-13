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
    Process all output area lookup data into easily accessible dict.

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
    Add the output area data to the national stats estimate.

    """
    output = []

    for datum in data:
        area = datum['msoa']
        area = lookup[area]

        number_of_aps = datum['hh_wifi_access'] + datum['baps_total_{}'.format(ap_coverage)]

        output.append({
            'msoa': datum['msoa'],
            'urban_rural': area['geotype'],
            'total_prems': area['total_prems'],
            'total_prems_density_km2': area['total_prems_density_km2'],
            'number_of_aps': number_of_aps ,
            'number_of_aps_density_km2': number_of_aps / area['area_km2'],
        })

    output = pd.DataFrame(output)

    return output


def process_sc_data(data):
    """
    Process the self-collected wardriving data.

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
    Add the output area data to the self-collected wardriving data.

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


def histograms_by_urban_rural(data, folder, buffer_size): #urban_rural, bins
    """
    Generate histograms for urban and rural areas.

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

    # data = data[data['urban_rural'] == urban_rural]

    wardriving_data = data[data['source'] == 'Wardriving']
    unique_wardriving_areas = wardriving_data['msoa'].unique()

    data = data[data['msoa'].isin(unique_wardriving_areas)]

    data = data.drop_duplicates()

    # bins = [round(x/1e3,1) for x in bins]
    # data['total_prems_density_km2_decile'] =  pd.cut(
    #     data['total_prems_density_km2'] / 1e3, bins)

    max_value = max(data['total_prems_density_km2'])
    bins = list(range(0, int(max_value), int(max_value/10)))
    data['total_prems_density_km2_decile'] =  pd.cut(
        data['total_prems_density_km2'], bins)

    path = os.path.join(BASE_PATH, '..', 'vis', 'all_data_to_plot.csv')
    data.to_csv(path, index=False)

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
            'total_prems_density_km2_decile': 'Premises Density by Decile (per km^2)',
            'number_of_aps_density_km2': 'AP Density (km^2)',
            'source': source_label,
            'buffer_size': 'Buffer Size (m)'
            }, inplace = True)

    catplot = sns.catplot(x="Premises Density by Decile (per km^2)",
        y='AP Density (km^2)',
        hue=source_label,
        col='Buffer Size (m)',
        row="Geotype",
        row_order=['Urban', 'Suburban', 'Rural'],
        capsize=.2,
        height=6, aspect=.75,
        sharey=True, sharex=False,
        kind="point",
        data=data,
        legend_out=True,
        palette=sns.color_palette(['red', 'black'])
        )

    catplot.set_xticklabels(rotation=45)
    plt.tight_layout()

    #export
    path = os.path.join(folder, "hist_catplot_prem_density.png")
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
        # 400
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
            data_ns = pd.read_csv(path)#[:50]
            data_ns = data_ns.to_dict('records')
            data_ns = add_lut_data_to_ns(data_ns, lookup, ap_coverage)
            data_ns = pd.DataFrame(data_ns)
            data_ns = data_ns[['msoa', 'urban_rural', 'total_prems',
                'total_prems_density_km2', 'number_of_aps', 'number_of_aps_density_km2'
            ]]
            data_ns['ap_coverage'] = ap_coverage
            data_ns['source'] = 'Predictive Model'
            data_ns['buffer_size'] = buffer_size

            filename = 'all_buffered_points_{}m.csv'.format(buffer_size)
            path = os.path.join(RESULTS_PATH, filename)
            data_sc = pd.read_csv(path)#[:50]
            data_sc = process_sc_data(data_sc)
            data_sc = add_lut_data_to_sc(data_sc, lookup)
            data_sc = data_sc[['msoa', 'urban_rural', 'total_prems',
                'total_prems_density_km2', 'number_of_aps', 'number_of_aps_density_km2'
            ]]
            data_sc['source'] = 'Wardriving'
            data_sc['buffer_size'] = buffer_size
            data_sc['ap_coverage'] = ap_coverage
            data_sc = data_sc.append(data_sc)

            all_data = all_data.append(data_ns)
            all_data = all_data.append(data_sc)

    path = os.path.join(BASE_PATH, '..', 'vis', 'all_data_to_plot.csv')
    all_data.to_csv(path, index=False)

    print('Plot histograms')
    folder = os.path.join(BASE_PATH, '..', 'vis', 'figures')

    bins = list(range(0, 2000, 500))
    histograms_by_urban_rural(all_data, folder, buffer_size)

    print('Completed')
    print('---------')
