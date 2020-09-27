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
    Return a dict with all necessary output area data for
    easy accessing.

    """
    output = {}

    for idx, row in oa_geotypes.iterrows():

        output[row['msoa']] = {
            'lad': row['lad'],
            'region': row['region'],
            'population': row['population'],
            'area_km2': row['area_km2'],
            'pop_density_km2': row['pop_density_km2'],
            'households': row['households'],
            'geotype': row['geotype'],
        }

    return output


def load_results(path):
    """
    Import data from path and return a pandas dataframe.

    """
    data = pd.read_csv(path)

    return data


def histograms(data, folder, buffer_size):
    """
    Generate histograms for urban and rural areas.

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
        # 'floor_area',
        # 'adjusted_floor_area',
        # 'area_km2'
        'geotype',
        'buffer_size'
    ]]

    data.columns = [
        'AP Count',
        # 'Wigle APs (km^2)',
        'Premises Count',
        # 'Building Density (km^2)',
        # 'Resident Count',
        # 'Resident Density (HHs per km^2)',
        # 'Non Residential Count',
        # 'Non Residential Density (km^2)',
        # 'Total Floor Area (km^2)',
        # 'Total Floor Area Adjusted (km^2)',
        # 'Area (km^2)'
        'Geotype',
        'Buffer Size (m)'
    ]

    data.loc[data['Geotype'] == 'urban', 'Geotype'] = 'Urban'
    data.loc[data['Geotype'] == 'suburban', 'Geotype'] = 'Suburban'
    data.loc[data['Geotype'] == 'rural', 'Geotype'] = 'Rural'

    data = data.drop_duplicates()

    max_value = max(data['Premises Count'])
    bins = list(range(0, int(max_value), int(max_value/10)))
    data['Premises Count by Decile'] =  pd.cut(data['Premises Count'], bins)

    catplot = sns.catplot(x="Premises Count by Decile",
        y='AP Count',
        # hue=source_label,
        col='Buffer Size (m)',
        row="Geotype",
        row_order=['Urban', 'Suburban', 'Rural'],
        # capsize=.2,
        # height=6,
        # aspect=.75,
        # sharey=True,
        # sharex=False,
        kind="bar",
        data=data,
        legend_out=False,
        # palette=sns.color_palette(['red', 'black'])
        )

    catplot.set_xticklabels(rotation=45)
    plt.tight_layout()

    #export
    path = os.path.join(folder, "hist_catplot_premises_count.png")
    catplot.savefig(path)


if __name__ == '__main__':

    #Create output folder
    folder = os.path.join(BASE_PATH, '..', 'vis', 'figures')
    if not os.path.exists(folder):
        os.makedirs(folder)

    path = os.path.join(BASE_PATH, 'intermediate', 'oa_list.csv')
    oa_areas = pd.read_csv(path)
    oa_areas = oa_areas['msoa'].unique()

    filename = 'oa_lookup.csv'
    path = os.path.join(BASE_PATH, 'intermediate', filename)
    oa_geotypes = pd.read_csv(path)
    oa_geotypes = define_geotypes(oa_geotypes)

    all_data = []

    buffer_sizes = [100, 200, 300]

    for buffer_size in buffer_sizes:

        for oa_area in oa_areas:#[:10]:

            directory = os.path.join(RESULTS_PATH, oa_area)
            filename = 'oa_aps_buffered_{}.csv'.format(buffer_size)
            path = os.path.join(directory, filename)

            if oa_area in [p for p in oa_geotypes.keys()]:
                oa_data = oa_geotypes[oa_area]
            else:
                continue

            print('-- Getting data for {}'.format(oa_area))

            if os.path.exists(path):

                data = pd.read_csv(path)
                data['buffer_size'] = buffer_size
                geotype = oa_data['geotype']
                data['geotype'] = geotype

                data = data.to_dict('records')

                all_data = all_data + data
            else:
                pass

    print('All processed data loaded for {}m buffer'.format(buffer_size))

    aps = pd.DataFrame(all_data)

    aps.to_csv(os.path.join(RESULTS_PATH, 'all_buffered_points.csv'))

    sample_size = len(aps)

    histograms(aps, folder, buffer_size)
