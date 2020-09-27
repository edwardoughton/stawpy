# wawpy
Wardriving Analytics for Wi-Fi with Python (wawpy)

### Description
This repo provides code to develop estimated Wi-Fi analytics using data collected by
'wardriving'.

According to [Wikipedia](https://en.wikipedia.org/wiki/Wardriving):

    Wardriving is the act of searching for Wi-Fi wireless networks by a person usually in a
    moving vehicle, using a laptop or smartphone. Warbiking, warcycling, warwalking and
    similar use the same approach but with other modes of transportation.

The etymology of the name originates from wardialing, a method popularized by a character
played by Matthew Broderick in the film WarGames, and named after that film. War dialing
consists of dialing every phone number in a specific sequence in search of modems.

### Setup using conda
Using Anaconda to handle packages and virtual environments, you can first create a conda
environment called stawpy:

    conda create --name wawpy python=3.7

Activate it (run this each time you switch projects):

    conda activate wawpy

Install the required packages (mainly visualization-related):

    conda install geopandas matplotlib seaborn pykml

### Preprocessing

To preprocess the Output Area (OA) data run the following from the `scripts` folder:

- preprocess.py

This processes all MSOA areas for England and Wales, and Intermediate Zones for Scotland.
This includes all affliated data on premises and households. After calculating the population
in each area, the 'oa_lookup.csv' filde is written which contains important lookup
information, such as the population density or geotype.


### Running the scripts for processing self-collected (sc) WiGLE data

There is a set order in which to run the code from the `scripts` folder as follows:

- oa_list.py
- prems.py
- sc.py

Then the visualization scripts can be run, such as from the `vis` folder:

- vis_sc.py

The `oa_list.py` processes all collected WiGLE .kml data files and exports the
`all_collected_points.shp` file to the `data/intermediate` folder. It finally writes
out the `oa_list.csv` to the same folder.

Next, the `prems.py` script processes the ITRC premises-level data into the
`data/intermediate` folder for each Output Area (OA) in each Local Authority District.

All self-collected data are then processed via the `sc.py` script which adds a set buffer to
each data point and intersects this shape with other APs and buildings. Data are written out
to the `results` folder.

Finally, the `vis_sc.py` script will take the self-collected data for all OAs, and then
produce a set of plotted visualizations.

### Running the scripts for estimating national Wi-Fi availability

To make a national estimate of fixed broadband adoption and Wi-Fi availability, for all OAs
using national statistics (ns), run:

- scripts/ns.py
- vis/vis_ns.py
