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
        # logging.debug("Added csv as layer")

    heating.updateChildVisibilityMutuallyExclusive()
    root.insertChildNode(0, QgsLayerTreeLayer(layer))
    root.insertChildNode(1, heating)

# Used to create heatmap layers from csv demographic data
def createDemographicHeatmapLayers(attributes: typing.List[str], file_path: str) -> None:
    demographic = QgsLayerTreeGroup()
    demographic.setName("Demographic Info")
    
    # Create a dictionary of demographic variables as related to zipcodes
    with open(file_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        data = {row['ZCTA']: {attr: row[attr] for attr in attributes} for row in reader}

    for layer in QgsProject.instance().mapLayers().values():
        if layer.name() == "BaseLayerDB — Zips_in_Metros":
            base_layer = layer.clone()
            break
    
    # Create a heatmap layer for each attribute in heating_attributes
    for index, attribute_name in enumerate(attributes):
        if index == 0 or index % 4 == 0:
            heatmap_layer = QgsVectorLayer("MultiPolygon?crs=EPSG:3857", f"{attribute_name}", "memory")
            heatmap_prov = heatmap_layer.dataProvider()
            original_fields = base_layer.fields()
            heatmap_prov.addAttributes(original_fields.toList())
            
            heatmap_layer.triggerRepaint()
            heatmap_fields = heatmap_prov.fields()
            
            heatmap_layer.startEditing() # Acts as with edit(heatmap_layer), as that method does not work
            for ftr in base_layer.getFeatures():
                new_ftr = QgsFeature()
                new_ftr.setGeometry(ftr.geometry())
                new_ftr.setAttributes(ftr.attributes())
                heatmap_layer.addFeature(new_ftr)
            heatmap_layer.loadNamedStyle(base_layer.styleURI())
            heatmap_layer.styleManager().copyStylesFrom(base_layer.styleManager())

            
            heatmap_layer.startEditing() # Acts as with edit(heatmap_layer), as that method does not work
            heatmap_layer.deleteAttributes([27, 28, 29, 30])
            
            for feature in heatmap_layer.getFeatures():
                zip_code = feature.attribute("ZCTA5")
                
                if (zip_code in data.keys()) and (attribute_name not in heatmap_fields.names()):
                    feat_id = feature.id()
                    new_feat = heatmap_layer.getFeature(feat_id)
                    features_size = new_feat.fields().size()
                    
                    if (features_size == 27):
                        new_feat.resizeAttributes(31)
                        features_size = new_feat.fields().size()
                    
                    for i in range(0, 4):
                        heatmap_layer.addAttribute(QgsField(attributes[index+i], QVariant.String))
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
                    
                    heatmap_layer.updateFeature(new_feat)

            renderer = QgsCategorizedSymbolRenderer(attributes[index])
            unique_values = heatmap_layer.uniqueValues(heatmap_layer.fields().indexOf(attributes[index]))
            unique_max = max(unique_values)
            unique_min = min(unique_values)
            color_ramp = QgsGradientColorRamp(QColor(0,0,0), QColor(0,0,255))
            # color_ramp = QgsRandomColorRamp()
            
            for value in unique_values:
                logging.info(value)
                if value is not None:
                    symbol = QgsSymbol.defaultSymbol(heatmap_layer.geometryType())
                    layer = symbol.symbolLayer(0)
                    layer.setColor(color_ramp.color(translate(float(value), 0, 255, unique_min, unique_max)))
                
                    category = QgsRendererCategory(float(value), symbol, str(value))
                    renderer.addCategory(category)
                
            heatmap_layer.setRenderer(renderer)
            
            # Add the layer to the Layer Tree
            demographic.insertChildNode(attributes.index(attribute_name), QgsLayerTreeLayer(heatmap_layer))

            # Display the layer
            layers.append(heatmap_layer)
            logging.debug("Added csv as layer")
            
            # Used to limit number of layers generated for testing
            if index > 4:
                break

    demographic.updateChildVisibilityMutuallyExclusive()
    root.insertChildNode(2, demographic)

# Used to create divisions using the median of the data from the csv for each attribute
def createDivisions(data, attribute_name: str):
    max_value = 0
    min_value = 0
    median_whole = 0
    median_lower = 0
    median_upper = 0
    values_whole = []
    values_lower = []
    values_upper = []
    
    for zip in data:
        value = data[zip].get(attribute_name, None)
        # logging.info(value)
        try:
            adjusted_value = float(value)
        except Exception as e:
            logging.warning(f"value is not a number: {e}")
            adjusted_value = 0
        values_whole.append(adjusted_value)
        if all(x < 0 for x in values_whole):
            return None
        else:
            values_whole = [0 if i < 0 else i for i in values_whole]
        
    max_value = max(values_whole)
    min_value = min(values_whole)
    median_whole = statistics.median(values_whole)
    
    for value in values_whole:
        if value <= median_whole:
            values_lower.append(value)
        else:
            values_upper.append(value)
        
    median_lower = statistics.median(values_lower)
    median_upper = statistics.median(values_upper)
    logging.info(f"{attribute_name}, {max_value}, {min_value}, {median_whole}, {median_upper}, {median_lower}")
    
    divisions = [min_value, median_lower, median_whole, median_upper, max_value]
    return divisions
   
# Used to create the gradient to assign each zip code based on the attribute value
def colorAssignment(divisions: typing.List[float]):
    colors = []
    
    # for val in divisions:
    #     translate(val, 0, 255, )
    
# Used to map a value from one scale into another scale
def translate(value, toMin, toMax, fromMin, fromMax):
    # Figure out how 'wide' each range is
    toSpan = toMax - toMin
    fromSpan = fromMax - fromMin

    # Convert the left range into a 0-1 range (float)
    valueScaled = float(value - toMin) / float(toSpan)

    # Convert the 0-1 range into a value in the right range.
    return fromMin + (valueScaled * fromSpan)

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