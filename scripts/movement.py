"""
Identify daytime and nighttime population.

Written by Ed Oughton

March 2020 (Amid coronavirus lockdown)

"""
import os
import sys
import configparser
import csv
import pandas as pd
import geopandas as gpd

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']
RESULTS_PATH = CONFIG['file_locations']['results']

def read_csv(path):
    """
    Function to read a csv into a pandas dataframe.

    """
    output = pd.read_csv(path)

    return output


def merge_data(population, employment):
    """
    Merge population and employment dataframes.

    """
    data = population.merge(employment, left_on='id', right_on='StrSect')

    return data


def get_area(path, data):
    """
    Load in postcode sector information.

    """
    pcd_sectors = gpd.read_file(path, crs='epsg:27700')

    pcd_sectors['area_km2'] = pcd_sectors['geometry'].area / 1e6

    pcd_sectors = pcd_sectors[['StrSect', 'area_km2']]

    data = data.merge(pcd_sectors, left_on='StrSect', right_on='StrSect')

    return data


def add_metrics(data):
    """

    Get the following:

        - Population density
        - Employment density
        - Daytime change (%)
        - Maximum number of people/users
        - Maximum density of people/users
        - Maximum increase in users (%)

    """
    data['pop_density_km2'] = data['population'] / data['area_km2']

    data['emp_density_km2'] = data['employment'] / data['area_km2']

    data['daytime_change_perc'] = (
        (data['employment'] - data['population']) /
        data['population'] * 100
    )

    data['max_users'] = data['population'] + data['employment']

    data['max_users_density'] =  data['max_users'] / data['area_km2']

    data['max_increase_perc'] = (
        (data['max_users'] - data['population']) /
        data['population'] * 100
    )

    return data


if __name__ == "__main__":

    print('Loading population data')
    path = os.path.join(BASE_PATH, 'population', 'postcode_sectors.csv')
    population = read_csv(path)

    print('Loading employment data')
    path = os.path.join(BASE_PATH, 'daytime_employment', 'daytime_employment.csv')
    employment = read_csv(path)

    print('Merging data')
    data = merge_data(population, employment)

    print('Adding area')
    path = os.path.join(BASE_PATH, 'shapes', 'PostalSector.shp')
    data = get_area(path, data)

    print('Add metrics')
    data = add_metrics(data)

    print('Writing data')
    path = os.path.join(RESULTS_PATH, 'pcd_sector_movement.csv')
    data.to_csv(path, index=False)
