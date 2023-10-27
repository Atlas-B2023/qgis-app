from qgis.core import *
from qgis.gui import *
from qgis.utils import *
from PyQt5.QtCore import Qt
from pathlib import Path

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

root = project.instance().layerTreeRoot()
bridge = QgsLayerTreeMapCanvasBridge(root, canvas)

# Load all layers
layers = []
scriptDirectory = os.path.dirname(os.path.abspath(__file__))
layersFolder = "layers/qgis_sample_data/shapefiles"
folderDirectory = os.path.join(scriptDirectory, layersFolder)

for filename in os.listdir(folderDirectory):
    fullFile = folderDirectory + "/" + filename
    layer = QgsVectorLayer(fullFile, filename, "ogr")
    path, type = os.path.splitext(filename)
    
    if layer.isValid() and filename.endswith(".shp"):
        # Add the layer to the canvas
        #layers.add(layer)
        project.instance().addMapLayer(layer)
        canvas.setExtent(layer.extent())
    elif filename.endswith(".shp"):
        print("Layer failed to load!")
        
# Show the map canvas
canvas.show()

# Run the QGIS application event loop
qgs.exec_()