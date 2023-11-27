# Setting up QGIS
## Installing QGIS
To install QGIS, head to their website [QGIS Download](https://qgis.org/en/site/forusers/download.html) and download version 3.34.0.
This can be installed anywhere on the device.

Once installed, head to AppData\Roaming\QGIS\QGIS3\profiles\default in your file explorer and delete the file called "symbology-style.db".

Next, head over to the locagtion of this project and unzip sample.zip.

Copy the file called symbology-style.db from this folder, and paste it in the location where you deleted the other one of the same name.

## Loading the Project
The base qgis project is provided within this program.

To load it, run QGIS and in the top left click "Project."

Navigate to this project file, and go to QGIS Map\Electrification Tracker Base Map.qgz.

### Extracting Sample Data
This project comes with sample data that can be run without running the scraper tool.

>[!NOTE]
>To get updated data, the scraper tool must be run.
>Data collected from running the scraper does not need to be loaded in the same way as the sample data.

To load the sample housing data, head to the sample folder and copy all files with a numeric name (representing zip code).

Paste these files in the housing folder located at qgis-app\layers\housing (this will cahnge).

To load the sample demographic data, heat to the sample folder and copy the reamining unused files (typically starting with "acs5").

Paste these files in the demographic folder located at qgis-app\layers\demographic (this will change).

### Running the Script
To run the scrip, load the base map qgis project.

Click on the python symbol (The second from the right on the bottom row of the taskbar on the top of the sscreen).

Next, in the python console that appears, click the Show Editor button (the third from the left that looks like a sheet of paper)

Then, click on the Open Script button (the left most icon) in the new window that appears.

From here, navigate to the script location qgis-app\src\our_qgis.py and click "Open."

Now run the script by clicking the green arrow icon in the script editor (fifth from the left).

>[!NOTE]
>For more information on how to use the program, please refer to the Video Tutorials here: [Atlas IQP QGIS Video Tutorials](link)


## Development
>[!NOTE]
>This is just for furture development on this project. If you are not changing or adding to this project, you do not need to follow these steps.

### Setting Up System Environments
There are a few paths that need to be set up within the system environment. The following steps will guide you through how:
1. Within the taskbar seach bar, search for environment variables and click on the one that says "Edit the systems environment variables."
2. In the bottom right of the popup, click "Environment Variables..."
3. In system variables, scroll down until you see "Path."
4. Click on it and click "Edit..."
5. Within this popup, click new and type the folder path to the QGIS download, bin (Likely C:\Program Files\QGIS 3.34.0\bin) then press enter.
6. Add another new path, but this time from QGIS3.34.0, go to apps, qgis, bin (C:\Program Files\QGIS 3.34.0\apps\qgis\bin) then press enter.
7. Click "OK."
8. Now scroll down until you see PYTHONPATH, click it and click "Edit..."
9. Type in the path from QGIS 3.34.0, apps, qgis, python (C:\Program Files\QGIS 3.34.0\apps\qgis\python) and click "OK."
10. Click "OK" again, then once more.