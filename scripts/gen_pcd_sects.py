"""
Generate postcode sector shapes.

Written by Ed Oughton.

June 2020

"""
import os
import csv
import configparser
import pandas as pd
import geopandas as gpd

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']


def define_geotypes(pcd_sector_geotypes):
    """

    """
    output = []

    for idx, row in pcd_sector_geotypes.iterrows():

        if row['pop_density_km2'] > 7959:
            row['geotype'] = 'urban'
        # elif row['pop_density_km2'] > 3119:
        #     row['geotype'] = 'suburban 1'
        elif row['pop_density_km2'] > 782:
            row['geotype'] = 'suburban' #'suburban 2'
        # elif row['pop_density_km2'] > 112:
        #     row['geotype'] = 'rural 1'
        # elif row['pop_density_km2'] > 47:
        #     row['geotype'] = 'rural 2'
        # elif row['pop_density_km2'] > 25:
        #     row['geotype'] = 'rural 3'
        # elif row['pop_density_km2'] > 0:
        #     row['geotype'] = 'rural 4'
        else:
            row['geotype'] = 'rural' #'rural 5'

        output.append({
            'pcd_sector': row['id'],
            'lad': row['lad'],
            'population': row['population'],
            'area_km2': row['area_km2'],
            'pop_density_km2': row['pop_density_km2'],
            'geotype': row['geotype'],
        })

    return output













    for idx, row in pcd_sector_geotypes.iterrows():

        if row['pop_density_km2'] > 7959:
            row['geotype'] = 'urban'
        # elif row['pop_density_km2'] > 3119:
        #     row['geotype'] = 'suburban 1'
        elif row['pop_density_km2'] > 782:
            row['geotype'] = 'suburban' #'suburban 2'
        # elif row['pop_density_km2'] > 112:
        #     row['geotype'] = 'rural 1'
        # elif row['pop_density_km2'] > 47:
        #     row['geotype'] = 'rural 2'
        # elif row['pop_density_km2'] > 25:
        #     row['geotype'] = 'rural 3'
        # elif row['pop_density_km2'] > 0:
        #     row['geotype'] = 'rural 4'
        else:
            row['geotype'] = 'rural' #'rural 5'

        output[row['id']] = {
            'lad': row['lad'],
            'population': row['population'],
            'area_km2': row['area_km2'],
            'pop_density_km2': row['pop_density_km2'],
            'geotype': row['geotype'],
        }




if __name__ == '__main__':

    path = os.path.join(BASE_PATH, 'shapes', 'PostalSector.shp')
    pcd_sector_shapes = gpd.read_file(path)
    pcd_sector_shapes.crs = 'epsg:27700'
    pcd_sector_shapes = pcd_sector_shapes.to_crs('epsg:27700')
    pcd_sector_shapes = pcd_sector_shapes[['StrSect', 'geometry']]
    pcd_sector_shapes.columns = ['pcd_sector', 'geometry']

    filename = 'pcd_sector_geotypes.csv'
    path = os.path.join(BASE_PATH, 'pcd_sector_geotypes', filename)
    pcd_sector_geotypes = pd.read_csv(path)
    pcd_sector_geotypes = define_geotypes(pcd_sector_geotypes)
    pcd_sector_geotypes = pd.DataFrame(pcd_sector_geotypes)

    pcd_sector_shapes = pd.merge(pcd_sector_shapes, pcd_sector_geotypes, on='pcd_sector', how='outer')
    filename = 'pcd_sector_shapes.shp'
    path = os.path.join(BASE_PATH, 'intermediate')
    pcd_sector_shapes.to_file(os.path.join(path, filename))
