from qgis.core import *
from qgis.gui import *
from qgis.utils import *
from PyQt5.QtCore import Qt


# Initialize QGIS
QgsApplication.setPrefixPath("C:/Program Files/QGIS 3.32.3", True)
qgs = QgsApplication([], False)
qgs.initQgis()

# Create a map canvas
canvas = QgsMapCanvas()
canvas.setWindowTitle("My QGIS Map")
canvas.setCanvasColor(Qt.white)


# Load a vector layer
layer_path = "C:/School/Junior/B Term/IQP/redfinapi/qgislayers/test.qlr"
layer = QgsVectorLayer(layer_path, "My Layer", "ogr")
if not layer.isValid():
    print("Layer failed to load!")
else:
    # Add the layer to the canvas
    QgsProject.instance().addMapLayer(layer)
    canvas.setExtent(layer.extent())

# Set up a layer tree and bridge to the canvas
root = QgsProject.instance().layerTreeRoot()
bridge = QgsLayerTreeMapCanvasBridge(root, canvas)
root.addLayer(layer)

# Show the map canvas
canvas.show()

# Run the QGIS application event loop
qgs.exec_()