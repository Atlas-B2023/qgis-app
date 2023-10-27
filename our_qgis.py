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

"""# Create a QgsDataSourceUri to specify the WMS connection
uri = QgsDataSourceUri()
uri.setParam("url", zctaArcGISMap)

# Create a new QgsRasterLayer based on the WMS connection
aGISLayer = QgsRasterLayer(uri.uri(), "ArcGIS Base Map", "wms")"""

# uri = QgsDataSourceUri()
# uri.setParam('crs', 'EPSG:3857')
# uri.setParam('url', 'https://services2.arcgis.com/FiaPA4ga0iQKduv3/ArcGIS/rest/services/Census_ZIP_Code_Tabulation_Areas_2010_v1/FeatureServer/0')

# alayer = QgsVectorLayer(uri.uri(), "Test Layer" , 'arcgisfeatureserver')
# alayer.setSubsetString('"classsubtype" = 12')
# if alayer.isValid():
#     QgsProject.instance().addMapLayer(alayer)
# else:
#     print('Invalid layer: failed to add layer')
# print("Past here")
# # Add the layer to the current project
# #project.instance().addMapLayer(aGISLayer)

# # Set up a layer tree and bridge to the canvas
# root = project.instance().layerTreeRoot()
# bridge = QgsLayerTreeMapCanvasBridge(root, canvas)
# root.addLayer(alayer)

arcgis_layer = QgsRasterLayer('https://services2.arcgis.com/FiaPA4ga0iQKduv3/ArcGIS/rest/services/Census_ZIP_Code_Tabulation_Areas_2010_v1/FeatureServer/0', "ArcGIS Map", "wms", QgsRasterLayer.LayerOptions(True))
print(QgsRasterLayer.LayerOptions.loadDefaultStyle)

# Check if the layer was loaded successfully
if not arcgis_layer.isValid():
    print("Failed to load ArcGIS layer")
else:
    # Add the layer to the current QGIS project
    QgsProject.instance().addMapLayer(arcgis_layer)

    # Show the layer in the Layers Panel
    root = QgsProject.instance().layerTreeRoot()
    layer = root.addLayer(arcgis_layer)

    # Set the extent to the full extent of the layer
    iface.mapCanvas().setExtent(arcgis_layer.extent())

    # Refresh the map canvas
    iface.mapCanvas().refresh()

# Load all layers
# layers = []
# scriptDirectory = os.path.dirname(os.path.abspath(__file__))
# layersFolder = "layers/qgis_sample_data/shapefiles"
# folderDirectory = os.path.join(scriptDirectory, layersFolder)

# for filename in os.listdir(folderDirectory):
#     fullFile = folderDirectory + "/" + filename
#     layer = QgsVectorLayer(fullFile, filename, "ogr")
#     path, type = os.path.splitext(filename)
    
#     if layer.isValid() and filename.endswith(".shp"):
#         # Add the layer to the canvas
#         #layers.add(layer)
#         project.instance().addMapLayer(layer)
#         canvas.setExtent(layer.extent())
#     elif filename.endswith(".shp"):
#         print("Layer failed to load!")
        
# Show the map canvas
canvas.show()

# Run the QGIS application event loop
qgs.exec_()