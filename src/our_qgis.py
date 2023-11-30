import re
from qgis.core import (
    QgsApplication,
    QgsProject,
    QgsVectorLayer,
    QgsGeometry,
    QgsPointXY,
    QgsVectorFileWriter,
    QgsVectorDataProvider,
    QgsHeatmapRenderer,
    QgsGradientColorRamp,
    QgsFeature,
    QgsLayerTreeLayer,
    QgsLayerTreeGroup,
    QgsField,
    QgsRendererCategory,
    QgsCategorizedSymbolRenderer,
    QgsSymbol,
    QgsCoordinateReferenceSystem,
    QgsReadWriteContext,
)
from PyQt5.QtCore import QVariant
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtXml import QDomDocument
import logging
import csv
import typing
import itertools
import traceback
from pathlib import Path
from sys import exit

# Keep in mind that this program will be running with python 3.9

# qgis = importlib.util.spec_from_file_location("qgis", "C:\Program Files\QGIS 3.34.0\apps\qgis\python\qgis")

# Grab the directory of the qgis project and parent folder of the project
#! this should be a sibling folder to the two repository folders
PROJECT_DIRECTORY = Path(__file__).parent.parent
PARENT_DIRECTORY = PROJECT_DIRECTORY.parent
QGIS_PROJECT_FILE_DIRECTORY = PARENT_DIRECTORY / "QGIS Map"
# new_current_gis_map

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

LOCATION_HEATMAP_GPKG_OUTPUT = QGIS_PROJECT_FILE_DIRECTORY / "location_heatmap.gpkg"
CENSUS_DATA_GPKG_OUTPUT = QGIS_PROJECT_FILE_DIRECTORY / "census_data.gpkg"

DP05_ALLOW_LIST = [
    "PCTTotalHousingUnits",
    "PCTSexAndAgeTPOP",
    "PCTSexAndAgeTPOPMedianAge(years)",
    "PCTSexAndAgeTPOPUnder18Years",
    "PCTSexAndAgeTPOP16Yearsplus",
    "PCTSexAndAgeTPOP18Yearsplus",
    "PCTSexAndAgeTPOP21Yearsplus",
    "PCTSexAndAgeTPOP62Yearsplus",
    "PCTSexAndAgeTPOP65Yearsplus",
    "PCTRaceAloneOrInCombinationWith1plusOtherRacesTPOP_W_",
    "PCTRaceAloneOrInCombinationWith1plusOtherRacesTPOP_B_",
    "PCTRaceAloneOrInCombinationWith1plusOtherRacesTPOP_A_",
    "PCTRaceAloneOrInCombinationWith1plusOtherRacesTPOP_S_",
    "PCTRaceAloneOrInCombinationWith1plusOtherRacesTPOP_P_",
    "PCTRaceAloneOrInCombinationWith1plusOtherRacesTPOP_O_",
]

S1501_ALLOW_LIST = [
    "ESTPCTAgeByEduAttainPop25YearsplusHighSchoolGraduate(includesEquivalency)",
    "ESTPCTAgeByEduAttainPop25YearsplusBachelorsDegreeOrHigher",
    "ESTPCTAgeByEduAttainPop18To24YearsHighSchoolGraduate(includesEquivalency)",
    "ESTPCTAgeByEduAttainPop18To24YearsBachelorsDegreeOrHigher",
]

# Set up project log file
log_file_path = PARENT_DIRECTORY / "qgisdebug.log"
logging.basicConfig(
    filename=log_file_path,
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Attempt to retrieve the path to the qgis-app and layers folders
scriptDirectory = PARENT_DIRECTORY / "qgis-app"
folderDirectory = scriptDirectory / "layers"

if not scriptDirectory.exists() or not folderDirectory.exists():
    logging.warning("qgis-app (repository) or layers (sub folder) does not exist")

# Initialize QGIS
QgsApplication.setPrefixPath("~/QGIS 3.34.0", True)
qgs = QgsApplication([], False)
qgs.initQgis()
logging.info("========================================================================")
logging.debug("Initialized QGIS")
logging.info("========================================================================")
logging.info(
    f"Saving location and heatmap GPKGs to {str(LOCATION_HEATMAP_GPKG_OUTPUT)}"
)
# Create a project
project = QgsProject.instance()
project.read()

# Set up a layer tree
layer_tree_root = project.instance().layerTreeRoot()

# Load all layers
layers = []


# Read all files in the directory stated and create layers accordingly
def read_housing_data_and_create_temp_location_points_layer(
    all_metros_directory: Path
) -> tuple[QgsVectorLayer, list[typing.Any], list[str], list[str]]:
    # All data within files in the housing folder will be combined in memory and processed as one
    # Get list of all zipcode csvs
    first = True
    merged_csv_contents = []
    headers = []
    zip_code_csv_regex = re.compile(r"[0-9]{3}|[0-9]{4}|[0-9]{5}")
    csv_files = [
        path
        for path in all_metros_directory.rglob("*.csv")
        if zip_code_csv_regex.match(path.stem) is not None
    ]

    for zip_file in csv_files:
        with open(zip_file, "r", encoding="utf-8") as f:
            lines = [line.strip("\r\n") for line in f.readlines() if line.strip("\r\n")]
            if first:
                first = False
                headers = lines[0].split(",")
            merged_csv_contents.extend(lines[1:])

    # Create the csv path (csv_info) and add the csv headers to the path
    csv_info = "Point?crs=EPSG:4326"

    csv_info += "".join([f"&field={header}" for header in headers])

    # location_layer_temp = QgsVectorLayer(csv_info, "Locations", "memory")
    # layer, csv, headers, attributes
    return (
        QgsVectorLayer(csv_info, "Locations", "memory"),
        merged_csv_contents,
        headers,
        list(itertools.dropwhile(lambda x: x != "Electricity", headers)),
    )

    # try:
    #     # Extracts desired attribute names from the csv headers
    #     new_prov = create_location_layers_from_csv(merged_csv_contents, headers, location_layer_temp)
    #     # attributes go up to heating details, skipping the general property info
    #     attributes = list(itertools.dropwhile(lambda x: x != "Electricity", headers))
    #     create_heatmap_layers(new_prov, attributes, heating_layers)
    # except Exception as e:
    #     logging.error(e)
    #     logging.error(traceback.format_exc())


# Used to create a point layer from csv data
def create_locations_layer_from_csv(
    csv_contents: typing.List[str],
    csv_headers: typing.List[str],
    locations_layer: QgsVectorLayer,
) -> QgsVectorLayer:
    """For each location in the given csv, add them as a feature to the provided housing layer

    Args:
        lines (typing.List[str]): csv content. do not include headers
        headers (typing.List[str]): headers
        housing_layer (QgsVectorLayer): the housing layer to display

    Returns:
        QgsVectorDataProvider: _description_
    """
    # list of location dots to be added to the layer
    feats = []

    locations_layer.startEditing()
    prov = locations_layer.dataProvider()
    fields = prov.fields()

    for line in csv_contents:
        csv_values = line.split(",")
        feat = QgsFeature(fields)

        feat.setGeometry(
            QgsGeometry.fromPointXY(
                QgsPointXY(
                    float(csv_values[csv_headers.index("LONGITUDE")]),
                    float(csv_values[csv_headers.index("LATITUDE")]),
                )
            )
        )

        for header, csv_value in zip(csv_headers, csv_values):
            feat[header] = csv_value
        feats.append(feat)

    prov.addFeatures(feats)
    locations_layer.setRenderer(
        locations_layer.renderer().defaultRenderer(locations_layer.geometryType())
    )
    locations_layer.setCrs(QgsCoordinateReferenceSystem("EPSG:4326"))
    locations_layer.updateExtents()
    locations_layer.commitChanges()

    error = save_location_heatmap_gpkg(locations_layer)

    if error == QgsVectorFileWriter.WriterError.NoError:
        locations_layer_path = (
            f"{LOCATION_HEATMAP_GPKG_OUTPUT}|layername={locations_layer.name()}"
        )
        locations_layer = QgsVectorLayer(locations_layer_path, "Locations", "ogr")
    else:
        logging.error(
            f"Encountered error {error} when writing {locations_layer.name()}"
        )
    return locations_layer


# Saves the location and heatmap layers in a database
def save_location_heatmap_gpkg(layer: QgsVectorLayer):
    if LOCATION_HEATMAP_GPKG_OUTPUT.exists():
        # update
        options = QgsVectorFileWriter.SaveVectorOptions()
        options.layerName = layer.name()
        options.fileEncoding = layer.dataProvider().encoding()
        options.attributes = layer.attributeList()  # just putting for sakes
        options.actionOnExistingFile = (
            QgsVectorFileWriter.ActionOnExistingFile.CreateOrOverwriteLayer
        )

        error = QgsVectorFileWriter.writeAsVectorFormatV3(
            layer,
            str(LOCATION_HEATMAP_GPKG_OUTPUT),
            project.transformContext(),
            options,
        )
    else:
        # create
        options = QgsVectorFileWriter.SaveVectorOptions()
        options.layerName = layer.name()
        options.attributes = layer.attributeList()

        error = QgsVectorFileWriter.writeAsVectorFormatV3(
            layer,
            str(LOCATION_HEATMAP_GPKG_OUTPUT),
            project.transformContext(),
            options,
        )
    return error[0]


# Saves the demographic layers in a database
def save_census_data_gpkg(layer: QgsVectorLayer):
    if CENSUS_DATA_GPKG_OUTPUT.exists():
        # update
        options = QgsVectorFileWriter.SaveVectorOptions()
        options.layerName = layer.name()
        options.fileEncoding = layer.dataProvider().encoding()
        options.attributes = layer.attributeList()  # just putting for sakes
        options.actionOnExistingFile = (
            QgsVectorFileWriter.ActionOnExistingFile.CreateOrOverwriteLayer
        )

        error = QgsVectorFileWriter.writeAsVectorFormatV3(
            layer,
            str(CENSUS_DATA_GPKG_OUTPUT),
            project.transformContext(),
            options,
        )
    else:
        # create
        options = QgsVectorFileWriter.SaveVectorOptions()
        options.layerName = layer.name()
        options.attributes = layer.attributeList()

        error = QgsVectorFileWriter.writeAsVectorFormatV3(
            layer,
            str(CENSUS_DATA_GPKG_OUTPUT),
            project.transformContext(),
            options,
        )
    return error[0]


# Used to create heatmap layers from csv heating data
def create_heatmap_layers(
    location_layer_prov: QgsVectorDataProvider,
    attributes: typing.List[str],
) -> list[QgsVectorLayer]:
    """Generate heat maps for the given attributes. Make sure that when you are rendering that you add all of these to a tree

    Args:
        prov (QgsVectorDataProvider): _description_
        attributes (typing.List[str]): _description_
    """
    heating_layers: list[QgsVectorLayer] = []
    doc = QDomDocument()
    read_write_context = QgsReadWriteContext()
    # Create a heatmap layer for each attribute in heating_attributes
    for attribute_name in attributes:
        # horizontal
        # Checks if there is already a layer for an attribute, and if not it creates one. eg if there is no diesel in the csv, still make the diesel layer
        heatmap_layer = None
        # If group is empty or if layer for attribute doesn't exist, create the layer. else get that layer
        if not heating_layers:
            heatmap_layer = QgsVectorLayer(
                "Point?crs=EPSG:4326", f"Heatmap-{attribute_name}", "memory"
            )
        else:
            for index, temp_layer in enumerate(heating_layers):
                if temp_layer.name() == f"Heatmap-{attribute_name}":
                    heatmap_layer = heating_layers[index]
                    break
                else:
                    heatmap_layer = QgsVectorLayer(
                        "Point?crs=EPSG:4326", f"Heatmap-{attribute_name}", "memory"
                    )
        try:
            assert heatmap_layer is not None
        except AssertionError:
            logging.error(
                f"Heatmap for {attribute_name} was None after trying to process."
            )
            exit()
        new_feats = []
        heatmap_layer.startEditing()
        heatmap_provider = heatmap_layer.dataProvider()
        # Determine if a feature is worth putting on a layer
        # vertical
        for feat in location_layer_prov.getFeatures():
            try:
                # value inside the csv file for wether a house has Electricity, NG, etc
                if feat[attribute_name] == "true":
                    new_feats.append(QgsFeature(feat))
            except KeyError:
                logging.error(
                    f"Could not find {attribute_name} field in {heatmap_layer.name()}"
                )
        heatmap_provider.addFeatures(new_feats)
        heatmap_layer.updateExtents()

        heatmap_renderer = QgsHeatmapRenderer()
        heatmap_renderer.setWeightExpression("1")
        heatmap_renderer.setRadius(10)
        heatmap_renderer.setColorRamp(
            QgsGradientColorRamp(QColor(255, 16, 16, 0), QColor(67, 67, 215, 255))
        )
        heatmap_layer.setRenderer(heatmap_renderer)
        # heatmap_layer.setSubLayerVisibility(attribute_name, False)
        heatmap_layer.exportNamedStyle(doc, read_write_context)
        heatmap_layer.commitChanges()

        error = save_location_heatmap_gpkg(heatmap_layer)

        if error == QgsVectorFileWriter.WriterError.NoError:
            heatmap_layer_path = (
                f"{LOCATION_HEATMAP_GPKG_OUTPUT}|layername={heatmap_layer.name()}"
            )
            heatmap_layer = QgsVectorLayer(
                heatmap_layer_path, f"Heatmap-{attribute_name}", "ogr"
            )
            heatmap_layer.importNamedStyle(doc)
            heatmap_layer.saveStyleToDatabase(
                heatmap_layer.name(), f"{heatmap_layer.name()} style", True, ""
            )
            heating_layers.append(heatmap_layer)
        else:
            logging.error(
                f"Encountered error {error} when writing {heatmap_layer.name()}"
            )

    return heating_layers


# Used to create heatmap layers from csv demographic data
def create_demographic_layers(
    attributes: typing.List[str],
    file_path: Path
) -> typing.List[QgsVectorLayer]:
    
    demo_layers: list[QgsVectorLayer] = []
    doc = QDomDocument()
    read_write_context = QgsReadWriteContext()
    
    # Create a dictionary of demographic variables as related to zipcodes
    with open(file_path, encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        data = {row["ZCTA"]: {attr: row[attr] for attr in attributes} for row in reader}

    for layer in QgsProject.instance().mapLayers().values():
        if layer.name() == "BaseLayerDB — Zips_in_Metros":
            base_layer = layer.clone()
            break

    # csv_groups = QgsLayerTreeGroup(f"{file_path.stem}")
    

    # Create a layer for each attribute in heating_attributes
    for index, attribute_name in enumerate(attributes):
        # Determines how the headers should be grouped (DP05 in groups of 4, S1901 in groups of 2, etc.)
        # If reading a csv with a new format, copy one if statement and be sure to modify the values in range()
        # Csvs with groups larger than 4 will need to be modified further, by modifying the values in:
        # demo_layer.deleteAttributes(), new_feat.resizeAttributes(), and new_feat.setAttribute()
        if (
            "S1501" in file_path.stem
            and attribute_name in S1501_ALLOW_LIST
            and "PCT" in attribute_name
        ):
            demo_layer = demographics_groups_of_four(
                attributes, attribute_name, base_layer, data, index
            )
        elif (
            "S1901" in file_path.stem
            and "famil" not in attribute_name.lower()
            and "EST" in attribute_name
        ):
            demo_layer = demographics_groups_of_two(
                attributes, attribute_name, base_layer, data, index
            )
        elif (
            "DP05" in file_path.stem
            and attribute_name in DP05_ALLOW_LIST
            and "PCT" in attribute_name
        ):
            demo_layer = demographics_groups_of_four(
                attributes, attribute_name, base_layer, data, index
            )
        else:
            continue
        
        # Colors the zip codes per the selected attribute's value
        unique_values = demo_layer.uniqueValues(
            demo_layer.fields().indexOf(attribute_name)
        )
        new_uniques = []
        for value in unique_values:
            if value is not None:
                try:
                    formatted_val = float(value)
                except ValueError:
                    continue
                if formatted_val < 0.0:
                    continue
                else:
                    new_uniques.append(formatted_val)
        if len(new_uniques) == 0:
            continue
        try:
            unique_max = max(new_uniques)
        except ValueError:
            logging.warning(f"failed max: {unique_values = }, {attribute_name = }")
        try:
            unique_min = min(new_uniques)
        except ValueError:
            logging.warning(f"failed min: {unique_values = }, {attribute_name = }")
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
        # error = QgsVectorFileWriter.writeAsVectorFormat(
        #     demo_layer,
        #     str(CENSUS_DATA_GPKG_OUTPUT / f"Demo-{attribute_name}.gpkg"),
        #     "UTF-8",
        #     demo_layer.crs(),
        #     "GPKG",
        # )
        # if error[0] == QgsVectorFileWriter.WriterError.NoError:
        #     shape_file_vector = QgsVectorLayer(
        #         str(CENSUS_DATA_GPKG_OUTPUT / f"Demo-{attribute_name}.gpkg"),
        #         f"{attribute_name}.gpkg",
        #         "ogr",
        #     )
        #     logging.info(f"Demo-{attribute_name}.gpkg file saved")
        #     # for some reason the writer doesnt save the crs info
        #     shape_file_vector.setCrs(demo_layer.crs())
        #     # mutate var so that its now pointing to the
        #     demo_layer = shape_file_vector
        # else:
        #     logging.info(f"Could not save Demo-{attribute_name}.gpkg")
        demo_layer.setRenderer(renderer)
        
        demo_layer.exportNamedStyle(doc, read_write_context)
        demo_layer.commitChanges()
        
        error = save_census_data_gpkg(demo_layer)

        if error == QgsVectorFileWriter.WriterError.NoError:
            demo_layer_path = (
                f"{CENSUS_DATA_GPKG_OUTPUT}|layername={demo_layer.name()}"
            )
            demo_layer = QgsVectorLayer(
                demo_layer_path, f"Demo-{attribute_name}", "ogr"
            )
            demo_layer.importNamedStyle(doc)
            demo_layer.saveStyleToDatabase(
                demo_layer.name(), f"{demo_layer.name()} style", True, ""
            )
            demo_layers.append(demo_layer)
        else:
            logging.error(
                f"Encountered error {error} when writing {demo_layer.name()}"
            )
        # Add the layer to the Layer Tree
        # demo_layers.append(demo_layer)
        # csv_groups.insertChildNode(
        #     attributes.index(attribute_name), QgsLayerTreeLayer(demo_layer)
        # )
        # csv_groups.updateChildVisibilityMutuallyExclusive()

        layers.append(demo_layer)
        # Used to limit number of layers generated for testing
        # if index == 6:
        #     logging.info(index)
        #     break
    return demo_layers


# Creates heatmap layers for csvs that are grouped in twos
def demographics_groups_of_two(
    attributes: typing.List[str],
    attribute_name: str,
    base_layer: QgsVectorLayer,
    data: typing.Dict[str, typing.Dict[str, str]],
    index: int,
) -> QgsVectorLayer:
    logging.info(f"{attribute_name = }")
    demo_layer = QgsVectorLayer(
        "MultiPolygon?crs=EPSG:3857", f"{attribute_name}", "memory"
    )
    demo_prov = demo_layer.dataProvider()
    original_fields = base_layer.fields()
    demo_prov.addAttributes(original_fields.toList())
    logging.info("Set up layer")
    
    demo_layer.triggerRepaint()
    demo_fields = demo_prov.fields()

    logging.info("Start editing")
    demo_layer.startEditing()  # Acts as with edit(demo_layer), as that method does not work
    logging.info("Here 1")
    for ftr in base_layer.getFeatures():
        new_ftr = QgsFeature()
        logging.info("Here 2")
        new_ftr.setGeometry(ftr.geometry())
        logging.info("Here 3")
        new_ftr.setAttributes(ftr.attributes())
        logging.info("Here 4")
        demo_layer.addFeature(new_ftr)
        logging.info("Here 5")
    demo_layer.loadNamedStyle(base_layer.styleURI())
    logging.info("Here 6")
    demo_layer.styleManager().copyStylesFrom(base_layer.styleManager())
    logging.info("Here 7")
    demo_layer.commitChanges()

    logging.info("Start editing again")
    demo_layer.startEditing()  # Acts as with edit(demo_layer), as that method does not work
    demo_layer.deleteAttributes(
        [27, 28, 29, 30]
    )  # Makes sure these attributes are empty before filling them
    logging.info("Attributed deleted")
    
    for feature in demo_layer.getFeatures():
        zip_code = feature.attribute("ZCTA5")

        # Makes sure there is data for a zip code and the attribute does not already exist in the fields
        if (zip_code in data.keys()) and (attribute_name not in demo_fields.names()):
            feat_id = feature.id()
            new_feat = demo_layer.getFeature(feat_id)
            features_size = new_feat.fields().size()

            logging.info("Attempting resize")
            if features_size == 27:
                new_feat.resizeAttributes(31)
                features_size = new_feat.fields().size()

            logging.info("Adding attributes")
            # Adds the group of two attributes to the zip code
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
            logging.info("Starting update")
            demo_layer.updateFeature(new_feat)
    return demo_layer


# Creates heatmap layers for csvs that are grouped in fours
def demographics_groups_of_four(
    attributes: typing.List[str],
    attribute_name: str,
    base_layer: QgsVectorLayer,
    data: typing.Dict[str, typing.Dict[str, str]],
    index: int,
) -> QgsVectorLayer:
    logging.info(f"{attribute_name = }")
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
        if (zip_code in data.keys()) and (attribute_name not in demo_fields.names()):
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
    return demo_layer


# Used to map a value from one scale to another scale
def translate(value, fromMin, fromMax, toMin, toMax):
    fromSpan = fromMax - fromMin
    toSpan = toMax - toMin
    valueScaled = float(value - fromMin) / float(fromSpan)
    return toMin + (valueScaled * toSpan)


def read_demographic_data(directory: Path) -> typing.List[typing.List[QgsVectorLayer]]:
    demo_groups = []
    
    # All files in the other folders, in the layers folder, will be processed individually
    for idx, file_path in enumerate(directory.glob("*.csv")):
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

        demo_groups.append(create_demographic_layers(headers, file_path))
    return demo_groups


def read_shape_file(directory: Path):
    for file_path in directory.glob("*.shp"):
        layer = QgsVectorLayer(str(file_path), file_path.stem, "ogr")
        try:
            layers.append(layer)
            project.instance().addMapLayer(layer)
        except Exception:
            logging.warning("Layer " + file_path.stem + " failed to load!")


# Create layer groups for heating information and demographic information
# heatmap_layer_tree_group = QgsLayerTreeGroup("Heating Types")
# demographic_layers = QgsLayerTreeGroup("Demographic Info")

(
    csv_layer,
    csv_contents,
    csv_headers,
    csv_attributes,
) = read_housing_data_and_create_temp_location_points_layer(METRO_DIRECTORY)
location_layer = create_locations_layer_from_csv(csv_contents, csv_headers, csv_layer)
heatmap_layers = create_heatmap_layers(location_layer.dataProvider(), csv_attributes)
demo_groups = read_demographic_data(CENSUS_DIRECTORY)

# add all layers to global LAYERS = [], and for each LAYER in LAYERS, project.addmaplayer(layer,...)
project.addMapLayer(location_layer)

# Have to rearrange before saving
heatmap_group = layer_tree_root.addGroup("Heating Types")
assert isinstance(heatmap_group, QgsLayerTreeGroup)
for index, placed_layer in enumerate(heatmap_layers):
    project.addMapLayer(heatmap_layers[index], False)
    heatmap_group.addLayer(heatmap_layers[index])
    
# Have to rearrange before saving
demo_group = layer_tree_root.addGroup("Demographic Data")
assert isinstance(demo_group, QgsLayerTreeGroup)
for index, placed_layer in enumerate(demo_groups):
    project.addMapLayer(demo_groups[index], False)
    demo_group.addLayer(demo_groups[index])

logging.debug("Last one")

# QgsProject.instance().layerTreeRoot().findLayer(layer_id/layername).setItemVisibilityChecked(False)
