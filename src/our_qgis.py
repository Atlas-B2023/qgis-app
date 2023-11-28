import re
from qgis.core import *
from qgis.gui import *
from qgis.utils import *
from PyQt5.QtCore import QVariant
from qgis.PyQt.QtGui import QColor
import logging
import csv
import typing
import itertools
import traceback
from pathlib import Path
import os

# Keep in mind that this program will be running with python 3.9

# qgis = importlib.util.spec_from_file_location("qgis", "C:\Program Files\QGIS 3.34.0\apps\qgis\python\qgis")

# Grab the directory of the qgis project and parent folder of the project
project_directory = os.path.dirname(QgsProject.instance().fileName())
parent_directory = os.path.dirname(project_directory)
# recurse
METRO_DIRECTORY = (
    Path(__file__).parent.parent.parent
    / "ResidentialElectrificationTracker"
    / "output"
    / "metro_data"
)
# do not recurse
CENSUS_DIRECTORY = (
    Path(__file__).parent.parent.parent
    / "ResidentialElectrificationTracker"
    / "output"
    / "census_data"
)

# Set up project log file
log_file_path = os.path.join(parent_directory, "qgisdebug.log")
logging.basicConfig(
    filename=log_file_path,
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logging.info("========================================================================")

# Attempt to retrieve the path to the qgis-app and layers folders
try:
    scriptDirectory = os.path.join(parent_directory, "qgis-app")
    folderDirectory = os.path.join(scriptDirectory, "layers")
except Exception as e:
    logging.exception("Exception occurred: " + str(e))

# Initialize QGIS
QgsApplication.setPrefixPath("~/QGIS 3.34.0", True)
qgs = QgsApplication([], False)
qgs.initQgis()
logging.debug("Initialized QGIS")

# Create a project
project = QgsProject.instance()
project.read()

# Set up a layer tree
root = project.instance().layerTreeRoot()

# Load all layers
layers = []


# Used to create a point layer from csv data
def create_csv_layers(
    lines: typing.List[str], headers: typing.List[str], housing_layer: QgsVectorLayer
) -> QgsVectorDataProvider:
    prov = housing_layer.dataProvider()
    fields = prov.fields()
    feats = []

    # expecting lines to include header
    for line in lines[1:]:
        if not line.strip():
            continue
        values = line.split(",")
        feat = QgsFeature(fields)
        feat.setGeometry(
            QgsGeometry.fromPointXY(
                QgsPointXY(
                    float(values[headers.index("LONGITUDE")]),
                    float(values[headers.index("LATITUDE")]),
                )
            )
        )
        try:
            for header, csv_value in zip(headers, values):
                feat[header] = csv_value
        except Exception:
            logging.error(traceback.format_exc())
        feats.append(feat)
    prov.addFeatures(feats)
    housing_layer.setRenderer(
        housing_layer.renderer().defaultRenderer(housing_layer.geometryType())
    )
    housing_layer.updateExtents()
    housing_layer.setCrs(QgsCoordinateReferenceSystem("EPSG:4326"))
    # root.insertChildNode(0, QgsLayerTreeLayer(housing_layer))
    project.instance().addMapLayer(housing_layer)
    return prov


# Used to create heatmap layers from csv heating data
def create_heatmap_layers(
    prov: QgsVectorDataProvider,
    attributes: typing.List[str],
    heating_layers: QgsLayerTreeGroup,
) -> None:
    # Create a heatmap layer for each attribute in heating_attributes
    for attribute_name in attributes:
        # Checks if there is already a layer for an attribute, and if not it creates one
        check = False
        if len(heating_layers.children()) == 0:
            heatmap_layer = QgsVectorLayer(
                "Point?crs=EPSG:4326", f"Heatmap - {attribute_name}", "memory"
            )
            check = False
        else:
            for child_node in heating_layers.children():
                if child_node.name() == f"Heatmap - {attribute_name}":
                    heatmap_layer = child_node.layer()
                    check = True
                    break
                else:
                    heatmap_layer = QgsVectorLayer(
                        "Point?crs=EPSG:4326", f"Heatmap - {attribute_name}", "memory"
                    )
                    check = False

        heatmap_provider = heatmap_layer.dataProvider()
        heatmap_renderer = QgsHeatmapRenderer()
        heatmap_renderer.setWeightExpression("1")
        heatmap_renderer.setRadius(10)

        color_ramp = QgsStyle().defaultStyle().colorRamp("TransparentBlue")
        heatmap_renderer.setColorRamp(color_ramp)

        # Determine if a feature is worth putting on a layer
        new_feats = []
        for feat in prov.getFeatures():
            try:
                if feat[attribute_name] == "true":
                    # new_feat = QgsFeature(QgsFields(feat.fields()))
                    # new_feats.append(new_feat)
                    new_feats.append(QgsFeature(feat))
            except:
                logging.error(traceback.format_exc())

        # Update the layer with the new features
        heatmap_provider.addFeatures(new_feats)
        heatmap_layer.updateExtents()
        heatmap_layer.setRenderer(heatmap_renderer)
        heatmap_layer.setSubLayerVisibility(attribute_name, False)

        # Add the heatmap layer to the Layer Tree
        if check == False:
            heating_layers.insertChildNode(
                attributes.index(attribute_name), QgsLayerTreeLayer(heatmap_layer)
            )

        # Display the heatmap
        layers.append(heatmap_layer)


# Used to create heatmap layers from csv demographic data
def create_demographic_layers(
    attributes: typing.List[str], file_path: Path, demographic: QgsLayerTreeGroup
) -> None:
    # Create a dictionary of demographic variables as related to zipcodes
    with open(file_path, encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        data = {row["ZCTA"]: {attr: row[attr] for attr in attributes} for row in reader}

    for layer in QgsProject.instance().mapLayers().values():
        if layer.name() == "BaseLayerDB — Zips_in_Metros":
            base_layer = layer.clone()
            break

    # Create a layer for each attribute in heating_attributes
    for index, attribute_name in enumerate(attributes):
        # Determines how the headers should be grouped (DP05 in groups of 4, S1901 in groups of 2, etc.)
        # If reading a csv with a new format, copy one if statement and be sure to modify the values in range()
        # Csvs with groups larger than 4 will need to be modified further, by modifying the values in:
        # demo_layer.deleteAttributes(), new_feat.resizeAttributes(), and new_feat.setAttribute()
        if "EST" in attribute_name and "S" in file_path.stem:
            demo_layer = QgsVectorLayer(
                "MultiPolygon?crs=EPSG:3857", f"{attribute_name}", "memory"
            )
            demo_prov = demo_layer.dataProvider()
            original_fields = base_layer.fields()
            demo_prov.addAttributes(original_fields.toList())

            demo_layer.triggerRepaint()
            demo_fields = demo_prov.fields()

            demo_layer.startEditing()  # Acts as with edit(demo_layer), as that method does not work
            for ftr in base_layer.getFeatures():
                new_ftr = QgsFeature()
                new_ftr.setGeometry(ftr.geometry())
                new_ftr.setAttributes(ftr.attributes())
                demo_layer.addFeature(new_ftr)
            demo_layer.loadNamedStyle(base_layer.styleURI())
            demo_layer.styleManager().copyStylesFrom(base_layer.styleManager())

            demo_layer.startEditing()  # Acts as with edit(demo_layer), as that method does not work
            demo_layer.deleteAttributes(
                [27, 28, 29, 30]
            )  # Makes sure these attributes are empty before filling them

            for feature in demo_layer.getFeatures():
                zip_code = feature.attribute("ZCTA5")

                # Makes sure there is data for a zip code and the attribute does not already exist in the fields
                if (zip_code in data.keys()) and (
                    attribute_name not in demo_fields.names()
                ):
                    feat_id = feature.id()
                    new_feat = demo_layer.getFeature(feat_id)
                    features_size = new_feat.fields().size()

                    if features_size == 27:
                        new_feat.resizeAttributes(31)
                        features_size = new_feat.fields().size()

                    # Adds the group of four attributes to the zip code
                    # If the index statement was changed above, the values in range will also need to be changed
                    for i in range(0, 2):
                        if attributes[index + i] == "ZCTA":
                            break
                        demo_layer.addAttribute(
                            QgsField(attributes[index + i], QVariant.String)
                        )
                        new_feat.fields().append(
                            QgsField(attributes[index + i], QVariant.String),
                            originIndex=features_size + i,
                        )
                        field_idx = new_feat.fields().indexOf(attributes[index + i])
                        value = data[zip_code].get(attributes[index + i]).strip()

                        if field_idx == -1 and features_size == 27:
                            new_feat.setAttribute(features_size + i, value)
                        elif field_idx == -1 and not features_size == 27:
                            new_feat.setAttribute(features_size + i - 4, value)
                        else:
                            new_feat.setAttribute(field_idx, value)

                    demo_layer.updateFeature(new_feat)
        elif "PCT" in attribute_name and "DP" in file_path.stem:
            demo_layer = QgsVectorLayer(
                "MultiPolygon?crs=EPSG:3857", f"{attribute_name}", "memory"
            )
            demo_prov = demo_layer.dataProvider()
            original_fields = base_layer.fields()
            demo_prov.addAttributes(original_fields.toList())

            demo_layer.triggerRepaint()
            demo_fields = demo_prov.fields()

            demo_layer.startEditing()  # Acts as with edit(demo_layer), as that method does not work
            for ftr in base_layer.getFeatures():
                new_ftr = QgsFeature()
                new_ftr.setGeometry(ftr.geometry())
                new_ftr.setAttributes(ftr.attributes())
                demo_layer.addFeature(new_ftr)
            demo_layer.loadNamedStyle(base_layer.styleURI())
            demo_layer.styleManager().copyStylesFrom(base_layer.styleManager())

            demo_layer.startEditing()  # Acts as with edit(demo_layer), as that method does not work
            demo_layer.deleteAttributes(
                [27, 28, 29, 30]
            )  # Makes sure these attributes are empty before filling them

            for feature in demo_layer.getFeatures():
                zip_code = feature.attribute("ZCTA5")

                # Makes sure there is data for a zip code and the attribute does not already exist in the fields
                if (zip_code in data.keys()) and (
                    attribute_name not in demo_fields.names()
                ):
                    feat_id = feature.id()
                    new_feat = demo_layer.getFeature(feat_id)
                    features_size = new_feat.fields().size()

                    if features_size == 27:
                        new_feat.resizeAttributes(31)
                        features_size = new_feat.fields().size()

                    # Adds the group of four attributes to the zip code
                    # If the index statement was changed above, the values in range will also need to be changed
                    for i in range(-2, 2):
                        if attributes[index + i] == "ZCTA":
                            break
                        demo_layer.addAttribute(
                            QgsField(attributes[index + i], QVariant.String)
                        )
                        new_feat.fields().append(
                            QgsField(attributes[index + i], QVariant.String),
                            originIndex=features_size + i,
                        )
                        field_idx = new_feat.fields().indexOf(attributes[index + i])
                        value = data[zip_code].get(attributes[index + i]).strip()

                        if field_idx == -1 and features_size == 27:
                            new_feat.setAttribute(features_size + i, value)
                        elif field_idx == -1 and not features_size == 27:
                            new_feat.setAttribute(features_size + i - 4, value)
                        else:
                            new_feat.setAttribute(field_idx, value)

                    demo_layer.updateFeature(new_feat)
        else:
            continue

        # Colors the zip codes per the selected attribute's value
        try:
            unique_values = demo_layer.uniqueValues(
                demo_layer.fields().indexOf(attribute_name)
            )
            new_uniques = []
            for value in unique_values:
                if value is not None:
                    try:
                        formatted_val = float(value)
                        if formatted_val < 0.0:
                            continue
                        else:
                            new_uniques.append(formatted_val)
                    except:
                        continue
            unique_max = max(new_uniques)
            unique_min = min(new_uniques)
            color_ramp = QgsGradientColorRamp(
                QColor(255, 255, 255, 160), QColor(0, 0, 255, 160)
            )

            renderer = QgsCategorizedSymbolRenderer(attribute_name)
            for value in new_uniques:
                symbol = QgsSymbol.defaultSymbol(demo_layer.geometryType())
                layer = symbol.symbolLayer(0)
                translated_val = translate(value, unique_min, unique_max, 0, 1)
                layer.setColor(color_ramp.color(translated_val))
                category = QgsRendererCategory(value, symbol, str(value))
                renderer.addCategory(category)
            demo_layer.setRenderer(renderer)
        except Exception:
            logging.error(traceback.format_exc())

        # Add the layer to the Layer Tree
        demographic.insertChildNode(
            attributes.index(attribute_name), QgsLayerTreeLayer(demo_layer)
        )
        layers.append(demo_layer)

        # Used to limit number of layers generated for testing
        if index == 6:
            logging.info(index)
            break


# Used to map a value from one scale to another scale
def translate(value, fromMin, fromMax, toMin, toMax):
    fromSpan = fromMax - fromMin
    toSpan = toMax - toMin
    valueScaled = float(value - fromMin) / float(fromSpan)
    return toMin + (valueScaled * toSpan)


# Read all files in the directory stated and create layers accordingly
def read_housing_data(directory: Path):
    # All data within files in the housing folder will be combined in memory and processed as one
    # Get list of all zipcode csvs
    first = True
    merged_csv_contents = []
    headers = []
    zip_code_csv_regex = re.compile(r"[0-9]{3}|[0-9]{4}|[0-9]{5}")
    csv_files = [
        path
        for path in directory.rglob("*.csv")
        if zip_code_csv_regex.match(path.stem) is not None
    ]
    logging.info(f"{csv_files=}")
    for zip_file in csv_files:
        with open(zip_file, "r", encoding="utf-8") as f:
            lines = [line.strip("\r\n") for line in f.readlines()]
            if first:
                first = False
                headers = lines[0].split(",")
            # shouldnt error as each csv should only be created if data exsists (2 lines min)
            merged_csv_contents.extend(lines)

        logging.info(f"{headers =}")
    # Create the csv path (csv_info) and add the csv headers to the path
    csv_info = "Point?crs=EPSG:4326"

    csv_info += "".join([f"&field={header}" for header in headers])

    layer = QgsVectorLayer(csv_info, "Locations", "memory")

    try:
        # Extracts desired attribute names from the csv headers
        new_prov = create_csv_layers(merged_csv_contents, headers, layer)
        attributes = list(itertools.dropwhile(lambda x: x != "Electricity", headers))
        create_heatmap_layers(new_prov, attributes, heating_layers)
    except Exception as e:
        logging.error(e)
        logging.error(traceback.format_exc())


def read_demographic_data(directory: Path):
    # All files in the other folders, in the layers folder, will be processed individually
    for file_path in directory.glob("*.csv"):
        # create vector layer from csv files
        headers = []
        with open(file_path, "r", encoding="utf-8") as f:
            headers = f.readline().strip("\r\n").split(",")

        try:
            headers.remove("GEO_ID")
        except ValueError:
            logging.warn(f"{file_path} doesn't have geoid")
        try:
            headers.remove("STATE_FIPS")
        except ValueError:
            logging.warn(f"{file_path} doesn't have statefips")
        try:
            headers.remove("state")
        except ValueError:
            logging.warn(f"{file_path} doesn't have state")

        create_demographic_layers(headers, file_path, demographic_layers)


def read_shape_file(directory: Path):
    for file_path in directory.glob("*.shp"):
        layer = QgsVectorLayer(file_path, file_path.stem, "ogr")
        try:
            layers.append(layer)
            project.instance().addMapLayer(layer)
        except Exception:
            logging.warning("Layer " + file_path.stem + " failed to load!")


# Create layer groups for heating information and demographic information
heating_layers = QgsLayerTreeGroup("Heating Types")
demographic_layers = QgsLayerTreeGroup("Demographic Info")

# Calls to read specific folders within the layers folder
# To read files in a new folder, add a new line with the folder to be read as the second parameter
read_housing_data(METRO_DIRECTORY)
read_demographic_data(CENSUS_DIRECTORY)
# shapefile?

heating_layers.updateChildVisibilityMutuallyExclusive()
root.insertChildNode(1, heating_layers)
demographic_layers.updateChildVisibilityMutuallyExclusive()
root.insertChildNode(2, demographic_layers)

# Run the QGIS application event loop
# qgs.exec_()
logging.debug("Last one")
