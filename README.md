
# Scratch Assay Monitoring Simulation

## Overview

This project is a software simulation of an automated
scratch assay monitoring device developed as part of
a Biomedical Engineering capstone project at the
University of the West Indies, Mona.

The proposed device will monitor cancer cell migration
and evaluate the effects of Jamaican and Turkish
propolis using scratch assays.

## Simulation Features

- Simulated LED illumination control
- Automated image acquisition using sample images
- Timestamped image storage
- Automated scratch detection using OpenCV
- Scratch area and average width measurements
- Straight boundary line visualization
- Percentage scratch closure calculation
- Automated CSV results generation
- Scratch closure graphs
- Separate experiment folders for data management

## Technologies Used

- Python
- OpenCV
- NumPy
- Matplotlib

## Installation

Install the required dependencies:

pip install -r requirements.txt

## Running the Simulation

Run the main program:

python main.py

The simulation uses three sample scratch assay images
representing 0, 12 and 24 hours. Shortened capture
intervals are used to demonstrate automated operation.

## Project Structure

- main.py: Automated experiment simulation
- scratch_analysis.py: Image processing and analysis
- sample_images/: Input microscopy images
- captured_images/: Simulated captured images
- processed_images/: Annotated scratch assay images
- results/: CSV measurements and graphs

## Limitations

This simulation uses existing microscopy images rather
than a physical camera. LED illumination is represented
through software commands.

The scratch detection algorithm requires further
validation using experimental images.

## Future Development

- Raspberry Pi Zero and HQ camera integration
- Physical LED illumination control
- Automated hourly image acquisition
- Azure cloud storage integration
- Remote monitoring web application
- Experimental validation
