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
import seaborn as sns

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

    plt.title('Population Density (Persons per km^2) (n={})'.format(n))
    plt.legend('')
    plt.xlim(0)
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

    plt.title('Area by Postcode Sector (km^2) (n={})'.format(n))
    plt.legend('')
    plt.xlim(0)
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

    plt.title('Employment Density (Employment per km^2) (n={})'.format(n))
    plt.legend('')
    plt.xlim(0)
    path = os.path.join(folder, 'emp_density')
    plt.savefig(path)


def daytime_change(data, folder):
    """

    """
    data = data[~data.isin([np.nan, np.inf, -np.inf]).any(1)]

    data = data.loc[data['daytime_change_perc'] <= 200]

    subset = data[['daytime_change_perc']]

    n = len(subset)

    plt.figure()

    subset.plot.hist(alpha=0.5, bins=1000)

    plt.title('Daytime change (%) (n={})'.format(n))
    plt.legend('')
    plt.xlim(-100, 100)
    path = os.path.join(folder, 'daytime_change')
    plt.savefig(path)


def max_persons(data, folder):
    """

    """
    data = data[~data.isin([np.nan, np.inf, -np.inf]).any(1)]

    # data = data.loc[data['max_users'] <= 50000]

    subset = data[['max_persons']]

    n = len(subset)

    plt.figure()

    subset.plot.hist(alpha=0.5, bins=1000)

    plt.title('Maximum Number of Persons (n={})'.format(n))
    plt.legend('')
    plt.xlim(0)
    path = os.path.join(folder, 'max_persons')
    plt.savefig(path)


def max_persons_density(data, folder):
    """

    """
    data = data[~data.isin([np.nan, np.inf, -np.inf]).any(1)]

    data = data.loc[data['max_persons_density'] <= 20000]

    subset = data[['max_persons_density']]

    n = len(subset)

    plt.figure()

    subset.plot.hist(alpha=0.5, bins=1000)

    plt.title('Maximum Person Density (Persons per km^2) (n={})'.format(n))
    plt.legend('')
    plt.xlim(0)
    path = os.path.join(folder, 'max_persons_density')
    plt.savefig(path)


def max_increase_perc(data, folder):
    """

    """
    data = data[~data.isin([np.nan, np.inf, -np.inf]).any(1)]

    data = data.loc[data['max_increase_perc'] <= 1000]

    subset = data[['max_increase_perc']]

    n = len(subset)

    plt.figure()

    subset.plot.hist(alpha=0.5, bins=1000)

    plt.title('Maximum Increase (%) (n={})'.format(n))
    plt.legend('')
    plt.xlim(0, 1000)
    path = os.path.join(folder, 'max_increase_perc')
    plt.savefig(path)


def pairwise(data, folder):
    """

    """
    data = data.loc[data['area_km2'] < 300]
    data = data.loc[data['emp_density_km2'] < 5000]

    data = data[[
        'pop_density_km2', 'area_km2',
        'emp_density_km2', 'daytime_change_perc',
        'max_persons', 'max_persons_density', 'max_increase_perc',
        'geotype'
    ]]

    data.columns = [
        'Pop. Density (km^2)', 'Area (km^2)',
        'Emp. Density (km^2)', 'Daytime Change (%)',
        'Max. People', 'Max. People Density', 'Max. Change (%)',
        'Geotype'
    ]

    plt.figure()
    # current_palette = sns.color_palette("RdBu_r", 6) #sns.diverging_palette(10, 220, l=60, n=6, center='dark')
    pairplot = sns.pairplot(data, hue = 'Geotype', hue_order = ['Urban', 'Suburban', 'Rural'], diag_kind = "kde", kind = "scatter", palette = 'husl')

    path = os.path.join(folder, 'pairwise')
    pairplot.savefig(path)


if __name__ == '__main__':

    #Create output folder
    folder = os.path.join(VIS_PATH, 'figures')
    if not os.path.exists(folder):
        os.makedirs(folder)

    #Load pcd sector data
    path = os.path.join(RESULTS_PATH, 'pcd_sector_movement.csv')
    data = load_results(path)

    #Vizualise pop density
    pop_density(data, folder)
    area(data, folder)
    emp_density(data, folder)
    daytime_change(data, folder)
    max_persons(data, folder)
    max_persons_density(data, folder)
    max_increase_perc(data, folder)

    #Plot correlations
    pairwise(data, folder)
