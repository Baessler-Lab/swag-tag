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

1. Clone both this repository and move to its new directory
   ```
   git clone https://github.com/Baessler-Lab/swag-tag.git
   cd swag-tag
   ```
2. Create a new conda environment using the environment.yml provided in the repo (change "myenv" to a name of your choice) and activate it
    ```
   conda env create -f environment.yml --name swag-tag 
   activate swag-tag
   ```
3. Move to upper directory and clone the dicom-base repo
   ```
      cd ..
      git clone https://github.com/Baessler-Lab/dicom-base.git
   ```
4. Install the package using pip 
    ```
    pip install -e dicom-base
    ```
5. Finally, move to the swag-tag directory and install the remaining packages 
    ```
    cd swag-tag
    pip install -r requirements.txt
    ```
## Configuration
The configuration is stored under `swagtag/config/config.yaml`. Change the settings (e.g. directories) to your needs.
   
## Run
Make sure to export the `src`-directory: `swagtag` and the `root`-directory to your `PYTHONPATH` environment.

You can run the streamlit application by running 
```
python -m streamlit run "/ABSOLUTE/PATH/TO/swag-tag/swagtag/main.py"
--server.fileWatcherType none
--server.port 8510
--server.enableCORS false
--server.enableXsrfProtection false
--server.enableWebsocketCompression false
--server.baseUrlPath "/swag-tag"
```
in your virtual environment/conda environment.
