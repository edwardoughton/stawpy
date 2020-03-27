"""
Visualize postcode sector movement analytics

Written by Ed Oughton

March 2020 (Amid coronavirus lockdown)

"""
import os
import sys
import configparser
import csv
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), '..', 'scripts', 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']
RESULTS_PATH = CONFIG['file_locations']['results']
VIS_PATH = CONFIG['file_locations']['vis']


def load_results(path):
    """

    """
    data = pd.read_csv(path)

    return data


def pop_density(data, folder):
    """

    """
    data = data.loc[data['pop_density_km2'] <= 10000]

    subset = data[['pop_density_km2']]

    n = len(subset)

    plt.figure()

    subset.plot.hist(alpha=0.5, bins=1000)

    plt.title('Population Density (Persons per km^2) (<10k per km^2) (n={})'.format(n))
    plt.legend('')
    path = os.path.join(folder, 'pop_density')
    plt.savefig(path)


def area(data, folder):
    """

    """
    data = data.loc[data['area_km2'] <= 300]

    subset = data[['area_km2']]

    n = len(subset)

    plt.figure()

    subset.plot.hist(alpha=0.5, bins=1000)

    plt.title('Area by Postcode Sector (km^2) (<300 per km^2) (n={})'.format(n))
    plt.legend('')
    path = os.path.join(folder, 'area')
    plt.savefig(path)


def emp_density(data, folder):
    """

    """
    data = data.loc[data['emp_density_km2'] <= 5000]

    subset = data[['emp_density_km2']]

    n = len(subset)

    plt.figure()

    subset.plot.hist(alpha=0.5, bins=1000)

    plt.title('Employment Density (Employment per km^2) (<5k per km^2) (n={})'.format(n))
    plt.legend('')
    path = os.path.join(folder, 'emp_density')
    plt.savefig(path)


def daytime_change(data, folder):
    """

    """
    data = data[~data.isin([np.nan, np.inf, -np.inf]).any(1)]

    data = data.loc[data['daytime_change_perc'] <= 100]

    subset = data[['daytime_change_perc']]

    n = len(subset)

    plt.figure()

    subset.plot.hist(alpha=0.5, bins=1000)

    plt.title('Daytime change (%) (n={})'.format(n))
    plt.legend('')
    path = os.path.join(folder, 'daytime_change')
    plt.savefig(path)


if __name__ == '__main__':

    #Create output folder
    folder = os.path.join(VIS_PATH, 'figures')
    if not os.path.exists(folder):
        os.makedirs(folder)

    #Load pcd sector data
    path = os.path.join(RESULTS_PATH, 'pcd_sector_movement.csv')
    data = load_results(path)

    #vizualise pop density
    pop_density(data, folder)
    area(data, folder)
    emp_density(data, folder)
    daytime_change(data, folder)
