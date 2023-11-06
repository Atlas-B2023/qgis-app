from qgis.core import *
from qgis.gui import *
from qgis.utils import *
from PyQt5.QtCore import Qt
from qgis.PyQt.QtGui import QColor
import logging
import csv
import typing
import itertools
import traceback
from PyQt5.QtCore import QVariant

# Grab the directory of the qgis project and parent folder of the project
project_directory = os.path.dirname(QgsProject.instance().fileName())
parent_directory = os.path.dirname(project_directory)

# Set up project log file
log_file_path = os.path.join(parent_directory, 'qgisdebug.log')
logging.basicConfig(filename=log_file_path, level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logging.info("========================================================================")

# Attempt to retrieve the path to the qgis-app and layers folders
try:
    scriptDirectory = os.path.join(parent_directory, "qgis-app")
    folderDirectory = os.path.join(scriptDirectory, "layers")
except Exception as e:
    logging.exception("Exception occurred: " + str(e))

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

# Used to create a point layer from csv data
def createCSVLayers(file_path: str, fields: QgsFields, feats: typing.List[str], headers: typing.List[str], layer: QgsVectorLayer) -> QgsVectorDataProvider:
    with open(file_path) as f:
        lines = f.read().splitlines()
        
        for line in lines[1:]:
            values = line.split(',')
            feat = QgsFeature(fields)
            feat.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(float(values[headers.index("LONGITUDE")]), float(values[headers.index("LATITUDE")]))))
            try:
                for header, csv_value in zip(headers, values):
                    feat[header] = csv_value
            except Exception as e:
                logging.error(str(e))
            feats.append(feat)
    prov.addFeatures(feats)
    layer.setCrs(QgsCoordinateReferenceSystem('EPSG:4326'))
    logging.debug("Created prov")
    return prov

# Used to create heatmap layers from csv heating data
def createHeatingHeatmapLayers(prov: QgsVectorDataProvider, attributes: typing.List[str]) -> None:
    
    heating = QgsLayerTreeGroup()
    heating.setName("Heating Types")
    
    # Create a heatmap layer for each attribute in heating_attributes
    for attribute_name in attributes:
        heatmap_layer = QgsVectorLayer("Point?crs=EPSG:4326", f"Heatmap - {attribute_name}", "memory")
        heatmap_provider = heatmap_layer.dataProvider()
        
        color_ramp = QgsStyle().defaultStyle().colorRamp('TransparentBlue')
        
        heatmap_renderer = QgsHeatmapRenderer()
        heatmap_renderer.setWeightExpression('1')
        heatmap_renderer.setRadius(10)
        heatmap_renderer.setColorRamp(color_ramp)
        
        # Determine if a feature is worth putting on a layer
        new_feats = []
        for feat in prov.getFeatures():
            try:
                if feat[attribute_name] == "true":
                    value = 1.0
                elif feat[attribute_name] == "false":
                    value = 0.0
                else:
                    value = float(feat[attribute_name])
            except:
                print(feat[attribute_name])
            if value > 0:
                new_feats.append(feat)
        
        heatmap_provider.addFeatures(new_feats)
        heatmap_layer.setRenderer(heatmap_renderer)
        heatmap_layer.setSubLayerVisibility(attribute_name, False)
        
        
        # Add the heatmap layer to the Layer Tree
        heating.insertChildNode(attributes.index(attribute_name), QgsLayerTreeLayer(heatmap_layer))

        # Display the heatmap
        layers.append(heatmap_layer)
        
        logging.debug("Added csv as layer")

    heating.updateChildVisibilityMutuallyExclusive()
    root.insertChildNode(0, QgsLayerTreeLayer(layer))
    root.insertChildNode(1, heating)

# Used to create heatmap layers from csv demographic data
def createDemographicHeatmapLayers(attributes: typing.List[str], file_path: str) -> None:
    demographic = QgsLayerTreeGroup()
    demographic.setName("Demographic Info")
    logging.info("Entered function")
    
    # Read the CSV file to obtain values for color assignment
    with open(file_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        data = {row['ZCTA']: {attr: row[attr] for attr in attributes} for row in reader}
        # logging.info(data.items())
    logging.info("Read file")
    
    # Create a heatmap layer for each attribute in heating_attributes
    for index, attribute_name in enumerate(attributes):
        heatmap_layer = QgsVectorLayer("Point?crs=EPSG:4326", f"Heatmap - {attribute_name}", "memory")
        logging.info(f"created new heatmap layer {attribute_name}")
        
        for layer in QgsProject.instance().mapLayers().values():
            if layer.name() == "BaseLayerDB — Zips_in_Metros":
                heatmap_layer = layer.clone()
                logging.info("cloned layer")
                break
        heatmap_layer.setName(f"Heatmap - {attribute_name}")
        logging.info(heatmap_layer.name())
        
        # Add attributes to the cloned layer
        with edit(heatmap_layer):
            for index, feature in enumerate(heatmap_layer.getFeatures()):
                zip_code = feature.attribute("ZCTA5")
                if zip_code in data:
                    value = data[zip_code].get(attribute_name, None)
                    logging.info(f"value set {value} for zipcode {zip_code}")
                    if value is not None:
                        if attribute_name not in heatmap_layer.fields().names():
                            # logging.info(feature.attributes())
                            heatmap_layer.addAttribute(QgsField(attribute_name, type=QVariant.String))
                            # logging.info(heatmap_layer.attributeList())
                            logging.info("attribute added")
                        heatmap_layer.getFeature(index+1).setAttribute(attribute_name, value)
                        logging.info("attribute set")
        
        # Add the heatmap layer to the Layer Tree
        demographic.insertChildNode(attributes.index(attribute_name), QgsLayerTreeLayer(heatmap_layer))

        # Display the heatmap
        layers.append(heatmap_layer)
        logging.debug("Added csv as layer")

    demographic.updateChildVisibilityMutuallyExclusive()
    root.insertChildNode(2, demographic)

# Create layers for each shape file or csv in the layers folder
for fileName in os.listdir(folderDirectory):
    fullFile = folderDirectory + os.sep + fileName
    path, type = os.path.splitext(fileName)
    
    # Create a vector layer from shape files
    if fileName.endswith(".shp"):
        layer = QgsVectorLayer(fullFile, fileName, "ogr")
        
        # Attempt to add the layer
        try:
            layers.append(layer)
            project.instance().addMapLayer(layer)
        except:
            logging.warning("Layer " + fileName + " failed to load!")
    
    # Create vector layers from csv files
    elif fileName.endswith(".csv"):
        # Store the headers of the csv file
        with open(fullFile, 'r', newline='') as file:
            reader = csv.reader(file)
            headers = next(reader)
            headers = [header.strip() for header in headers]
        
        # Create the csv path (csv_info) and add the csv headers to the path
        csv_info = "Point?crs=EPSG:4326"
        for index, header_name in enumerate(headers):
            headers[index] = header_name
            csv_info += f"&field={header_name}"
        
        layer = QgsVectorLayer(csv_info, "locations", "memory")
        prov = layer.dataProvider()
        fields = prov.fields()
        feats = []
        
        try:
            # Extracts desired attribute names from the csv headers
            attributes = headers
            if headers.__contains__("LONGITUDE"):
                prov = createCSVLayers(fullFile, fields, feats, headers, layer)
                attributes = list(itertools.dropwhile(lambda x : x != "LONGITUDE", headers))
                attributes.remove("LONGITUDE")
                createHeatingHeatmapLayers(prov, attributes)
            elif headers.__contains__("ZCTA"):
                attributes.remove("GEO_ID")
                attributes.remove("STATE_FIPS")
                createDemographicHeatmapLayers(attributes, fullFile)
        except Exception as e:
            # logging.warning("CSV " + fileName + " failed to load!")
            logging.error(e)
            logging.error(traceback.format_exc())

# Run the QGIS application event loop
qgs.exec_()
logging.debug("Last one") 