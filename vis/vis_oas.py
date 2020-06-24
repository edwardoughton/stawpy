"""
Visualize Output Areas (OAs)

Written by Ed Oughton

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
