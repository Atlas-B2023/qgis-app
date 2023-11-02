from qgis.core import *
from qgis.gui import *
from qgis.utils import *
from PyQt5.QtCore import Qt
from PyQt5 import QtGui
import logging

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
try:
    scriptDirectory = os.path.join(parent_directory, "qgis-app")
    logging.debug("Script directory")
    folderDirectory = os.path.join(scriptDirectory, "layers")
    logging.debug("Folder directory")
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
        # else:
        #     print("Layer " + fileName + " failed to load!")
        logging.debug("Loaded .shp files")
    elif fileName.endswith(".csv"):
        layer = QgsVectorLayer("Point?crs=EPSG:4326&field=Address:string&field=City:string&field=State/Province:string&field=Year-Built:string&field=Zip/Postal:string&field=Price:string&field=Square-Feet:string&field=Latitude:string&field=Longitude:string&field=Heating-Amenities:string", "locations", "memory")
        # layer = QgsVectorLayer("""Point?crs=EPSG:4326
        #                        &field=Address:string
        #                        &field=City:string
        #                        &field=State/Province:string
        #                        &field=Year-Built:string
        #                        &field=Zip/Postal:string
        #                        &field=Price:string
        #                        &field=Square-Feet:string
        #                        &field=Latitude:string
        #                        &field=Longitude:string
        #                        &field=Solar-Heating:string
        #                        &field=Natrual-Gas:string
        #                        &field=Propane:string
        #                        &field=Diesel:string
        #                        &field=Heating-Oil:string
        #                        &field=Wood/Pellet:string
        #                        &field=Electric:string
        #                        &field=Heat-Pump:string
        #                        &field=Baseboard:string""", "locations", "memory")
        prov = layer.dataProvider()
        fields = prov.fields()
        feats = []
        with open(fullFile) as f:
            lines = f.read().splitlines()
            for line in lines[1:]:
                address, city, state, year, zipcode, price, sqrft, lat, lon, amen = line.split(",")
                # address, city, state, year, zipcode, price, sqrft, lat, lon, solar, ng, propane, diesel, oil, wood, electric, hp, baseboard = line.split(",")
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
                feat["Heating-Amenities"] = amen
                # feat["Solar-Heating"] = solar
                # feat["Natrual-Gas"] = ng
                # feat["Propane"] = propane
                # feat["Diesel"] = diesel
                # feat["Heating-Oil"] = oil
                # feat["Wood/Pellet"] = wood
                # feat["Electric"] = electric
                # feat["Heat-Pump"] = hp
                # feat["Baseboard"] = baseboard
                feats.append(feat)
        prov.addFeatures(feats)
        
        logging.debug("Created prov")
        
        #  if layer.isValid():
        try:
            attributes = ["Year-Built"
                        #   ,"Solar-Heating",
                        #   "Natural-Gas",
                        #   "Propane",
                        #   "Diesel",
                        #   "Heating-Oil",
                        #   "Wood/Pellet",
                        #   "Electric",
                        #   "Heat-Pump",
                        #   "Baseboard",
                          ]
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
                        if feat[attribute_name] == "Yes":
                            value = 1
                        elif feat[attribute_name] == "No":
                            value = 0
                        else:
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

                # Display the heatmap
                layer.triggerRepaint()
                layers.append(layer)
                
                logging.debug("Added csvs as layers")
            root.insertChildNode(0, QgsLayerTreeLayer(layer))
        except:
            logging.warning("Layer " + fileName + " failed to load!")
        # else:
        #     print("Layer " + fileName + " failed to load!")

# Run the QGIS application event loop
qgs.exec_()
logging.debug("Last one")