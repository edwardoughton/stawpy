"""
Calculate AP density using grid squares.

Written by Ed Oughton.

April 2020

"""
import os
import csv
import configparser
import pandas as pd
import geopandas as gpd
from pykml import parser
from shapely.geometry import mapping, Polygon
import numpy as np
import seaborn as sns; sns.set()
import matplotlib.pyplot as plt

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']


def define_geotypes(pcd_sector_geotypes):
    """

    """
    output = {}

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

    return output


def load_collected_ap_data(folder, files):
    """
    Load existing AP data collected.

    """
    all_data = []

    for filename in files:

        if not filename.endswith('.kml'):
            continue

        print('Loading {}'.format(filename))
        path = os.path.join(folder, filename)

        data = load_data(path)

        all_data = all_data + data

    all_data = gpd.GeoDataFrame.from_features(all_data)
    all_data.crs = 'epsg:4326'
    all_data = all_data.to_crs('epsg:27700')

    return all_data


def load_data(path):
    """
    Load existing AP data collected from Wigle to geojson.

    """
    with open(path) as f:
        folder = parser.parse(f).getroot().Document.Folder

    output = []

    for ap_id, pm in enumerate(folder.Placemark):
        device_type = str(pm.description).split('\n')[5]
        if device_type.split(' ')[1] == 'WIFI':
            output.append({
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    'coordinates': (
                        float(str(pm.Point.coordinates).split(',')[0]),
                        float(str(pm.Point.coordinates).split(',')[1])
                    )
                },
                'properties': {
                    'ap_id': ap_id,
                    'name': str(pm.name),
                    'network_id': str(pm.description).split('\n')[0],
                    'encryption': str(pm.description).split('\n')[1],
                    'time': str(pm.description).split('\n')[2],
                    'signal': str(pm.description).split('\n')[3],
                    'accuracy': str(pm.description).split('\n')[4],
                    'type': str(device_type),
                },
            })

    return output


def grid_area(boundary, side_length):
    """
    Create grid area with specfic user-defined tile widths.

    """
    xmin, ymin, xmax, ymax = boundary['geometry'].total_bounds

    cols = list(range(int(np.floor(xmin)), int(np.ceil(xmax)), side_length))
    rows = list(range(int(np.floor(ymin)), int(np.ceil(ymax)), side_length))
    rows.reverse()

    polygons = []
    for x in cols:
        for y in rows:
            polygons.append(
                Polygon(
                    [
                        (x, y),
                        (x+side_length, y),
                        (x+side_length, y-side_length),
                        (x, y-side_length)
                    ]
                )
            )

    grid = gpd.GeoDataFrame({'geometry':polygons})

    grid['FID'] = range(0, len(grid))

    return grid


def intersect_grid_w_points(grid, all_data, buildings, pcd_sector_data):
    """
    Convert point data to grid squares by intersecting.

    """
    print('Intersecting grid with collected waps data')
    f = lambda x:np.sum(all_data.intersects(x))
    grid['waps_collected'] = grid['geometry'].apply(f)

    grid['area_km2'] = grid['geometry'].area / 1e6

    grid['waps_km2'] = grid['waps_collected'] / grid['area_km2']

    print('Total grid squares {}'.format(len(grid)))
    grid = grid.loc[grid['waps_km2'] > 0]
    print('Subset of grid squares without waps data {}'.format(len(grid)))

    print('Add grid ids to building layer')
    try:
        merged = gpd.overlay(buildings, grid, how='intersection')
    except:
        return 'Unable to complete intersection'

    merged = merged[['mistral_fu', 'mistral_bu', 'res_count', 'floor_area',
        'height_tor', 'height_t_1', 'nonres_cou', 'number_of_', 'footprint_',
        'StrSect', 'FID', 'waps_collected', 'area_km2', 'waps_km2',]]
    merged = merged[merged["floor_area"] > 100]
    merged = merged.to_dict('records')

    grid_aggregated = []

    for idx, grid_tile in grid.iterrows():
        res_count = 0
        floor_area = 0
        adjusted_floor_area = 0
        building_count = 0
        nonres_count = 0

        for merged_points in merged:
            if grid_tile['FID'] == merged_points['FID']:
                res_count += merged_points['res_count']
                if merged_points['number_of_'] <= 2: #if number of floors < 2
                    floor_area += merged_points['floor_area']
                    adjusted_floor_area += merged_points['floor_area']
                else:
                    floor_area += merged_points['floor_area']
                    #assume APs at or above 3 floors can't be accessed
                    adjusted_floor_area += (merged_points['footprint_'] * 2)

                building_count += 1
                nonres_count += merged_points['nonres_cou']

        area_km2 = grid_tile['geometry'].area / 1e6

        grid_aggregated.append({
            'geometry': grid_tile['geometry'],
            'properties': {
                'res_count': res_count,
                'floor_area': floor_area,
                'adjusted_floor_area': adjusted_floor_area,
                'building_count': building_count,
                'nonres_count': nonres_count,
                'waps_collected': grid_tile['waps_km2'] * area_km2,
                'waps_km2': grid_tile['waps_km2'],
                'area_km2': area_km2,
                'FID': grid_tile['FID'],
                'geotype': pcd_sector_data['geotype'],
                'lad': pcd_sector_data['lad'],
                'population': pcd_sector_data['population'],
                'area_km2': pcd_sector_data['area_km2'],
                'pop_density_km2': pcd_sector_data['pop_density_km2'],
                'geotype': pcd_sector_data['geotype'],
            }
        })

    grid_aggregated = gpd.GeoDataFrame.from_features(grid_aggregated, crs='epsg:27700')
    grid_aggregated.to_file(os.path.join(folder, 'merged.shp'), crs='epsg:27700')

    print('Total grid squares {}'.format(len(grid_aggregated)))
    grid_aggregated = grid_aggregated.loc[grid_aggregated['floor_area'] > 0]
    print('Subset of grid squares without rmdps data {}'.format(len(grid_aggregated)))

    return grid_aggregated


def plot_results(data, pcd_sector, x_axis, y_axis, plotname, x_label, y_label):
    """
    General plotting function.

    """
    data = data.loc[data[y_axis] > 0]
    plot = sns.jointplot(x=x_axis, y=y_axis, data=data, kind='hex')
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plot.savefig(os.path.join(results, pcd_sector, "{}.png".format(plotname)))
    plt.clf()


if __name__ == '__main__':

    path = os.path.join(BASE_PATH, 'intermediate', 'pcd_list.csv')
    pcd_sectors = pd.read_csv(path)
    pcd_sectors = pcd_sectors.iloc[::-1]

    path = os.path.join(BASE_PATH, 'shapes', 'PostalSector.shp')
    pcd_sector_shapes = gpd.read_file(path)
    pcd_sector_shapes.crs = 'epsg:27700'
    pcd_sector_shapes = pcd_sector_shapes.to_crs('epsg:27700')

    path = os.path.join(BASE_PATH, 'shapes', 'lad_uk_2016-12.shp')
    lad_shapes = gpd.read_file(path)
    lad_shapes.crs = 'epsg:27700'
    lad_shapes = lad_shapes.to_crs('epsg:27700')

    filename = 'pcd_sector_geotypes.csv'
    path = os.path.join(BASE_PATH, 'pcd_sector_geotypes', filename)
    pcd_sector_geotypes = pd.read_csv(path)
    pcd_sector_geotypes = define_geotypes(pcd_sector_geotypes)

    folder_kml = os.path.join(BASE_PATH, 'wigle', 'all_kml_data')
    files = os.listdir(folder_kml)

    results = os.path.join(BASE_PATH, '..', 'results')
    if not os.path.exists(results):
        os.makedirs(results)

    path = os.path.join(BASE_PATH, 'intermediate', 'all_collected_points.shp')
    if not os.path.exists(path):
        all_data = load_collected_ap_data(folder_kml, files)
    else:
        all_data = gpd.read_file(path, crs='epsg:27700')

    side_lengths = [100, 300]
    problem_pcd_sectors = []

    #W1H 2
    #W1G 6
    #W1G 8

    for side_length in side_lengths:

        for idx, row in pcd_sectors.iterrows():

            pcd_sector = row['StrSect']

            # if not pcd_sector == 'NW16':
            #     continue

            print('-- Working on {} with {}m grid width'.format(pcd_sector, side_length))

            pcd_sector_data = pcd_sector_geotypes[pcd_sector]

            # if not pcd_sector_data['lad'] == 'E07000008':
            #     continue

            print('Creating a results folder (if one does not exist already)')
            folder = os.path.join(BASE_PATH, '..', 'results', str(pcd_sector))
            if not os.path.exists(folder):
                os.makedirs(folder)

            print('Getting postcode sector boundary')
            path = os.path.join(folder, 'boundary.shp')
            if not os.path.exists(path):
                boundary = pcd_sector_shapes.loc[pcd_sector_shapes['StrSect'] == pcd_sector]
                boundary.to_file(path, crs='epsg:27700')
            else:
                boundary = gpd.read_file(path, crs='epsg:27700')

            print('Getting the LAD(s) which intersect the postcode sector')
            bbox = boundary.envelope
            geo = gpd.GeoDataFrame()
            geo = gpd.GeoDataFrame({'geometry': bbox})
            merged = gpd.overlay(geo, lad_shapes, how='intersection')

            print('Catch overlaps across lad boundaries')
            lad_ids = []
            for idx, row in merged.iterrows():
                lad_ids.append(row['name'])

            print('Creating a grid across the postcode sector')
            path = os.path.join(folder, 'grid_{}.shp'.format(side_length))
            if not os.path.exists(path):
                grid = grid_area(boundary, side_length)
                grid.to_file(path, crs='epsg:27700')
            else:
                grid = gpd.read_file(path, crs='epsg:27700')

            print('Subsetting the collected points for the postcode sector')
            collected_data = os.path.join(folder, 'collected_points.shp')
            if not os.path.exists(collected_data):
                points_subset = all_data[all_data.intersects(boundary.unary_union)]
                points_subset = points_subset.drop_duplicates('network_id')
                points_subset.to_file(collected_data, crs='epsg:27700')
            else:
                points_subset = gpd.read_file(collected_data, crs='epsg:27700')

            print('Subsetting the premises data for the postcode sector')
            path = os.path.join(folder, 'buildings.shp')
            buildings = gpd.GeoDataFrame()
            if not os.path.exists(path):
                for lad_id in lad_ids:
                    directory = os.path.join(BASE_PATH, 'intermediate', 'prems', lad_id)
                    path_buildings = os.path.join(directory, pcd_sector + '.shp')
                    if not os.path.exists(path_buildings):
                        print('Unable to find building data for {}'.format(pcd_sector))
                        continue
                    else:
                        loaded_buildings = gpd.read_file(path_buildings)
                        buildings = buildings.append(loaded_buildings, ignore_index=True)
                    if len(buildings) > 0:
                        buildings.to_file(path, crs='epsg:27700')
                    else:
                        print('Unable to find building data for {}'.format(pcd_sector))
                        continue
            else:
                buildings = gpd.read_file(path, crs='epsg:27700')

            print('Intersecting grid with collected and building points layers')
            if len(buildings) > 0:
                postcode_aps = intersect_grid_w_points(grid, points_subset, buildings, pcd_sector_data)
                if len(postcode_aps) > 0:
                    if not type(postcode_aps) is str:
                        postcode_aps.to_file( os.path.join(folder, 'postcode_aps_gridded_{}.shp'.format(side_length)), crs='epsg:27700')
                        postcode_aps.to_csv(os.path.join(folder, 'postcode_aps_gridded_{}.csv'.format(side_length)), index=False)
                    else:
                        print('Unable to process {}'.format(pcd_sector))
                        print(pcd_sector)
                        problem_pcd_sectors.append(str(pcd_sector))
            else:
                pass

            # print('Plot results')
            # try:
            #     plot_results(postcode_aps, pcd_sector, "waps_km2", "waps_collected",
            #         'aps_vs_waps_collected_{}'.format(side_length), 'Wigle APs per km^2', 'Wigle APs')
            #     plot_results(postcode_aps, pcd_sector, "waps_km2", "building_count",
            #         'aps_vs_building_count_{}'.format(side_length), 'Wigle APs per km^2', 'Building count')
            #     plot_results(postcode_aps, pcd_sector, "waps_km2", "res_count",
            #         'aps_km2_vs_res_count_{}'.format(side_length), 'Wigle APs per km^2', 'Residential count')
            #     plot_results(postcode_aps, pcd_sector, "waps_km2", "floor_area",
            #         'aps_km2_vs_floor_area_{}'.format(side_length), 'Wigle APs per km^2', 'Floor area (km^2)')
            #     plot_results(postcode_aps, pcd_sector, "waps_km2", "adjusted_floor_area",
            #         'aps_vs_adjusted_floor_area_{}'.format(side_length), 'Wigle APs per km^2', 'Adjusted Floor area (km^2)')
            # except:
            #     pass

        print('Completed script')
        print('----------------')
        print('----------------')
        print('----------------')
        print('Unable to process the following pcd_sectors {}'.format(problem_pcd_sectors))
        problem_pcd_sectors = pd.DataFrame(problem_pcd_sectors)
        folder = os.path.join(BASE_PATH, '..', 'results')
        path = os.path.join(folder, 'problem_pcd_sectors.csv')
        problem_pcd_sectors.to_csv(path)
