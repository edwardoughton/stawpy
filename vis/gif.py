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
from mpl_toolkits.axes_grid1 import make_axes_locatable
import pygifsicle

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__),'..','scripts','script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']
RESULTS_PATH = CONFIG['file_locations']['results']
VIS_PATH = CONFIG['file_locations']['vis']


def plot_map(data, folder, i, bounds, time, max_aps, min_aps):

    fig, ax = plt.subplots(figsize=(8, 10))

    plt.rcParams['savefig.pad_inches'] = 0
    plt.autoscale(tight=True)
    ax.get_xaxis().set_visible(False)
    ax.get_yaxis().set_visible(False)
    ax.set_aspect('auto')

    #(minx, miny, maxx, maxy)
    ax.set_xlim(bounds[0], bounds[2])
    ax.set_ylim(bounds[1], bounds[3])

    data.plot(
        column = 'ap_count',
        markersize=50,
        cmap='RdYlBu_r',
        norm=matplotlib.colors.Normalize(vmin=min_aps, vmax=max_aps),
        legend=True,
        edgecolors='b',
        ax=ax
        )

    # plt.colorbar(label='signal_str')
    plt.legend(title="Signal Strength of Counted WiFi APs")
    plt.title('{}'.format((str(time))), fontsize=16)
    ctx.add_basemap(ax, crs=data.crs)
    plt.tight_layout(h_pad=1)

    filename = '{}.png'.format(i)
    path = os.path.join(folder, filename)
    plt.savefig(path, pad_inches=0, bbox_inches='tight')
    plt.close()

    return print('Completed {}'.format(time))


def generate_gif(path_gif, path_images):

    images = []

    filenames = glob.glob(os.path.join(path_images,'*.png'))

    for i in range(0, len([f for f in filenames])):
        for filename in filenames:
            base = os.path.basename(filename)[:-4]
            if i == int(base):

                images.append(imageio.imread(filename))

    imageio.mimsave(os.path.join(path_gif), images)

    return print('Generated .gif')


if __name__ == '__main__':

    path = os.path.join(BASE_PATH, 'wigle', '20200328-00032.shp')
    shapes = gpd.read_file(path)
    shapes = shapes.sort_values('time')

    shapes = shapes[['geometry', 'time', 'signal_str', 'ap_count']]
    shapes['signal_str'] = pd.to_numeric(shapes['signal_str'])

    max_aps = shapes.ap_count.max()
    min_aps = shapes.ap_count.min()

    bounds = (0.11103, 52.2014, 0.14223, 52.22058)

    path_images = os.path.join(VIS_PATH, 'images')
    path_gif = os.path.join(VIS_PATH, 'movies', 'movie.gif')

    to_plot = []
    for idx, unique_time in enumerate(shapes.time.unique()):

        print('working on {}'.format(unique_time))

        if idx > 0:
            current_time = shapes.loc[shapes['time'] == unique_time]
            to_plot = to_plot.append([current_time])
        else:
            to_plot = shapes.loc[shapes['time'] == unique_time]

        plot_map(to_plot, path_images, idx, bounds, unique_time, max_aps, min_aps)

    generate_gif(path_gif, path_images)

    pygifsicle.optimize(path_gif)
