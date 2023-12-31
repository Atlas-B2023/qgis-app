# Setting up QGIS

## Installing QGIS

> [!NOTE]
> This document assumes that you are an Atlas analyst and have the .gbd files that were handed over at the end of our project. If this is not your case, you can try to follow along by using an OpenMapBox world map, a EPSG 4347 projection, and 3 layers: 1 being MSA blocks, the other being ZCTA blocks inside of these MSAs, and the last being state border shapefiles.

To install QGIS, head to their website [QGIS Download](https://qgis.org/en/site/forusers/download.html) and download version 3.34.1.
This can be installed anywhere on the device.

Once installed, head to `AppData\Roaming\QGIS\QGIS3\profiles\default` in your file explorer and delete the file called "symbology-style.db".

> [!TIP]
> To access AppData, search for "run" in the taskbar search bar, and click on the result.
> From there, type "%appdata%" and press enter.

Next, head over to the location of this project (`AtlasIQP2023\qgis-app\`) and unzip sample.zip.

Copy the file called "symbology-style.db" from this folder, and paste it in the location where you deleted the other one of the same name.

## Loading the Project

The base qgis project is provided in the folder `QGIS Map\`.

To load it, run QGIS and in the top left click "Project."

Navigate to this project folder, and open `QGIS Map\Electrification Tracker Base Map.qgz`.

### Extracting Sample Data

This project comes with sample data that can be used without running the scraper tool.

> [!NOTE]
> To get updated data, the scraper tool must be run.
> Data collected from running the scraper does not need to be loaded in the same way as the sample data.

To load the sample housing data, open `sample.zip` and copy all files with a numeric name (representing zip codes).

Create a new folder named "test", located at `ResidentialElectrificationTracker\output\metro_data\`, and paste in the copied files.

To load the sample demographic data, open `sample.zip` and copy the remaining unused files (typically starting with "acs5").

Create a new folder named "census_data", located at `ResidentialElectrificationTracker\output\`, and paste in the copied files.

### Running the Script

To run the scrip, load the base map qgis project.

Click on the python icon (The second from the right on the bottom row of the taskbar on the top of the screen):

<img src="https://upload.wikimedia.org/wikipedia/commons/thumb/c/c3/Python-logo-notext.svg/640px-Python-logo-notext.svg.png" width="100" height="100"> 

Next, in the python console that appears, click the Show Editor button (the third from the left that looks like a sheet of paper)

Then, click on the Open Script button (the left most icon) in the new window that appears.

From here, navigate to the script location `qgis-app\src\our_qgis.py` and click "Open."

Now run the script by clicking the green arrow icon in the script editor (fifth from the left).

> [!NOTE]
> For more information on how to use the program, please refer to the Video Tutorials here: [Atlas IQP QGIS Video Tutorials](link)

> [!WARNING]
> If the program crashes, just run again. If the program crashes more than three times, please open an issue on GitHub.

### Saving the Project

When saving the project, be sure to save it as a copy, as to not override the existing one.

It might be useful to create a backup of the project in the event the project is overridden.

### Closing the Project

When closing the project, there will be a couple pop-ups.

The first will ask if you would like to proceed in closing the project; click "Yes."

The second will ask if you would like to save the project; click "Discard."

### Why is it Freezing?

Creating the GeoPackage files creates a database. When QGIS goes to load information from these tables, it must run SQL operations. Each of the 33 tables in the Census GPKG database has about 23,000-ish entries, and each entry is about 15 kilobytes. This means that there will be a lot of CPU waiting time as this gets loaded in. If you find that this process takes an exceptionally long amount of time, you can try to crash QGIS by clicking profusely on the application. 

This is fine as the databases are saved independently of what the QGIS graphical user interface is doing. You can then create a new GeoPackage database connection to these saved databases in a fresh project, and play with the data there. More information is in the video tutorials.

## Development

> [!NOTE]
> This is just for furture development on this project. If you are not changing or adding to this project, you do not need to follow these steps.

### Setting Up System Environments

There are a few paths that need to be set up within the system environment. The following steps will guide you through how:

1. Within the taskbar search bar, search for environment variables and click on the one that says "Edit the systems environment variables."
2. In the bottom right of the popup, click "Environment Variables..."
3. In system variables, scroll down until you see "Path."
4. Click on it and click "Edit..."
5. Within this popup, click new and type the folder path to the QGIS download, bin (Likely `C:\Program Files\QGIS 3.34.1\bin`) then press enter.
6. Add another new path, but this time from QGIS3.34.1, go to apps, qgis, bin (`C:\Program Files\QGIS 3.34.1\apps\qgis\bin`) then press enter.
7. Click "OK."
8. Now scroll down until you see PYTHONPATH, click it and click "Edit..."
9. Type in the path from QGIS 3.34.1, apps, qgis, python (`C:\Program Files\QGIS 3.34.1\apps\qgis\python`) and click "OK."
10. Click "OK" again, then once more.

### Setting up Python

> [!NOTE]
> Your Python version does not affect the script when it is being ran in QGIS, as it comes packaged with its own Python (version 3.9). 

Steps:

1. Download Python 3.9. (Remember where you download it.)
2. Download this repository as a zip file
3. Un-zip the folder into your desired folder.
4. Make sure that this folder is adjacent in the file viewer to your QGIS project folder!
5. Run the included setup.bat script to create a virtual environment and install PyQt5! (When prompted, give the file path from step 1)