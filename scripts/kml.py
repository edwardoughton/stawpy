"""
Read KML file.

Written by Ed Oughton.

March 2020 (amid coronavirus lockdown)

"""
import os
import csv
import configparser
import time
import pandas as pd
import geopandas as gpd
import lxml
from pykml import parser
import glob

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']


def load_data(path):
    """

    """
    with open(path) as f:
        folder = parser.parse(f).getroot().Document.Folder

    plnm=[]
    cordi=[]
    dates = []
    times = []
    signal_strengths = []

    for pm in folder.Placemark:
        plnm1 = pm.name
        plcs1 = pm.Point.coordinates
        date_time_str = str(pm.description).split('\n')[2]
        date = date_time_str.split(' ')[1][:10]
        time = date_time_str.split('T')[2][:5]

        signal_strength = str(pm.description).split('\n')[3]
        signal_strength = signal_strength.split(' ')[1]

        # if date == '2020-03-28':
        plnm.append(plnm1.text)
        cordi.append(plcs1.text)
        dates.append(date)
        times.append(time)
        signal_strengths.append(signal_strength)

    data = pd.DataFrame()
    data['place_name'] = plnm
    data['coordinates'] = cordi
    data['date'] = dates
    data['time'] = times
    data['signal_strength'] = signal_strengths

    data['lon'], data['lat'] = zip(*data['coordinates'].apply(lambda x: x.split(',', 2)))

    data['lon'] = data['lon'].astype(float)
    data['lat'] = data['lat'].astype(float)
    data['ap_count'] = 1

    data = data.drop(columns=['coordinates'])

    return data

def aggregate(data):
    """

    """
    output = []

    data = data.sort_values('time')

    unique_times = set(data.time.unique())

    for unique_time in list(unique_times):
        signal_strength = []
        lon = []
        lat = []
        ap_count = 0
        for idx, item in data.iterrows():
            if unique_time == item['time']:
                ap_count += 1
                lon.append(item['lon'])
                lat.append(item['lat'])
                signal_strength.append(float(item['signal_strength']))
        output.append({
            'lon': sum(lon) / len(lon),
            'lat': sum(lat) / len(lat),
            'time': unique_time,
            'ap_count': ap_count,
            'signal_strength': sum(signal_strength) / len(signal_strength),
        })

    output = pd.DataFrame(output)

    output = output.sort_values('time')

    return output


if __name__ == '__main__':

    files = os.listdir(os.path.join(BASE_PATH, 'wigle', '2020_4_7'))

    for filename in files:

        print('Working on {}'.format(filename))

        print('Loading .kml data')
        path = os.path.join(BASE_PATH, 'wigle', '2020_4_7', filename)
        data = load_data(path)

        print('Aggregating data')
        data = aggregate(data)

        print('Exporting as .csv')
        filename = filename[:-4]
        data.to_csv(os.path.join(BASE_PATH, 'wigle', '2020_4_7', filename + '.csv'), index=False)

        print('Converting to geopandas geodataframe')
        data = gpd.GeoDataFrame(data, geometry=gpd.points_from_xy(data.lon, data.lat))
        path = os.path.join(BASE_PATH, 'wigle', '2020_4_7', filename + '.shp')

        print('Exporting as .shp')
        data.to_file(path, crs='epsg:4326', index=False)

        print('Completed conversion to .kml')
