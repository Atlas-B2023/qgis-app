# Setting up QGIS
## Installing QGIS
To install QGIS, head to their website [QGIS Download](https://qgis.org/en/site/forusers/download.html) and download version 3.34.0.
This can be installed anywhere on the device.
Once installed, head to AppData\Roaming\QGIS\QGIS3\profiles\default in your file explorer and delete the file called "symbology-style.db".
Next, head over to the locagtion of this project and unzip sample.zip.
Copy the file called symbology-style.db from this folder, and paste it in the location where you deleted the other one of the same name.


## Setting up System Environments
[!NOTE]
This is just for development. If you are not changing or adding to this project, you do not need to follow these steps.

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