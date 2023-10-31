from qgis.core import *
from qgis.gui import *
from qgis.utils import *
from PyQt5.QtCore import Qt
from PyQt5 import QtGui
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
layersFolder = "layers"
folderDirectory = os.path.join(scriptDirectory, layersFolder)

for fileName in os.listdir(folderDirectory):
    fullFile = folderDirectory + os.sep + fileName
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
        layer = QgsVectorLayer("Point?crs=EPSG:4326&field=Address:string&field=City:string&field=State/Province:string&field=Year-Built:string&field=Zip/Postal:string&field=Price:string&field=Square-Feet:string&field=Latitude:string&field=Longitude:string&field=Heat-Amenities:string", "locations", "memory")
        prov = layer.dataProvider()
        fields = prov.fields()
        feats = []
        with open(fullFile) as f:
            lines = f.read().splitlines()
            for line in lines[1:]:
                address, city, state, year, zipcode, price, sqrft, lat, lon, heatAmen = line.split(",")
                feat = QgsFeature(fields)
                feat.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(float(lon), float(lat))))
                feat["Address"] = address
                feat["City"] = city
                feat["State/Province"] = state
                feat["Year-Built"] = year
                feat["Zip/Postal"] = zipcode
                feat["Price"] = price
                feat["Square-Feet"] = sqrft
                feat["Latitude"] = lat
                feat["Longitude"] = lon
                feat["Heat-Amenities"] = heatAmen
                feats.append(feat)
        prov.addFeatures(feats)
        
        if layer.isValid():
            attributes = ["Year-Built",
                          "Price",
                          "Square-Feet"]
            for attribute_name in attributes:
                heatmap_layer = QgsVectorLayer("Point?crs=EPSG:4326", f"Heatmap - {attribute_name}", "memory")
                heatmap_provider = heatmap_layer.dataProvider()
                
                heatmap_renderer = QgsHeatmapRenderer()
                heatmap_renderer.setWeightExpression('1')
                heatmap_renderer.setRadius(10)
                heatmap_renderer.setColorRamp(QgsStyle().defaultStyle().colorRamp('Red to Green'))
                
                feats = []
                for feat in prov.getFeatures():
                    lat = feat['Latitude']
                    lon = feat['Longitude']
                    try:
                        value = float(feat[attribute_name])
                    except:
                        print(feat[attribute_name])
                    
                    new_feat = QgsFeature()
                    new_feat.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(float(lon), float(lat))))
                    if value > 0:
                        feats.append(new_feat)
                
                heatmap_provider.addFeatures(feats)
                heatmap_layer.setRenderer(heatmap_renderer)
                
                # Add the heatmap layer to the Layer Tree
                root = QgsProject.instance().layerTreeRoot()
                root.insertChildNode(0, QgsLayerTreeLayer(heatmap_layer))

                # Refresh the map canvas to display the heatmap
                layer.triggerRepaint()
                layers.append(layer)
                canvas.refresh()
        else:
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