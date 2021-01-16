"""
Visualize the model results performance against real data.

Written by Ed Oughton.

December 2020.

"""
import os
import sys
import configparser
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), '..', 'scripts', 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']
VIS_PATH = os.path.join(BASE_PATH, '..', 'vis')


def load_data():
    """
    Load evaluation data.

    """
    path = os.path.join(VIS_PATH, 'evaluation', 'real_data.csv')

    data = pd.read_csv(path)

    return data


def process_data(data, ap_coverage_area_baseline):
    """
    Process evaluation data.

    """
    data['predicted_200'] = round(
        data['Gross Internal Area (GIA) (m^2)'] /
        ap_coverage_area_baseline
    )

    return data


def plot(data, ap_coverage_area_baseline):
    """
    Plot data.

    """
    data = data.sort_values(by=['AP Count'])#[:30]

    data['Rank'] = data['AP Count'].rank(method='first', ascending=True)

    data['Rank'] = data['Rank'].astype('int')

    data = data[['Rank', 'AP Count', 'predicted_200']]

    data.columns = ['Rank', 'Real', 'Predicted']

    data = pd.melt(
        data,
        id_vars=['Rank'],
        value_vars=['Real', 'Predicted']
    )

    data = data.sort_values(by=['Rank'])

    ax = sns.catplot(
        x='value',
        y='Rank',
        hue='variable',
        data=data,
        palette=['black', 'red'],
        ci=None,
        legend=None,
        orient='h',
        jitter=False
    )

    title = 'Evaluating Predicted versus Actual \n Wi-Fi APs ({}m)'.format(
        ap_coverage_area_baseline
    )

    ax.set(
        title=title,
        xlabel='Number of Wi-Fi APs per Building',
        ylabel='Rank',
    )

    plt.legend(loc='upper right')

    ax.fig.set_figwidth(4)
    ax.fig.set_figheight(7)
    plt.tight_layout()

    path = os.path.join(VIS_PATH, 'figures', 'predicted_vs_real.png')
    plt.savefig(path)


if __name__ == '__main__':

    ap_coverage_area_baseline = 200

    data = load_data()

    data = process_data(data, ap_coverage_area_baseline)

    plot(data, ap_coverage_area_baseline)
