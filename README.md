# stawpy
Spatio-Temporal Analytics from Wardriving in Python

###Description
This repo provides code to analyze data collected from 'wardriving'.

According to [Wikipedia](https://en.wikipedia.org/wiki/Wardriving):

    Wardriving is the act of searching for Wi-Fi wireless networks by a person usually in a
    moving vehicle, using a laptop or smartphone. Warbiking, warcycling, warwalking and
    similar use the same approach but with other modes of transportation.

The etymology of the name originates from wardialing, a method popularized by a character
played by Matthew Broderick in the film WarGames, and named after that film. War dialing
consists of dialing every phone number in a specific sequence in search of modems.

###Setup using conda
Using Anaconda to handle packages and virtual environments, you can first create a conda
environment called stawpy:

    conda create --name stawpy python=3.7

Activate it (run this each time you switch projects):

    conda activate stawpy

Install required packages:

    conda install pandas matplotlib imagio contextily

For `pygifsicle` you need to pip install.

    pip install pygifsicle

Then run this script with the test data:

    python scripts/run.py
