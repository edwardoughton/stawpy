"""
Generate results using stawpy

Written by Ed Oughton.

March 2020 (amid coronavirus lockdown)

"""
import os
import csv
import configparser

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']


def import_gps_trajectories(path):
    """



    """
    output = []



    return output


#import gsp trajecotires

#import test_drive data

#match time


if __name__ == "__main__":

    path = os.path.join(BASE_PATH, 'gps_trajectories.csv')
    gps_trajectories = import_gps_trajectories(path)

    print(gps_trajectories)
