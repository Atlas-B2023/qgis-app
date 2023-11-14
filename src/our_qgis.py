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
import statistics

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
def createCSVLayers(file_path: str, fields: QgsFields, feats: typing.List[str], headers: typing.List[str], housing_layer: QgsVectorLayer) -> QgsVectorDataProvider:
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
    housing_layer.updateExtents()
    housing_layer.setCrs(QgsCoordinateReferenceSystem('EPSG:4326'))
    logging.debug("Created prov")
    return prov

# Used to create heatmap layers from csv heating data
def createHeatingHeatmapLayers(prov: QgsVectorDataProvider, attributes: typing.List[str], heating_layers: QgsLayerTreeGroup) -> None:
    
    # Create a heatmap layer for each attribute in heating_attributes
    for attribute_name in attributes:
        
        check = False
        if len(heating_layers.children()) == 0:
            heatmap_layer = QgsVectorLayer("Point?crs=EPSG:4326", f"Heatmap - {attribute_name}", "memory")
            logging.info("was 0")
            check = False
        else:
            for child_node in heating_layers.children():
                logging.info(f"{attribute_name = }, {child_node.name() = }")
                # logging.info(child_node.name() == f"Heatmap - {attribute_name}")
                if child_node.name() == f"Heatmap - {attribute_name}":
                    heatmap_layer = child_node.layer()
                    logging.info("exists")
                    check = True
                    break
                else:
                    heatmap_layer = QgsVectorLayer("Point?crs=EPSG:4326", f"Heatmap - {attribute_name}", "memory")
                    logging.info("does not exist")
                    check = False
        
        heatmap_provider = heatmap_layer.dataProvider()
        heatmap_renderer = QgsHeatmapRenderer()
        heatmap_renderer.setWeightExpression('1')
        heatmap_renderer.setRadius(10)
        
        color_ramp = QgsStyle().defaultStyle().colorRamp('TransparentBlue')
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
        heatmap_layer.updateExtents()
        heatmap_layer.setRenderer(heatmap_renderer)
        heatmap_layer.setSubLayerVisibility(attribute_name, False)
        
        # Add the heatmap layer to the Layer Tree
        if check == False:
            heating_layers.insertChildNode(attributes.index(attribute_name), QgsLayerTreeLayer(heatmap_layer))

        # Display the heatmap
        layers.append(heatmap_layer)

# Used to create heatmap layers from csv demographic data
def createDemographicLayers(attributes: typing.List[str], file_path: str, demographic: QgsLayerTreeGroup) -> None:
    
    # Create a dictionary of demographic variables as related to zipcodes
    with open(file_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        data = {row['ZCTA']: {attr: row[attr] for attr in attributes} for row in reader}

    for layer in QgsProject.instance().mapLayers().values():
        if layer.name() == "BaseLayerDB — Zips_in_Metros":
            base_layer = layer.clone()
            break
    
    # Create a layer for each attribute in heating_attributes
    for index, attribute_name in enumerate(attributes):
        if index == 0 or index % 4 == 0:
            demo_layer = QgsVectorLayer("MultiPolygon?crs=EPSG:3857", f"{attribute_name}", "memory")
            demo_prov = demo_layer.dataProvider()
            original_fields = base_layer.fields()
            demo_prov.addAttributes(original_fields.toList())
            
            demo_layer.triggerRepaint()
            demo_fields = demo_prov.fields()
            
            demo_layer.startEditing() # Acts as with edit(demo_layer), as that method does not work
            for ftr in base_layer.getFeatures():
                new_ftr = QgsFeature()
                new_ftr.setGeometry(ftr.geometry())
                new_ftr.setAttributes(ftr.attributes())
                demo_layer.addFeature(new_ftr)
            demo_layer.loadNamedStyle(base_layer.styleURI())
            demo_layer.styleManager().copyStylesFrom(base_layer.styleManager())

            
            demo_layer.startEditing() # Acts as with edit(demo_layer), as that method does not work
            demo_layer.deleteAttributes([27, 28, 29, 30])
            
            for feature in demo_layer.getFeatures():
                zip_code = feature.attribute("ZCTA5")
                
                if (zip_code in data.keys()) and (attribute_name not in demo_fields.names()):
                    feat_id = feature.id()
                    new_feat = demo_layer.getFeature(feat_id)
                    features_size = new_feat.fields().size()
                    
                    if (features_size == 27):
                        new_feat.resizeAttributes(31)
                        features_size = new_feat.fields().size()
                    
                    for i in range(0, 4):
                        demo_layer.addAttribute(QgsField(attributes[index+i], QVariant.String))
                        new_feat.fields().append(QgsField(attributes[index+i], QVariant.String), originIndex = features_size+i)
                        field_idx = new_feat.fields().indexOf(attributes[index+i])
                        value = data[zip_code].get(attributes[index+i]).strip()
                        
                        if field_idx == -1 and features_size == 27:
                            new_feat.setAttribute(features_size+i, value)
                            # logging.info(f"first, {feat_id}, {field_idx}, {features_size+i}, {attributes[index+i]}, {value}, {new_feat.attribute(features_size+i)}")
                        elif field_idx == -1 and not features_size == 27:
                            new_feat.setAttribute(features_size+i-4, value)
                            # logging.info(f"second, {feat_id}, {field_idx}, {features_size+i-4}, {attributes[index+i]}, {value}, {new_feat.attribute(features_size+i-4)}")
                        else:
                            new_feat.setAttribute(field_idx, value)
                            # logging.info(f"third, {feat_id}, {field_idx}, {features_size+i}, {attributes[index+i]}, {value}, {new_feat.attribute(field_idx)}")
                    
                    demo_layer.updateFeature(new_feat)

            renderer = QgsCategorizedSymbolRenderer(attributes[index])
            unique_values = demo_layer.uniqueValues(demo_layer.fields().indexOf(attributes[index]))
            new_uniques = []
            for value in unique_values:
                if value is not None:
                    if value.isnumeric():
                        new_uniques.append(float(value))
            unique_max = max(new_uniques)
            unique_min = min(new_uniques)
            color_ramp = QgsGradientColorRamp(QColor(255,255,255,160), QColor(0,0,255,160))
            
            for value in new_uniques:
                symbol = QgsSymbol.defaultSymbol(demo_layer.geometryType())
                layer = symbol.symbolLayer(0)
                translated_val = translate(value, unique_min, unique_max, 0, 1)
                # logging.info(f"{unique_min = }, {unique_max = }, {value = }, {translated_val = }")
                layer.setColor(color_ramp.color(translated_val))
                category = QgsRendererCategory(value, symbol, str(value))
                renderer.addCategory(category)
            demo_layer.setRenderer(renderer)
            
            # Add the layer to the Layer Tree
            demographic.insertChildNode(attributes.index(attribute_name), QgsLayerTreeLayer(demo_layer))

            # Display the layer
            layers.append(demo_layer)
            
            # Used to limit number of layers generated for testing
            if index > 4:
                break
    
# Used to map a value from one scale into another scale
def translate(value, fromMin, fromMax, toMin, toMax):
    fromSpan = fromMax - fromMin
    toSpan = toMax - toMin
    valueScaled = float(value - fromMin) / float(fromSpan)
    return toMin + (valueScaled * toSpan)



# Create layer groups for heating information and demographic information
heating_layers = QgsLayerTreeGroup("Heating Types")
demographic_layers = QgsLayerTreeGroup("Demographic Info")

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
                createHeatingHeatmapLayers(prov, attributes, heating_layers)
            elif headers.__contains__("ZCTA"):
                attributes.remove("GEO_ID")
                attributes.remove("STATE_FIPS")
                createDemographicLayers(attributes, fullFile, demographic_layers)
        except Exception as e:
            logging.error(e)
            logging.error(traceback.format_exc())

root.insertChildNode(0, QgsLayerTreeLayer(layer))
heating_layers.updateChildVisibilityMutuallyExclusive()
root.insertChildNode(1, heating_layers)
demographic_layers.updateChildVisibilityMutuallyExclusive()
root.insertChildNode(2, demographic_layers)

# Run the QGIS application event loop
qgs.exec_()
logging.debug("Last one") 