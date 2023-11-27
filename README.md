# Setting up QGIS
## Installing QGIS
To install QGIS, head to their website [QGIS Download](https://qgis.org/en/site/forusers/download.html) and download version 3.34.1.
This can be installed anywhere on the device.

Once installed, head to `AppData\Roaming\QGIS\QGIS3\profiles\default` in your file explorer and delete the file called "symbology-style.db".

>[!INFO]
>To access AppData, search for "run" in the taskbar search bar, and click on the result.
>From there, type "%appdata%" and press enter.

Next, head over to the location of this project (`AtlasIQP2023\qgis-app\`) and unzip sample.zip.

Copy the file called "symbology-style.db" from this folder, and paste it in the location where you deleted the other one of the same name.

## Loading the Project
The base qgis project is provided in the folder `QGIS Map\`.

To load it, run QGIS and in the top left click "Project."

Navigate to this project folder, and open `QGIS Map\Electrification Tracker Base Map.qgz`.

### Extracting Sample Data
This project comes with sample data that can be used without running the scraper tool.

>[!NOTE]
>To get updated data, the scraper tool must be run.
>Data collected from running the scraper does not need to be loaded in the same way as the sample data.

To load the sample housing data, open `sample.zip` and copy all files with a numeric name (representing zip codes).

Create a new folder named "test", located at `ResidentialElectrificationTracker\output\metro_data\`, and paste in the copied files.

To load the sample demographic data, open `sample.zip` and copy the reamining unused files (typically starting with "acs5").

Create a new folder named "census_data", located at `ResidentialElectrificationTracker\output\`, and paste in the copied files.

### Running the Script
To run the scrip, load the base map qgis project.

Click on the python icon ![Python logo](https://upload.wikimedia.org/wikipedia/commons/thumb/c/c3/Python-logo-notext.svg/640px-Python-logo-notext.svg.png =250x250) (The second from the right on the bottom row of the taskbar on the top of the screen).

Next, in the python console that appears, click the Show Editor button (the third from the left that looks like a sheet of paper)

Then, click on the Open Script button (the left most icon) in the new window that appears.

From here, navigate to the script location `qgis-app\src\our_qgis.py` and click "Open."

Now run the script by clicking the green arrow icon in the script editor (fifth from the left).

>[!NOTE]
>For more information on how to use the program, please refer to the Video Tutorials here: [Atlas IQP QGIS Video Tutorials](link)

>[!WARNING]
>If the program crashes, just run again. If the program crashes more than three times, please open an issue on GitHub.

### Saving the Project
When saving the project, be sure to save it as a copy, as to not override the existing one.

It might be useful to create a backup of the project in the event the project is overriden.

### Closing the Project
When closing the project, there will be a couple pop-ups.

The first will ask if you would like to proceed in closing the project; click "Yes."

The second will ask if you would like to save the project; click "Discard."


## Development
>[!NOTE]
>This is just for furture development on this project. If you are not changing or adding to this project, you do not need to follow these steps.

### Setting Up System Environments
There are a few paths that need to be set up within the system environment. The following steps will guide you through how:
1. Within the taskbar seach bar, search for environment variables and click on the one that says "Edit the systems environment variables."
2. In the bottom right of the popup, click "Environment Variables..."
3. In system variables, scroll down until you see "Path."
4. Click on it and click "Edit..."
5. Within this popup, click new and type the folder path to the QGIS download, bin (Likely `C:\Program Files\QGIS 3.34.1\bin`) then press enter.
6. Add another new path, but this time from QGIS3.34.1, go to apps, qgis, bin (`C:\Program Files\QGIS 3.34.1\apps\qgis\bin`) then press enter.
7. Click "OK."
8. Now scroll down until you see PYTHONPATH, click it and click "Edit..."
9. Type in the path from QGIS 3.34.1, apps, qgis, python (`C:\Program Files\QGIS 3.34.1\apps\qgis\python`) and click "OK."
10. Click "OK" again, then once more.