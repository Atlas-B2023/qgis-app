from qgis.core import *
from qgis.gui import *
from qgis.utils import *
from PyQt5.QtCore import Qt
from pathlib import Path

# Variables
zctaArcGISMap = "https://services2.arcgis.com/FiaPA4ga0iQKduv3/arcgis/rest/services/Census_ZIP_Code_Tabulation_Areas_2010_v1/FeatureServer"




# Initialize QGIS
QgsApplication.setPrefixPath("~/QGIS 3.32.3", True)
qgs = QgsApplication([], False)
qgs.initQgis()

# Create a map canvas
canvas = QgsMapCanvas()
canvas.setWindowTitle("My QGIS Map")
canvas.setCanvasColor(Qt.white)

# Create a project
project = QgsProject.instance()
project.read()

# Load a all layers
layers = []
scriptDirectory = os.path.dirname(os.path.abspath(__file__))
layersFolder = "layers"
folderDirectory = os.path.join(scriptDirectory, layersFolder)

for filename in os.listdir(folderDirectory):
    layer = QgsVectorLayer(os.path.abspath(filename), Path(filename).stem, "ogr")
    if not layer.isValid():
        print("Layer failed to load!")
    else:
        # Add the layer to the canvas
        layers.add(layer)
        project.instance().addMapLayer(layer)
        canvas.setExtent(layer.extent())

# Create a QgsDataSourceUri to specify the WMS connection
uri = QgsDataSourceUri()
uri.setParam("url", zctaArcGISMap)

# Create a new QgsRasterLayer based on the WMS connection
layer = QgsRasterLayer(uri.uri(), "ArcGIS Base Map", "wms")

# Add the layer to the current project
project.instance().addMapLayer(layer)

# Set up a layer tree and bridge to the canvas
root = project.instance().layerTreeRoot()
bridge = QgsLayerTreeMapCanvasBridge(root, canvas)
root.addLayer(layer)



# Show the map canvas
canvas.show()

# Run the QGIS application event loop
qgs.exec_()