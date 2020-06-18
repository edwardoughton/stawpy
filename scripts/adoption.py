"""
Estimate internet adoption for households and businesses.

"""
import os
import csv
import configparser
import pandas as pd
import geopandas as gpd
import math
import random

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

random.seed(43)

def load_business_counts(path):
    """
    Load business count for output areas by employee count.

    Counts are at the MSOA or Scottish Intermediate Zone level.

    """
    output = []

    data = pd.read_csv(path)#[:1]

    data = data.to_dict('records')

    unique_area_ids = set()

    for area in data:
        output.append({
            'area_type': area['Area'].split(':')[0],
            'code': area['mnemonic'],
            'micro': area['Micro (0 to 9)'],
            'small': area['Small (10 to 49)'],
            'medium': area['Medium-sized (50 to 249)'],
            'large': area['250 to 499'],
            'very_large': area['500 to 999'],
        })
        unique_area_ids.add(area['mnemonic'])

    return output, list(unique_area_ids)


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


def estimate_adoption_rates(business_counts, bussiness_adoption):
    """
    Estimate adoption rates for businesses.

    """
    output = []

    for area in business_counts:

        micro = math.ceil(area['micro'] * bussiness_adoption['micro'])
        small = math.ceil(area['small'] * bussiness_adoption['small'])
        medium = math.ceil(area['medium'] * bussiness_adoption['medium'])
        large = math.ceil(area['large'] * bussiness_adoption['large'])
        very_large = math.ceil(area['very_large'] * bussiness_adoption['very_large'])

        output.append({
            'area_type': area['area_type'],
            'code': area['code'],
            'micro': micro,
            'small': small,
            'medium': medium,
            'large': large,
            'very_large': very_large,
        })

    return output


def load_lut(path):
    """
    Load a lookup table for MSOA or Scottish IZ areas to LADs.

    """
    all_data = pd.read_csv(path)

    all_data = all_data[['MSOA11CD', 'LAD17CD']]

    all_data = all_data.to_dict('records')

    output = {}

    for item in all_data:
        output[item['MSOA11CD']] = item['LAD17CD']

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


def process_areas(path_output, path_ew, path_scot):
    """
    Load shapes and extract required urban/rural information.

    """
    path = os.path.join(BASE_PATH, 'eng_regions', 'Regions__December_2017__Boundaries.shp')
    regions = gpd.read_file(path)
    regions = regions[['rgn17nm', 'geometry']]

    if not os.path.exists(path_output):

        data_ew = gpd.read_file(path_ew)#[:1000]
        data_ew = data_ew[['msoa11cd', 'geometry']]
        wales = data_ew[data_ew['msoa11cd'].str.startswith('W')]
        wales['region'] = 'Wales'
        wales.columns = ['lower_id', 'geometry', 'region']

        data_ew = gpd.overlay(data_ew, regions, how='intersection')
        data_ew.columns = ['lower_id', 'region', 'geometry']

        data_scot = gpd.read_file(path_scot)
        data_scot = data_scot[['InterZone', 'geometry']]
        data_scot['region'] = 'Scotland'
        data_scot.columns = ['lower_id', 'geometry', 'region']

        all_data = data_ew.append(data_scot, ignore_index=True)
        all_data = all_data.append(wales, ignore_index=True)

        all_data['area_km2'] = all_data['geometry'].area / 1e6

        path = os.path.join(BASE_PATH, 'intermediate', 'output_areas.shp')
        all_data.to_file(path, index=False)
        all_data = all_data[['lower_id', 'area_km2', 'region']]
        all_data.to_csv(path_output, index=False)

    else:
        all_data = pd.read_csv(path_output)

    data = all_data.to_dict('records')

    output = {}

    for item in data:
        output[item['lower_id']] = {
            'area_km2': item['area_km2'],
            'region': item['region'],
        }

    return output


def load_household_deomgraphics(folder, unique_area_ids, lookup, hh_adoption,
    area_features):
    """
    Get the estimated household demographics for each MSOA or Scottish
    IZ area.

    """
    for area_id in unique_area_ids:#[:1]:

        lad_id = lookup[area_id]

        path = os.path.join(folder, 'ass_{}_MSOA11_2018.csv'.format(lad_id))

        area_data = pd.read_csv(path)

        area_data = area_data.loc[area_data['Area'] == area_id]

        area_data = area_data.to_dict('records')#[:1000]

        households, urban_rural, region = get_area_features(area_id, area_data)

        estimated_data = estimate_fixed_access(area_id, area_data, households,
            hh_adoption, urban_rural, region, lad_id)

        estimated_data = estimate_wifi_access(estimated_data, hh_adoption)

    return estimated_data


def get_area_features(area_id, area_data):
    """

    """
    area_km2 = area_features[area_id]['area_km2']
    region = area_features[area_id]['region'].lower().replace(' ', '')

    population = 0
    households = set()

    for area in area_data:
        population += 1
        households.add(area['HID'])

    pop_density_km2 = population / area_km2

    if pop_density_km2 > 700:
        urban_rural = 'urban'
    else:
        urban_rural = 'rural'

    return households, urban_rural, region


def estimate_fixed_access(area_id, area_data, households, hh_adoption,
    urban_rural, region, lad_id):
    """

    """
    fixed_access = []

    for household_id in list(households):#[:10]:

        household_members = []

        for area in area_data:
            if household_id == area['HID']:
                household_members.append(area)

        #treat the oldest person as the head of household
        hh_head = max(household_members, key=lambda x:x['DC1117EW_C_AGE'])

        age = get_age(hh_head)

        probs = []

        probs.append(hh_adoption['internet_access']['age'][age])
        probs.append(hh_adoption['internet_access']['region'][region])
        probs.append(hh_adoption['internet_access']['urban_rural'][urban_rural])

        mean_probability = sum(probs) / len(probs)

        if random.uniform(0, 1) < mean_probability:
            hh_fixed_access = 1
        else:
            hh_fixed_access = 0

        fixed_access.append({
            'PID': hh_head['PID'],
            'Area': hh_head['Area'],
            'region': region,
            'lad_id': lad_id,
            'urban_rural': urban_rural,
            'age': age,
            # 'DC1117EW_C_SEX': household_member['DC1117EW_C_SEX'],
            # 'DC1117EW_C_AGE': hh_head['DC1117EW_C_AGE'],
            # 'DC2101EW_C_ETHPUK11': household_member['DC2101EW_C_ETHPUK11'],
            'HID': hh_head['HID'],
            'hh_fixed_access_prob':  round(mean_probability, 4),
            'hh_fixed_access': hh_fixed_access
        })

    return fixed_access


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


def estimate_wifi_access(estimated_data, hh_adoption):
    """

    """
    output = []

    for hh_head in estimated_data:

        probs = []

        probs.append(hh_adoption['wifi_access']['age'][hh_head['age']])
        probs.append(hh_adoption['wifi_access']['region'][hh_head['region']])
        probs.append(hh_adoption['wifi_access']['urban_rural'][hh_head['urban_rural']])

        mean_probability = sum(probs) / len(probs)

        if hh_head['hh_fixed_access'] == 1:
            if random.uniform(0, 1) < mean_probability:
                hh_wifi_access = 1
            else:
                hh_wifi_access = 0
        else:
            hh_wifi_access = 0

        output.append({
            'PID': hh_head['PID'],
            'Area': hh_head['Area'],
            'region': hh_head['region'],
            'lad_id': hh_head['lad_id'],
            'urban_rural': hh_head['urban_rural'],
            'age': hh_head['age'],
            'HID': hh_head['HID'],
            'hh_fixed_access_prob':  hh_head['hh_fixed_access_prob'],
            'hh_fixed_access': hh_head['hh_fixed_access'],
            'hh_wifi_access_prob': round(mean_probability, 4),
            'hh_wifi_access': hh_wifi_access,
        })

    return output


def aggregate_data(results, unique_area_ids):
    """

    """
    output = []

    for area_id in unique_area_ids:

        households = 0
        hh_fixed_access = 0
        hh_wifi_access = 0

        for item in results:
            if area_id == item['Area']:

                households += 1

                if item['hh_fixed_access'] == 1:
                    hh_fixed_access += 1
                if item['hh_wifi_access'] == 1:
                    hh_wifi_access += 1

        # if not hh_fixed_access == 0 and households == 0:
        #     perc_hh_fixed_access = (hh_fixed_access / households) * 100
        # else:
        #     perc_hh_fixed_access = 0

        # if not hh_fixed_access == 0 and households == 0:
        #     perc_hh_wifi_access = (hh_wifi_access / households) * 100
        # else:
        #     perc_hh_wifi_access = 0

        output.append({
            'Area': area_id,
            # 'region': hh_head['region'],
            # 'lad_id': hh_head['lad_id'],
            # 'urban_rural': hh_head['urban_rural'],
            'hh_fixed_access': hh_fixed_access,
            'hh_wifi_access': hh_wifi_access,
            'households': households,
            # 'perc_hh_fixed_access': perc_hh_fixed_access,
            # 'perc_hh_wifi_access': perc_hh_wifi_access,
        })

    return output


if __name__ == '__main__':

    print('--Working on estimating business adoption')

    print('Loading local business counts')
    path = os.path.join(BASE_PATH, 'ons_local_business_counts', 'business_counts.csv')
    businesses, unique_area_ids = load_business_counts(path)

    # print('Loading local internet access statistics')
    # bussiness_adoption = internet_access_by_business()

    # print('Estimate adoption')
    # adopted = estimate_adoption_rates(businesses, bussiness_adoption)

    print('--Working on estimating household adoption')

    print('Loading msoa/iz areas to LAD lookup table')
    path = os.path.join(BASE_PATH, 'msoa_lut', 'gb_msoa_lut.csv')
    lookup = load_lut(path)

    print('Get household access statistics')
    hh_adoption = internet_access_by_households()

    print('Processing shape areas')
    path_output = os.path.join(BASE_PATH, 'intermediate', 'area_features.csv')
    filename = 'Middle_Layer_Super_Output_Areas__December_2011__Boundaries.shp'
    path_ew = os.path.join(BASE_PATH, 'msoa_shapes', filename)
    filename = 'SG_IntermediateZone_Bdry_2011.shp'
    path_scot = os.path.join(BASE_PATH, 'scottish_iz_shapes', filename)
    area_features = process_areas(path_output, path_ew, path_scot)

    print('Loading household demographic data')
    folder = os.path.join(BASE_PATH, 'hh_demographics_msoa_2018')
    results = load_household_deomgraphics(
        folder,
        unique_area_ids,
        lookup,
        hh_adoption,
        area_features
    )

    print('Aggregating results')
    results = aggregate_data(results, unique_area_ids)

    print('Exporting results')
    results = pd.DataFrame(results)
    results.to_csv(os.path.join(BASE_PATH, '..', 'results', 'adoption_estimates.csv'))
