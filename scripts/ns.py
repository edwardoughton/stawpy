"""
Estimate internet adoption for households and businesses using national statistics (ns).

"""
import os
import csv
import configparser
import pandas as pd
import geopandas as gpd
import math
import random
from tqdm import tqdm

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

random.seed(43)

def load_business_data(path):
    """
    Load business count for output areas by employee count.

    Counts are at the MSOA or Scottish Intermediate Zone level.

    """
    output = {}

    data = pd.read_csv(path)#[:1]

    data = data.to_dict('records')

    for area in data:

        micro = int(area['Micro (0 to 9)'])
        small = int(area['Small (10 to 49)'])
        medium = int(area['Medium-sized (50 to 249)'])
        large = int(area['250 to 499'])
        very_large = int(area['500 to 999'] + area['1000+'])

        output[area['mnemonic']] = {
            'area_type': area['Area'].split(':')[0],
            'micro': micro,
            'small': small,
            'medium': medium,
            'large': large,
            'very_large': very_large,
            'total': micro + small + medium + large + very_large,
        }

    return output


def internet_access_by_business():
    """
    Internet access data taken from the ONS
    E-commerce and ICT activity survey (2018).
    https://www.ons.gov.uk/businessindustryandtrade/itandinternetindustry/bulletins/ecommerceandictactivity/2018

    """
    return {
            'micro': 0.837,
            'small': 0.943,
            'medium': 0.988,
            'large': 0.987,
            'very_large': 0.983,
    }


def load_lookup(data):
    """

    """
    output = {}

    for idx, row in data.iterrows():

        output[row['msoa']] = {
            'lad': row['lad'],
            'region': row['region'],
            'population': row['population'],
            'area_km2': row['area_km2'],
            'pop_density_km2': row['pop_density_km2'],
            'geotype': row['geotype'],
            'households': row['households'],
            'prems_residential': row['prems_residential'],
            'prems_residential_floor_area': row['prems_residential_floor_area'],
            'prems_residential_footprint_area': row['prems_residential_footprint_area'],
            'prems_non_residential': row['prems_non_residential'],
            'prems_non_residential_floor_area': row['prems_non_residential_floor_area'],
            'prems_non_residential_footprint_area': row['prems_non_residential_footprint_area'],
        }

    return output


def internet_access_by_households():
    """
    OFCOM NATIONS & REGIONS TECHNOLOGY TRACKER - 2019.
    3rd January to 28th February 2019
    https://www.ofcom.org.uk/__data/assets/pdf_file/0026/143981/technology-tracker-2019-uk-data-tables.pdf

    internet_access: p363 / 364, Table 52

    """
    return {
        'internet_access': {
            'age': {
                '16-24': 0.94,
                '25-34': 0.94,
                '35-54': 0.93,
                '55+': 0.72,
            },
            'region': {
                'scotland': 0.82,
                'wales': 0.82,
                'london': 0.87,
                'southeast': 0.9,
                'southwest': 0.91,
                'eastmidlands': 0.83,
                'westmidlands': 0.82,
                'eastofengland': 0.87,
                'yorkshireandthehumber': 0.78,
                'northeast': 0.88,
                'northwest': 0.85,
            },
            'urban_rural': {
                'urban': 0.85,
                'rural': 0.88,
            },
        },
        'wifi_access': {
            'age': {
                '16-24': 0.95,
                '25-34': 0.91,
                '35-54': 0.93,
                '55+': 0.88,
            },
            'region': {
                'scotland': 0.92,
                'wales': 0.84,
                'london': 0.97,
                'southeast': 0.84,
                'southwest': 0.88,
                'eastmidlands': 0.86,
                'westmidlands': 0.96,
                'eastofengland': 0.97,
                'yorkshireandthehumber': 0.87,
                'northeast': 0.98,
                'northwest': 0.97,
            },
            'urban_rural': {
                'urban': 0.92,
                'rural': 0.88,
            },
        },
    }

def estimate_business_stats(area_id, bus_counts, bussiness_adoption, lookup, ap_coverage_area):
    """
    Estimate adoption rates for businesses.

    """
    lookup[area_id]['population']

    floor_area = lookup[area_id]['prems_non_residential_footprint_area']

    emp_micro = (bus_counts['micro'] * 5)
    emp_small = (bus_counts['small'] * 25)
    emp_medium = (bus_counts['medium'] * 150)
    emp_large = (bus_counts['large'] * 350)
    emp_very_large = (bus_counts['very_large'] * 750)
    emp_total = emp_micro + emp_small + emp_medium + emp_large + emp_very_large

    #ba_ stands for Business Adoption
    ba_micro = bus_counts['micro'] * bussiness_adoption['micro']
    ba_small = bus_counts['small'] * bussiness_adoption['small']
    ba_medium = bus_counts['medium'] * bussiness_adoption['medium']
    ba_large = bus_counts['large'] * bussiness_adoption['large']
    ba_very_large = bus_counts['very_large'] * bussiness_adoption['very_large']
    total_businesses = bus_counts['total']

    #disaggregate total floor area based on employees
    bfa_micro = (emp_micro / emp_total) * floor_area
    bfa_small = (emp_small / emp_total) * floor_area
    bfa_medium = (emp_medium / emp_total) * floor_area
    bfa_large = (emp_large / emp_total) * floor_area
    bfa_very_large = (emp_very_large / emp_total) * floor_area

    #fa_ stands for Adopted Floor Area (m2)
    bafa_micro = bfa_micro * bussiness_adoption['micro']
    bafa_small = bfa_small * bussiness_adoption['small']
    bafa_medium = bfa_medium * bussiness_adoption['medium']
    bafa_large = bfa_large * bussiness_adoption['large']
    bafa_very_large = bfa_very_large * bussiness_adoption['very_large']

    baps_micro = round(bafa_micro / ap_coverage_area)
    baps_small = round(bafa_small / ap_coverage_area)
    baps_medium = round(bafa_medium / ap_coverage_area)
    baps_large = round(bafa_large / ap_coverage_area)
    baps_very_large = round(bafa_very_large / ap_coverage_area)

    return {
        'area_type': bus_counts['area_type'],
        'businesses': total_businesses,
        'ba_micro': ba_micro,
        'ba_small': ba_small,
        'ba_medium': ba_medium,
        'ba_large': ba_large,
        'ba_very_large': ba_very_large,
        'ba_total': ba_micro + ba_small + ba_medium + ba_large + ba_very_large,
        'bafa_micro': bfa_micro,
        'bafa_small': bfa_small,
        'bafa_medium': bfa_medium,
        'bafa_large': bfa_large,
        'bafa_very_large': bfa_very_large,
        'bafa_total': bfa_micro + bfa_small + bfa_medium + bfa_large + bfa_very_large,
        'baps_micro': baps_micro,
        'baps_small': baps_small,
        'baps_medium': baps_medium,
        'baps_large': baps_large,
        'baps_very_large': baps_very_large,
        'baps_total': baps_micro + baps_small + baps_medium + baps_large + baps_very_large,
    }


def load_household_deomgraphics(folder, area_id, lookup, hh_adoption, lad_id):
    """
    Get the estimated household demographics for each MSOA or Scottish
    IZ area.

    """
    directory = os.path.join(BASE_PATH, 'intermediate', 'hh_by_oa')
    if not os.path.exists(directory):
        os.makedirs(directory)

    path_hh_data = os.path.join(directory, area_id + '.csv')

    if not os.path.exists(path_hh_data):

        path = os.path.join(folder, 'ass_{}_MSOA11_2018.csv'.format(lad_id))

        if not os.path.exists(path):
            return 'oa hh data not found'

        hh_data = pd.read_csv(path)

        hh_data = hh_data.loc[hh_data['Area'] == area_id]

        hh_data.to_csv(path_hh_data, index=False)

    else:

        hh_data = pd.read_csv(path_hh_data)

    hh_data = hh_data.to_dict('records')#[:1000]

    return hh_data


def estimate_hh_stats(area_id, hh_data, hh_adoption, lookup, lad_id):
    """

    """
    region = lookup[area_id]['region'].lower().replace(' ', '')
    urban_rural = lookup[area_id]['geotype']

    households = set()

    for item in hh_data:
        households.add(item['HID'])

    output = []

    for household_id in list(households):#[:10]:

        household_members = []

        for item in hh_data:
            if household_id == item['HID']:
                household_members.append(item)

        #treat the oldest person as the head of household
        hh_head = max(household_members, key=lambda x:x['DC1117EW_C_AGE'])

        age = get_age(hh_head)

        if urban_rural == 'suburban':
            urban_rural_adapted = 'urban'
        else:
            urban_rural_adapted = urban_rural

        probs = []

        probs.append(hh_adoption['internet_access']['age'][age])
        probs.append(hh_adoption['internet_access']['region'][region])
        probs.append(hh_adoption['internet_access']['urban_rural'][urban_rural_adapted])

        mean_probability_fixed_access = sum(probs) / len(probs)

        if random.uniform(0, 1) < mean_probability_fixed_access:
            hh_fixed_access = 1
        else:
            hh_fixed_access = 0

        probs = []

        probs.append(hh_adoption['wifi_access']['age'][age])
        probs.append(hh_adoption['wifi_access']['region'][region])
        probs.append(hh_adoption['wifi_access']['urban_rural'][urban_rural_adapted])

        mean_probability_wifi_access = sum(probs) / len(probs)

        if hh_fixed_access == 1:
            if random.uniform(0, 1) < mean_probability_wifi_access:
                hh_wifi_access = 1
            else:
                hh_wifi_access = 0
        else:
            hh_wifi_access = 0

        output.append({
            'PID': hh_head['PID'],
            'Area': hh_head['Area'],
            'region': region,
            'lad_id': lad_id,
            'urban_rural': urban_rural,
            'age': age,
            'HID': hh_head['HID'],
            'hh_fixed_access_prob':  round(mean_probability_fixed_access, 4),
            'hh_fixed_access': hh_fixed_access,
            'hh_wifi_access_prob': round(mean_probability_wifi_access, 4),
            'hh_wifi_access': hh_wifi_access,
        })

    return output


def get_age(hh_head):
    """

    """
    if 16 <= hh_head['DC1117EW_C_AGE'] <= 24:
        return '16-24'
    elif 25 <= hh_head['DC1117EW_C_AGE'] <= 34:
        return '25-34'
    elif 35 <= hh_head['DC1117EW_C_AGE'] <= 54:
        return '35-54'
    else:
        return '55+'


def aggregate_data(business_data, estimated_data, area_id, lookup, lad_id):
    """

    """
    area_km2 = lookup[area_id]['area_km2']

    households = 0
    hh_fixed_access = 0
    hh_wifi_access = 0

    for item in estimated_data:
        if area_id == item['Area']:

            households += 1

            if item['hh_fixed_access'] == 1:
                hh_fixed_access += 1
            if item['hh_wifi_access'] == 1:
                hh_wifi_access += 1

    if hh_fixed_access > 0 or households > 0:
        perc_hh_fixed_access = (hh_fixed_access / households) * 100
    else:
        perc_hh_fixed_access = 0

    if hh_fixed_access > 0 or households > 0:
        perc_hh_wifi_access = (hh_wifi_access / households) * 100
    else:
        perc_hh_wifi_access = 0

    return {
        'msoa': area_id,
        'area_km2': area_km2,
        'population': lookup[area_id]['population'],
        'population_km2': lookup[area_id]['population'] / area_km2,
        'urban_rural': lookup[area_id]['geotype'],
        'households': households,
        'households_km2': households / area_km2,
        'hh_fixed_access': hh_fixed_access,
        'hh_wifi_access': hh_wifi_access,
        'hh_fixed_access_km2': hh_fixed_access / area_km2,
        'hh_wifi_access_km2': hh_wifi_access / area_km2,
        'perc_hh_fixed_access': perc_hh_fixed_access,
        'perc_hh_wifi_access': perc_hh_wifi_access,
        'region': lookup[area_id]['region'],
        'lad_id': lad_id,
        'businesses': business_data['businesses'],
        'business_density_km2': business_data['businesses'] / area_km2,
        #busines adoption - ba_
        'ba_micro': business_data['ba_micro'],
        'ba_small': business_data['ba_small'],
        'ba_medium': business_data['ba_medium'],
        'ba_large': business_data['ba_large'],
        'ba_very_large': business_data['ba_very_large'],
        'ba_total': business_data['ba_total'],
        #busines adoption floor area - bafa_
        'bafa_micro': business_data['bafa_micro'],
        'bafa_small': business_data['bafa_small'],
        'bafa_medium': business_data['bafa_medium'],
        'bafa_large': business_data['bafa_large'],
        'bafa_very_large': business_data['bafa_very_large'],
        'bafa_total': business_data['bafa_total'],
        #business access points - baps_
        'baps_micro': business_data['baps_micro'],
        'baps_small': business_data['baps_small'],
        'baps_medium': business_data['baps_medium'],
        'baps_large': business_data['baps_large'],
        'baps_very_large': business_data['baps_very_large'],
        'baps_total': business_data['baps_total'],
        'baps_density_km2': business_data['baps_total'] / area_km2,
    }


if __name__ == '__main__':

    print('----Working on estimating business adoption')
    print('----')

    ap_coverage_area = 50

    print('Loading local business counts')
    path = os.path.join(BASE_PATH, 'ons_local_business_counts', 'business_counts.csv')
    business_data = load_business_data(path)

    print('Loading local internet access statistics')
    bussiness_adoption = internet_access_by_business()

    print('Get household access statistics')
    hh_adoption = internet_access_by_households()

    print('Load lookup')
    filename = 'oa_lookup.csv'
    path = os.path.join(BASE_PATH, 'intermediate', filename)
    lookup = pd.read_csv(path)
    lookup = load_lookup(lookup)

    output = []

    print('Exporting adoption results')
    for area_id in tqdm(business_data.keys()):

        # if not area_id == 'E02004555':
        #     continue

        if area_id in lookup:
            lad_id = lookup[area_id]['lad']
        else:
            continue

        if area_id in business_data:
            bus_counts = business_data[area_id]
        else:
            continue

        estimated_bus_data = estimate_business_stats(area_id, bus_counts,
            bussiness_adoption, lookup, ap_coverage_area)

        directory = os.path.join(BASE_PATH, 'intermediate', 'hh_by_lad_msoa', lad_id)
        path_hh = os.path.join(directory, area_id + '.csv')
        if os.path.exists(path_hh):
            hh_data = pd.read_csv(path_hh)
            hh_data = hh_data.to_dict('records')#[:1000]
        else:
            continue

        folder = os.path.join(BASE_PATH, 'intermediate', 'hh_data_aggregated', lad_id)
        if not os.path.exists(folder):
            os.makedirs(folder)
        path = os.path.join(folder, area_id + '.csv')

        if not os.path.exists(path):
            estimated_hh_data = estimate_hh_stats(area_id, hh_data, hh_adoption, lookup, lad_id)
            hh_data_to_write = pd.DataFrame(estimated_hh_data)
            hh_data_to_write.to_csv(path, index=False)
        else:
            estimated_hh_data = pd.read_csv(path)
            estimated_hh_data = estimated_hh_data.to_dict('records')#[:1000]

        estimated_data = aggregate_data(estimated_bus_data, estimated_hh_data, area_id, lookup, lad_id)

        output.append(estimated_data)

    print('Exporting adoption results')
    results = pd.DataFrame(output)
    path = os.path.join(BASE_PATH, '..', 'results', 'estimated_adoption_ns.csv')
    results.to_csv(path, index=False)
