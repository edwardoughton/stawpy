"""
Network Planning in Four Dimensions - np4d

Written by Edward Oughton
November 2019
Oxford, UK

"""
import os
import csv
import configparser
import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon
import glob
import contextily as ctx
import imageio
import matplotlib.pyplot as plt
import matplotlib.colors
import pygifsicle

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__),'..','scripts','script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']
RESULTS_PATH = CONFIG['file_locations']['results']
VIS_PATH = CONFIG['file_locations']['vis']

def load_results(path):
    """

    """
    output = []

    with open(path, 'r') as source:
        reader = csv.DictReader(source)
        for item in reader:
            output.append({
                'time': item['gps_time'],
                'lat': item['lat'],
                'lon': item['lon'],
                'ap_count': item['ap_count']
            })

    return output


def plot_map(data, folder, i, bounds, time):

    fig, ax = plt.subplots(figsize=(8, 10))

    plt.rcParams['savefig.pad_inches'] = 0
    plt.autoscale(tight=True)
    ax.get_xaxis().set_visible(False)
    ax.get_yaxis().set_visible(False)

    #(minx, miny, maxx, maxy)
    ax.set_xlim(bounds[0], bounds[2])
    ax.set_ylim(bounds[1], bounds[3])

    data.plot(
        column = 'ap_count',
        markersize=50,
        cmap='RdYlBu',
        norm=matplotlib.colors.Normalize(vmin=0, vmax=1500),
        legend=True,
        edgecolors='b',
        ax=ax
        )

    plt.title('{}'.format(time), fontsize=16)
    ctx.add_basemap(ax, crs=data.crs)
    filename = '{}'.format(i)
    path = os.path.join(folder, filename)
    plt.savefig(path, pad_inches=0, bbox_inches='tight')
    plt.close()

    return print('Completed {}'.format(i))


def generate_gif(path_gif, path_images):

    images = []

    filenames = glob.glob(os.path.join(path_images,'*.png'))

    for filename in filenames:
        images.append(imageio.imread(filename))

    imageio.mimsave(os.path.join(path_gif), images)

    return print('Generated .gif')


if __name__ == '__main__':

    path = os.path.join(RESULTS_PATH, 'results.shp')
    shapes = gpd.read_file(path)

    lon = []
    lat = []

    for idx, point in shapes.iterrows():
        lon.append(point['geometry'].x)
        lat.append(point['geometry'].y)

    poly_geom = Polygon(zip(lon, lat)).bounds

    path_images = os.path.join(VIS_PATH, 'images')
    path_gif = os.path.join(VIS_PATH, 'movies', 'movie.gif')

    for i in range(1, len(shapes)+1):

        to_plot = shapes[0:i]

        time = to_plot['gps_time'].values

        time = '{}:{}:{}'.format(
            time[i-1].split(', ')[0],
            time[i-1].split(', ')[1],
            time[i-1].split(', ')[2]
        )

        plot_map(to_plot, path_images, i, poly_geom, time)

    generate_gif(path_gif, path_images)

    pygifsicle.optimize(path_gif)
