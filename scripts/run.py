"""
Generate results using stawpy

Written by Ed Oughton.

March 2020 (amid coronavirus lockdown)

"""
import os
import csv
import configparser
import time
import pandas as pd

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']


def import_gps_trajectories(path):
    """
    Import gpd trajectory data.

    Parameters
    ----------
    path : string
        Location of data to import.

    Returns
    -------
    output : list of dicts
        All imported data.

    """
    output = []

    with open(path, 'r') as source:
        reader = csv.DictReader(source)
        for item in reader:

            date = item['Date2'].split(' ')[0]
            full_time = item['Date2'].split(' ')[1]

            output.append({
                'date': date,
                'time': full_time.split('+')[0],
                'lat': float(item['Lat']),
                'lon': float(item['Lng']),
            })

    return output


def import_ap_data(path):
    """
    Import the collected WiFi Access Point (AP) data.

    Parameters
    ----------
    path : string
        Location of data to import.

    Returns
    -------
    output : list of dicts
        All imported data.

    """
    output = []

    with open(path, 'r') as source:
        reader = csv.DictReader(source)
        for item in reader:

            output.append({
                'time': item['Time'].split('+')[0],
                'source': item['Source'],
            })

    return output


def merge_data(gps_trajectories, ap_data):
    """
    Merge the gps trajectories with the collected AP data.

    Parameters
    ----------
    gps_trajectories : list of dicts
        All gpd trajectories.
    ap_data : list of dicts
        All collected APs.

    Returns
    -------
    output : list of dicts
        All merged data.

    """
    output = []

    times = sorted((time.strptime(d['time'], "%H:%M:%S") for d in gps_trajectories), reverse=False)#[:4]

    for i in range(0, len(times)-1):

        full_time1 = times[i]
        full_time2 = times[i+1]

        t1 = ('{}, {}, {}'.format(
            full_time1[3], #hours
            full_time1[4], #mins
            full_time1[5]  #secs
            ))

        t2 = ('{}, {}, {}'.format(
            full_time2[3], #hours
            full_time2[4], #mins
            full_time2[5]  #secs
            ))

        for item in gps_trajectories:

            gps_t = ('{}, {}, {}'.format(
                item['time'].split(':')[0], #hours
                item['time'].split(':')[1], #mins
                item['time'].split(':')[2]  #secs
                ))

            if t1 < gps_t < t2:
                print(t1, gps_t, t2)
                lat = item['lat']
                lon = item['lon']

                ap_count = 0

                for ap in ap_data:

                    ap_time =  ('{}, {}, {}'.format(
                        ap['time'].split(':')[0], #hours
                        ap['time'].split(':')[1], #mins
                        ap['time'].split(':')[2]  #secs
                        ))

                    if t1 < ap_time < t2:

                        ap_count += 1

                output.append({
                    'date': item['date'],
                    'ap_time': ap_time,
                    'gps_time': gps_t,
                    'lat': lat,
                    'lon': lon,
                    'ap_count': ap_count,
                })

    return output


if __name__ == "__main__":

    print('Importing gps trajectories')
    path = os.path.join(BASE_PATH, 'gps_trajectories.csv')
    gps_trajectories = import_gps_trajectories(path)

    print('Importing collected APs')
    path = os.path.join(BASE_PATH, 'test_drive_1.csv')
    ap_data = import_ap_data(path)

    print('Merging data')
    path = os.path.join(BASE_PATH, 'test_drive_1.csv')
    all_data = merge_data(gps_trajectories, ap_data)

    print('Writing data')
    path = os.path.join(BASE_PATH, '..', 'results', 'results.csv')
    data_to_write = pd.DataFrame(all_data)
    data_to_write.to_csv(path, index=False)
