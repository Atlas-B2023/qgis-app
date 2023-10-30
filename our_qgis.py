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
canvas = iface.mapCanvas()
# canvas = QgsMapCanvas()
# canvas.setWindowTitle("My QGIS Map")
# canvas.setCanvasColor(Qt.white)

# Create a project
project = QgsProject.instance()
project.read()

# Set up a layer tree and bridge to the canvas
root = project.instance().layerTreeRoot()
bridge = QgsLayerTreeMapCanvasBridge(root, canvas)

# Load all layers
layers = []
scriptDirectory = os.path.dirname(os.path.abspath(__file__))
layersFolder = "layers/Metro_Zips"
folderDirectory = os.path.join(scriptDirectory, layersFolder)

for filename in os.listdir(folderDirectory):
    fullFile = folderDirectory + "/" + filename
    layer = QgsVectorLayer(fullFile, filename, "ogr")
    path, type = os.path.splitext(filename)
    
    if layer.isValid() and filename.endswith(".shp"):
        # Add the layer to the canvas
        layers.append(layer)
        project.instance().addMapLayer(layer)
        canvas.setExtent(layer.extent())
    elif filename.endswith(".shp"):
        print("Layer failed to load!")
        
# Custom map tool for identifying features
class IdentifyMapTool(QgsMapTool):
    def __init__(self, canvas, layers):
        super().__init__(canvas)
        self.layers = layers

    def canvasReleaseEvent(self, event):
        for layer in self.layers:
            identify = QgsMapToolIdentify(canvas)
            result = identify.identify(event.x(), event.y(), [layer], QgsMapToolIdentify.TopDownStopAtFirst)
            if result:
                for feat in result:
                    field_names = feat.mFeature.fields().names()
                    info = "\n".join([name + " " + str(feat.mFeature.attribute(name)) for name in field_names])
                    print(info)

# Set the custom identify map tool
identifyMapTool = IdentifyMapTool(canvas, layers)
canvas.setMapTool(identifyMapTool)
        
# Show the map canvas
canvas.show()

# Run the QGIS application event loop
qgs.exec_()