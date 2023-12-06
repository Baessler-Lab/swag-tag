# swag-tag: A Streamlit-based webapp for annotation of medical images and reports

Swag-Tag is a web application built using Streamlit that enables efficient annotation of medical images
and reports via tagging. The reports and scans as well as the added tags are all saved in a postgres database.

## Features

Current features are:

- Displaying a report-scan combination from the database
    - If multiple scans are present, they are displayed vertically (below each other)
    - Reports are displayed divided into several categories like "Examination" and "Findings"
- Setting min and max values for windowing X-Ray DICOMs
- Moving between slices along the z-axis for 3D-scans (e.g. CT)
- Adding tags to the current case
    - Several pathologies and findings with finer specifications are currently available
    - Additionally, severity for action can be added as a tag
    - Side of an annotation and a multiple heights (corresponding to upper, middle, and lower field of the lung
- Moving between dataset cases and specifying a case to jump directly to it
- Previous annotations are loaded directly into the case.
- loading and saving user configurations

## Installation

Follow this step-by-step guide to install the project on your local system. We firmly recommend using conda on Linux
since one of the required packages, psycopg2, has bugs regarding system-level libraries when installed via pip.

1. Clone this repository
   ```
   git clone https://github.com/Baessler-Lab/swag-tag.git
   cd swag-tag
   ```
2. Make sure that the volumes (e.g. mimic files and templates) point to the right place on host system
Make sure that a postgres image

## Configuration
The configuration is stored under `swagtag/config/config.yaml`. Change the settings (e.g. directories) to your needs.
1. Make sure that the volumes (e.g. mimic files and templates) point to the right place on host system

2. Make sure that a postgres image runs in the docker container (or separate host) 
defined in `docker/config/db_config.yaml`

   
## Run as a docker container
1. build and deploy docker container.
   ```
   cd docker
   docker compose up -d
   ```


# (deprecated) 
2. Create a new conda environment using the environment.yml provided in the repo and activate it
```
conda env create -f environment.yml
conda activate swag-tag

   ```
## Configuration
The configuration is stored under `swagtag/config/config.yaml`. Change the settings (e.g. directories) to your needs.
   
## Run (on host)
You can run the streamlit application by running 
```

bash start-app.sh

```


