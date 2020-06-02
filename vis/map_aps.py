"""
Vis AP Density

"""
import os
import csv
import configparser
import seaborn as sns; sns.set()
import matplotlib.pyplot as plt
import geopandas as gpd
import contextily as ctx

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), '..', 'scripts', 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

RESULTS = os.path.join(BASE_PATH, '..', 'results')

fig, axs = plt.subplots(2, 2, figsize=(20, 20))

countries = [
    # ('W1G6', 0, 0, 'W1G6 - Dense Urban'),
    # ('W1H2', 0, 1, 'london'),
    # ('N78', 1, 0, 'london'),
    ('CB41', 1, 1, 'cambridge'),
]

for country in countries:

    pcd_sector = country[0]
    x = country[1]
    y = country[2]
    plot_title = country[3]
    # buff_value = country[4]

    path = os.path.join(RESULTS, pcd_sector)

    boundary = gpd.read_file(os.path.join(path, 'boundary.shp'), crs='epsg:27700')
    boundary = boundary.to_crs({'init': 'epsg:3857'})
    boundary.plot(facecolor="none", edgecolor='grey', lw=1.2, ax=axs[x, y])

    # axs[x, y].set_title(plot_title)
    # centroid = boundary['geometry'].values[0].representative_point().buffer(buff_value).envelope

    # xmin = min([coord[0] for coord in centroid.exterior.coords])
    # xmax = max([coord[0] for coord in centroid.exterior.coords])

    # ymin = min([coord[1] for coord in centroid.exterior.coords])
    # ymax = max([coord[1] for coord in centroid.exterior.coords])

    # axs[x, y].set_xlim([xmin, xmax])
    # axs[x, y].set_ylim([ymin, ymax])

    ctx.add_basemap(axs[x, y], crs=boundary.crs)

fig.tight_layout()

plt.savefig(os.path.join(BASE_PATH, '..', 'vis', 'figures', 'pcd_sectors.png'))
