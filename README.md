# Transwell Image Processing Scripts
[![DOI](https://zenodo.org/badge/1272666693.svg)](https://doi.org/10.5281/zenodo.20741673)

## Description
This repository contains the scripts used for the automated processing, compositing, and visualization of transwell microscopy images from my Bachelor Thesis. 

## Repository Overview
The repository is structured into three modules:

* **ImageJ script/Image_Processing_V1.ijm**: An ImageJ macro that automates the batch processing of subdirectories. It locates DAPI, ZO1, and OCCL channel images, applies background subtraction and contrast enhancement, and merges them into a multi-channel composite TIFF and PNG (`Merged_Composite.png`).
* **Image grid maker/image_merger.py**: A Python script that searches within a structured directory hierarchy to locate images and stitches them into a 2x2 composite grid.
* **Image grid maker/image_merger_finals.py**: Same thing, but a bit more flexible.
* **Slides viewer/streamlit_app.py**: A Streamlit-based interactive web application that uses `data_indexer.py` to provide a searchable, filterable gallery interface for comparative analysis of the generated composites across multiple conditions, concentrations, and time points.

## Setup & Installation

To run the Python scripts in this repository, it is recommended to use a Python virtual environment to isolate dependencies. Activate the virtual environment, then install the packages listed in `requirements.txt`

## Usage

### 1. ImageJ Batch Processing
This script was designed and run within FIJI Stable Version 2026/03/07-1417
Execute the macro within ImageJ/Fiji:
1. Open ImageJ/Fiji.
2. Navigate to `Plugins > Macros > Run...` and select `Image_Processing_V1.ijm`.
3. Choose the root directory containing your raw image subfolders when prompted.

### 2. Generating Image Grids
Ensure your virtual environment is active. Navigate to the grid maker directory and execute the script:
```bash
cd "Image grid maker"
python image_merger.py
```
*Note: The script currently targets the current directory (`.`). Adjust the `TARGET_DIRECTORY` variable in the source code if necessary.*

### 3. Running the Slides Viewer Application
Ensure your virtual environment is active. Navigate to the slides viewer directory and launch the Streamlit application:
```bash
cd "Slides viewer"
streamlit run streamlit_app.py
```
This command will start a local web server and open the interactive viewer in your default web browser.
