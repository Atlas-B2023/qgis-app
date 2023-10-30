from qgis.core import *
from qgis.gui import *
from qgis.utils import *
from PyQt5.QtCore import Qt
from pathlib import Path
import numpy

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
layersFolder = "layers"
folderDirectory = os.path.join(scriptDirectory, layersFolder)

for fileName in os.listdir(folderDirectory):
    fullFile = folderDirectory + "/" + fileName
    path, type = os.path.splitext(fileName)
    
    if fileName.endswith(".shp"):
        layer = QgsVectorLayer(fullFile, fileName, "ogr")
        if layer.isValid():
            # Add the layer to the canvas
            layers.append(layer)
            project.instance().addMapLayer(layer)
            canvas.setExtent(layer.extent())
        else:
            print("Layer " + fileName + " failed to load!")
    elif fileName.endswith(".csv"):
        data = numpy.loadtxt(fullFile, dtype=str, delimiter=",", skiprows=1)
        uri = 'file:///' + fullFile + "?delimiter=,&yField={}&xField={}".format('LATITUDE', 'LONGITUDE')
        vl = QgsVectorLayer(uri, fileName, 'delimitedtext')
        if vl.isValid():
            QgsProject.instance().addMapLayer(vl)
            for r in data:
                f = QgsFeature(vl.fields())
                f['LATITUDE'] = float(r[7])
                f['LONGITUDE'] = float(r[8])
                
                geom = QgsGeometry.fromPointXY(QgsPointXY(float(r[7]), float(r[8])))
                f.setGeometry(geom)
                vl.dataProvider().addFeatures([f])
                
            vl.updateExtents()
            layers.append(vl)
        else:
            print("Layer " + fileName + " failed to load!")
    elif fileName.endswith(".shp") or fileName.endswith(".csv"):
        print("Layer " + fileName + " failed to load!")
        
# # Custom map tool for identifying features
# class IdentifyMapTool(QgsMapTool):
#     def __init__(self, canvas, layers):
#         super().__init__(canvas)
#         self.layers = layers

#     def canvasReleaseEvent(self, event):
#         for layer in self.layers:
#             identify = QgsMapToolIdentify(canvas)
#             result = identify.identify(event.x(), event.y(), [layer], QgsMapToolIdentify.TopDownStopAtFirst)
#             if result:
#                 for feat in result:
#                     field_names = feat.mFeature.fields().names()
#                     info = "\n".join([name + " " + str(feat.mFeature.attribute(name)) for name in field_names])
#                     print(info)

# Set the custom identify map tool
# identifyMapTool = IdentifyMapTool(canvas, layers)
# canvas.setMapTool(identifyMapTool)
# iface.actionIdentify().trigger()
# identifyMapTool = IdentifyMapTool(canvas, layers)
        
# Show the map canvas
canvas.show()

# Run the QGIS application event loop
qgs.exec_()