"""
Visualize the model results performance against real data.

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
    path = os.path.join(VIS_PATH, 'evaluation', 'real_data_50.csv')

    data = pd.read_csv(path)

    return data


def process_data(data):
    """
    Process evaluation data.

    """
    data['predicted_200'] = round(data['Gross Internal Area (GIA) (m^2)'] / 200)

    return data


def plot(data):
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
        x='Rank',
        y='value',
        hue='variable',
        data=data,
        palette=['black', 'red'],
        ci=None,
        legend=None
    )

    ax.set(
        title='Evaluating Predicted versus Actual Wi-Fi APs',
        xlabel='Rank',
        ylabel='Number of Wi-Fi APs per Building'
    )
    plt.legend(loc='upper left')
    ax.fig.set_figwidth(10)
    ax.fig.set_figheight(5)
    ax.set_xticklabels(rotation=90)
    plt.tight_layout()

    path = os.path.join(VIS_PATH, 'figures', 'predicted_vs_real.png')
    plt.savefig(path)


if __name__ == '__main__':

    data = load_data()

    data = process_data(data)

    plot(data)
