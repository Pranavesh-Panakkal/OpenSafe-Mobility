<div align="center">

# OpenSafe Mobility
**Open** source **S**ituational **A**wareness **F**ram**e**work for **Mobility**

<a href="https://hydra.cc/"><img alt="Config: Hydra" src="https://img.shields.io/badge/Config-Hydra-89b8cd"></a>
[![Paper](https://img.shields.io/badge/paper-under%20review-blue)]()
[![Keywords](https://img.shields.io/badge/keywords-urban%20flooding%2C%20mobility%2C%20situational%20awareness-blue)]()
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
</div>

## Context

This repository contains the code for OpenSafe Mobility. OpenSafe Mobility is the first among a group of tools collectively called OpenSafe. OpenSafe project aims to conceptualize, develop, validate, and maintain reliable and affordable situational awareness and emergency response decision-making tools.

## Description
OpenSafe Mobility aims to provide real-time information on flooded roads. It achieves this by performing real-time flood simulations using a state-of-the-art flood model, rainfall data, and network and spatial analyses.

## Transferability

The framework is transferable to other regions.

Steps to follow:
1. Develop and validate a flood model. While OpenSafe Mobility uses HEC-RAS, any other software that can be managed by Python (or via an API) can be used.
2. Secure access to real-time rainfall data. Some options are radar (NEXRAD, OPERA), gage-adjusted rainfall radar, and gage data.
3. Acquire access to a web domain (e.g., using Google Domains), web hosting (e.g., using Amazon AWS), and a mapping framework (E.g., using Mapbox).
4. Collect additional data for roads (e.g., OpenStreetMap), location on critical facilities (e.g., HIFLD dataset), socio-demographic data (e.g., census data).
5. Clone the repository and create a Python environment using the [environment.yml](environment.yml/) file.
6. Modify the code to suit the study area. OpenSafe Mobility model parameters are stored in Hydra Config files ([configs](configs/)).

## Cost of Operation

1. Web domain - ~12/year ([Google Domains](https://domains.google)). Cheaper options are also available.
2. Web hosting - [Amazon AWS](https://aws.amazon.com/s3/pricing/?p=ft&c=wa&z=2). $0.0004/1000 requests.
3. Map framework - 
   1. [Mapbox](https://www.mapbox.com/pricing): Free (50k monthly loads); $250 (100k monthly loads); $1610 (500k monthly loads).
   2. [Leaflet](https://leafletjs.com/): Free and Open Source.
4. Radar data: Free (NEXARD) or gage-adjusted radar data (depends on the provider).
5. Flood model development: Regional flood models might be open source and free (e.g., [M3 System from Harris County Flood Control District](https://www.hcfcd.org/Resources/Interactive-Mapping-Tools/Model-and-Map-Management-M3-System)). Cost for custom flood models depends on several factors. 


## How to Obtain OpenSafe Mobility Code

Install dependencies

```bash
# clone project
git clone https://github.com/Pranavesh-Panakkal/OpenSafe-Mobility
cd OpenSafe-Mobility

# [OPTIONAL] create conda environment
conda env create --file environment.yml
conda activate opensafe_mobility
```

## REST API Access

To facilitate interoperability with existing tools, OpenSafe provides access to real-time results from the framework.

Real-time information on flooded roads:
```bash
https://bxx9umzruh.execute-api.us-east-1.amazonaws.com/default/opensafe_rest_api?key=flooded_roads.geojson
```

For flood impact on access to select critical facilities:

```bash
https://bxx9umzruh.execute-api.us-east-1.amazonaws.com/default/opensafe_rest_api?key=mobility.geojson
```

## License

TBD 

## Contact

Please contact Pranavesh Panakkal [pranavesh at rice.edu] or Dr. Jamie Ellen Padgett for more information.
