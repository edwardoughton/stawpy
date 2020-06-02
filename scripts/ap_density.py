"""
Calculate AP density.

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


def subset_points(folder, files):
    """

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


def union_of_points(data):
    """

    """
    buffer = data.buffer(30)
    union = buffer.unary_union
    geom = mapping(union)

    interim = []

    if geom['type'] == 'MultiPolygon':
        for idx, item in enumerate(geom['coordinates']):
                interim.append({
                    'geometry': {
                        'type': 'Polygon',
                        'coordinates': item,
                    },
                    'properties': {
                    }
                })
    else:
        interim.append({
            'geometry': geom,
            'properties': {
            }
        })

    union = gpd.GeoDataFrame.from_features(interim)

    return union


def create_general_buffer(collected_aps, aps_buffered, codepoint_polys):
    """

    """
    f = lambda x:np.sum(collected_aps.intersects(x))
    aps_buffered['waps_collected'] = aps_buffered['geometry'].apply(f)

    aps_buffered['area_km2'] = aps_buffered['geometry'].area / 1e6

    aps_buffered['waps_km2'] = (
        aps_buffered['waps_collected'] / aps_buffered['area_km2'])

    f = lambda x:np.sum(codepoint_polys.intersects(x))
    aps_buffered['rmdps'] = aps_buffered['geometry'].apply(f)

    aps_buffered['rmdps_km2'] = (
        aps_buffered['rmdps'] / aps_buffered['area_km2'])

    return aps_buffered


def subset_codepoint(pcd_sector, boundary):
    """

    """
    pcd_area = pcd_sector[:2]
    pcd_area = ''.join([i for i in pcd_area if not i.isdigit()])

    filename = '{}.shp'.format(pcd_area)
    path = os.path.join(BASE_PATH, 'codepoint', 'shapes', filename)
    codepoint_polys = gpd.read_file(path, crs='epsg:27700')

    filename = '{}_vstreet_lookup.txt'.format(pcd_area)
    path = os.path.join(BASE_PATH, 'codepoint', 'shapes',filename)
    verticals = open(path, "r")

    v_lookup = {}

    for vertical in verticals:

        pcd_id = vertical.split(',')[0]
        pcd_id = pcd_id[1:8].replace('"', '')
        vertical_id = vertical.split(',')[1]
        vertical_id = vertical_id[1:9].replace('"', '')
        v_lookup[vertical_id] = pcd_id

    centroids = codepoint_polys.copy()
    centroids['geometry'] = centroids['geometry'].representative_point()
    centroids = centroids[centroids.intersects(boundary.unary_union)]

    interim = []

    for idx, poly in codepoint_polys.iterrows():

        if poly['POSTCODE'] in centroids['POSTCODE'].unique():
            if poly['POSTCODE'].startswith('V'): # and poly['POSTCODE'] in v_lookup.keys()
                pcd = v_lookup[poly['POSTCODE']]
                poly['POSTCODE'] = pcd

            interim.append({
                'type': 'Feature',
                'geometry': mapping(poly['geometry'].representative_point()),
                'properties': {
                    'POSTCODE': poly['POSTCODE'],
                }
            })

    #import codepoint delivery point data from csv and merge
    filename = '{}.csv'.format(pcd_area)
    path = os.path.join(BASE_PATH, 'codepoint', 'csvs', filename)
    codepoint_lut = pd.read_csv(path)
    codepoint_lut = codepoint_lut.to_records().tolist()

    output = []

    for item in interim:
        for lut_item in codepoint_lut:
            if item['properties']['POSTCODE'] == lut_item[1]:
                output.append({
                    'type': item['type'],
                    'geometry': item['geometry'],
                    'properties': {
                        'POSTCODE': item['properties']['POSTCODE'],
                        # 'po_box': lut_item[3],
                        'total_rmdps': lut_item[4],
                        # 'domestic': lut_item[6],
                        # 'non_domestic': lut_item[7],
                        # 'po_boxes': lut_item[8],
                        # 'type': lut_item[19]
                    }
                })

    output = gpd.GeoDataFrame.from_features(output)

    return output


def intersect_grid_w_points(grid, all_data, buildings):
    """

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
    merged = gpd.overlay(buildings, grid, how='intersection')
    merged = merged[['geometry', 'res_count', 'nonres_cou', 'floor_area', 'FID']]
    merged = merged[merged["floor_area"] > 100]
    merged = merged.to_dict('records')

    grid_aggregated = []

    for idx, grid_tile in grid.iterrows():
        building_count = 0
        res_count = 0
        nonres_count = 0
        floor_area = 0
        for merged_points in merged:
            if grid_tile['FID'] == merged_points['FID']:
                building_count += 1
                res_count += merged_points['res_count']
                nonres_count += merged_points['nonres_cou']
                floor_area += merged_points['floor_area']

        area_km2 = grid_tile['geometry'].area / 1e6

        grid_aggregated.append({
            'geometry': grid_tile['geometry'],
            'properties': {
                'FID': grid_tile['FID'],
                'waps_km2': grid_tile['waps_km2'],
                'building_count': building_count,
                'building_count_km2': building_count / area_km2,
                'res_count': res_count,
                'res_count_km2': res_count / area_km2,
                'nonres_count': nonres_count,
                'nonres_count_km2': nonres_count / area_km2,
                'floor_area': floor_area,
                'floor_area_km2': floor_area / area_km2,
                'area_km2': area_km2,
            }
        })

    grid_aggregated = gpd.GeoDataFrame.from_features(grid_aggregated, crs='epsg:27700')
    grid_aggregated.to_file(os.path.join(folder, 'merged.shp'), crs='epsg:27700')

    print('Total grid squares {}'.format(len(grid_aggregated)))
    grid_aggregated = grid_aggregated.loc[grid_aggregated['floor_area_km2'] > 0]
    print('Subset of grid squares without rmdps data {}'.format(len(grid_aggregated)))
    return grid_aggregated


def plot_results(data, pcd_sector, x_axis, y_axis, plotname, x_label, y_label):
    """

    """
    data = data.loc[data[y_axis] > 0]

    # title = plotname + ': {}'.format(pcd_sector)

    plot = sns.jointplot(x=x_axis, y=y_axis, data=data, kind='hex')#.set_title(title)
    # plot = sns.regplot(x=x_axis, y=y_axis, data=data).set_title(title)

    plt.xlabel(x_label)
    plt.ylabel(y_label)
    # plt.xlabel('Density of Collected WiFi APs (km^2)')
    # plt.ylabel('Density of Postal Delivery Points (km^2)')
    # fig = plot.get_figure()
    plot.savefig(os.path.join(results, pcd_sector, "{}.png".format(plotname)))
    plt.clf()


if __name__ == '__main__':

    path = os.path.join(BASE_PATH, 'intermediate', 'pcd_list.csv')
    pcd_sectors = pd.read_csv(path)

    path = os.path.join(BASE_PATH, 'shapes', 'PostalSector.shp')
    pcd_sector_shapes = gpd.read_file(path)
    pcd_sector_shapes.crs = 'epsg:27700'
    pcd_sector_shapes = pcd_sector_shapes.to_crs('epsg:27700')

    path = os.path.join(BASE_PATH, 'shapes', 'lad_uk_2016-12.shp')
    lad_shapes = gpd.read_file(path)
    lad_shapes.crs = 'epsg:27700'
    lad_shapes = lad_shapes.to_crs('epsg:27700')

    folder_kml = os.path.join(BASE_PATH, 'wigle', 'all_kml_data')
    files = os.listdir(folder_kml)

    results = os.path.join(BASE_PATH, '..', 'results')
    if not os.path.exists(results):
        os.makedirs(results)

    path = os.path.join(BASE_PATH, 'intermediate', 'all_collected_points.shp')
    if not os.path.exists(path):
        all_data = subset_points(folder_kml, files)
    else:
        all_data = gpd.read_file(path, crs='epsg:27700')

    side_lengths = [50, 100, 200, 300]

    for side_length in side_lengths:

        for idx, row in pcd_sectors.iterrows():

            pcd_sector = row['StrSect']

            # if not pcd_sector == 'CB41':
            #     continue

            print('-- Working on {} with {}m grid width'.format(pcd_sector, side_length))

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


        #     # pcd_sector = 'CB41'
        #     # side_length = 100
        #     # folder = os.path.join(BASE_PATH, '..', 'results', 'CB41')
        #     # grid = gpd.read_file(os.path.join(folder, 'grid_100.shp'), crs='epsg:27700')
        #     # collected_data = os.path.join(folder, 'collected_points.shp')
        #     # points_subset = gpd.read_file(collected_data, crs='epsg:27700')
        #     # points_subset = points_subset[:200]
        #     # path = os.path.join(folder, 'buildings.shp')
        #     # buildings = gpd.read_file(path, crs='epsg:27700')

            print('Intersecting grid with collected and building points layers')
            # path = os.path.join(folder, 'grid_{}_with_points.csv'.format(side_length))
            # if not os.path.exists(path):
            if len(buildings) > 0:
                postcode_aps = intersect_grid_w_points(grid, points_subset, buildings)
                if len(postcode_aps) > 0:
                    postcode_aps.to_file( os.path.join(folder, 'postcode_aps_{}.shp'.format(side_length)), crs='epsg:27700')
                    postcode_aps.to_csv(os.path.join(folder, 'postcode_aps_{}.csv'.format(side_length)), index=False)
            else:
                pass
            # else:
            #     postcode_aps = pd.read_csv(path)

            print('Plot results')
            try:
                plot_results(postcode_aps, pcd_sector, "waps_km2", "building_count",
                    'aps_vs_building_count_{}'.format(side_length), 'Wigle APs per km^2', 'Building count')
                plot_results(postcode_aps, pcd_sector, "waps_km2", "res_count",
                    'aps_km2_vs_res_count_{}'.format(side_length), 'Wigle APs per km^2', 'Residential count')
                # plot_results(postcode_aps, pcd_sector, "waps_km2", "nonres_count",
                #     'aps_vs_nonres_count', 'Wigle APs per km^2', 'Non residential count')
                plot_results(postcode_aps, pcd_sector, "waps_km2", "floor_area",
                    'aps_km2_vs_floor_area_{}'.format(side_length), 'Wigle APs per km^2', 'Floor area (km^2)')
                # plot_results(postcode_aps, pcd_sector, "waps_km2", "area_km2",
                #     'aps_vs_area', 'Wigle APs per km^2', 'Area (km^2)')

                plot_results(postcode_aps, pcd_sector, "waps_km2", "building_count_km2",
                    'aps_vs_building_count_km2_{}'.format(side_length), 'Wigle APs per km^2', 'Building count (km^2)')
                plot_results(postcode_aps, pcd_sector, "waps_km2", "res_count_km2",
                    'aps_km2_vs_res_count_km2_{}'.format(side_length), 'Wigle APs per km^2', 'Residential count (km^2)')
                # plot_results(postcode_aps, pcd_sector, "waps_km2", "nonres_count_km2",
                #     'aps_vs_nonres_count_km2', 'Wigle APs per km^2', 'Non residential count (km^2)')
                plot_results(postcode_aps, pcd_sector, "waps_km2", "floor_area_km2",
                    'aps_km2_vs_floor_area_km2_{}'.format(side_length), 'Wigle APs per km^2', 'Floor area (km^2)')
            except:
                pass





        print('Completed script')
