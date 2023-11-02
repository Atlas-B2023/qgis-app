from qgis.core import *
from qgis.gui import *
from qgis.utils import *
from PyQt5.QtCore import Qt
from PyQt5 import QtGui
import logging
from qgis.PyQt.QtGui import QColor

project_directory = os.path.dirname(QgsProject.instance().fileName())
parent_directory = os.path.dirname(project_directory)
log_file_path = os.path.join(parent_directory, 'qgisdebug.log')
logging.basicConfig(filename=log_file_path, level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize QGIS
QgsApplication.setPrefixPath("~/QGIS 3.32.3", True)
qgs = QgsApplication([], False)
qgs.initQgis()
logging.debug("Initialized QGIS")

# Create a project
project = QgsProject.instance()
project.read()

# Set up a layer tree
root = project.instance().layerTreeRoot()
logging.debug("Set up layer tree")

# Load all layers
layers = []
logging.debug("Layers list")

style = QgsStyle().defaultStyle()
ramp_names = style.colorRampNames()
print(ramp_names)

try:
    scriptDirectory = os.path.join(parent_directory, "qgis-app")
    folderDirectory = os.path.join(scriptDirectory, "layers")
except Exception as e:
    logging.exception("Exception occurred: " + str(e))

for fileName in os.listdir(folderDirectory):
    fullFile = folderDirectory + os.sep + fileName
    path, type = os.path.splitext(fileName)
    
    if fileName.endswith(".shp"):
        layer = QgsVectorLayer(fullFile, fileName, "ogr")
        # if layer.isValid():
        try:
            # Add the layer
            layers.append(layer)
            project.instance().addMapLayer(layer)
        except:
            logging.warning("Layer " + fileName + " failed to load!")
        logging.debug("Loaded .shp files")
        
    elif fileName.endswith(".csv"):
        layer = QgsVectorLayer("""Point?crs=EPSG:4326
                               &field=Address:string
                               &field=City:string
                               &field=State/Province:string
                               &field=Year-Built:string
                               &field=Zip/Postal:string
                               &field=Price:string
                               &field=Square-Feet:string
                               &field=Latitude:string
                               &field=Longitude:string
                               &field=Solar-Heating:string
                               &field=Furnace:string
                               &field=Natural-Gas:string
                               &field=Propane:string
                               &field=Diesel:string
                               &field=Heating-Oil:string
                               &field=Wood/Pellet:string
                               &field=Electric:string
                               &field=Heat-Pump:string
                               &field=Baseboard:string
                               &field=Swamp-Coolers:string
                               &field=Radiant-Floor:string""", "locations", "memory")
        prov = layer.dataProvider()
        fields = prov.fields()
        feats = []
        with open(fullFile) as f:
            lines = f.read().splitlines()
            for line in lines[1:]:
                address, city, state, year, zipcode, price, sqrft, lat, lon, solar, furnace, ng, propane, diesel, oil, wood, electric, hp, baseboard, sc, rf = line.split(",")
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
                feat["Solar-Heating"] = solar
                feat["Furnace"] = furnace
                feat["Natural-Gas"] = ng
                feat["Propane"] = propane
                feat["Diesel"] = diesel
                feat["Heating-Oil"] = oil
                feat["Wood/Pellet"] = wood
                feat["Electric"] = electric
                feat["Heat-Pump"] = hp
                feat["Baseboard"] = baseboard
                feat["Swamp-Coolers"] = sc
                feat["Radiant-Floor"] = rf
                feats.append(feat)
        prov.addFeatures(feats)
        layer.setCrs(QgsCoordinateReferenceSystem('EPSG:4326'))
        
        logging.debug("Created prov")
        
        #  if layer.isValid():
        try:
            attributes = ["Solar-Heating",
                          "Furnace",
                          "Natural-Gas",
                          "Propane",
                          "Diesel",
                          "Heating-Oil",
                          "Wood/Pellet",
                          "Electric",
                          "Heat-Pump",
                          "Baseboard",
                          "Swamp-Coolers",
                          "Radiant-Floor"]
            
            for attribute_name in attributes:
                heatmap_layer = QgsVectorLayer("Point?crs=EPSG:4326", f"Heatmap - {attribute_name}", "memory")
                heatmap_provider = heatmap_layer.dataProvider()
                
                color_ramp = QgsStyle().defaultStyle().colorRamp('Blues')
                
                heatmap_renderer = QgsHeatmapRenderer()
                heatmap_renderer.setWeightExpression('1')
                heatmap_renderer.setRadius(10)
                heatmap_renderer.setColorRamp(color_ramp)
                
                new_feats = []
                for feat in prov.getFeatures():
                    lat = feat['Latitude']
                    lon = feat['Longitude']
                    try:
                        if feat[attribute_name] == "true":
                            value = 1.0
                        elif feat[attribute_name] == "false":
                            value = 0.0
                        else:
                            value = float(feat[attribute_name])
                    except:
                        print(feat[attribute_name])
                    
                    # new_feat = QgsFeature()
                    # new_feat.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(float(lon), float(lat))))
                    if value > 0:
                        new_feats.append(feat)
                
                heatmap_provider.addFeatures(new_feats)
                heatmap_layer.setRenderer(heatmap_renderer)
                
                
                # Add the heatmap layer to the Layer Tree
                root = QgsProject.instance().layerTreeRoot()
                root.insertChildNode(0, QgsLayerTreeLayer(heatmap_layer))

                # Display the heatmap
                # layer.triggerRepaint()
                layers.append(heatmap_layer)
                
                logging.debug("Added csv as layer")
            root.insertChildNode(0, QgsLayerTreeLayer(layer))
        except Exception as e:
            logging.warning("Layer " + fileName + " failed to load!")
            logging.warning(e)

# Run the QGIS application event loop
qgs.exec_()
logging.debug("Last one")