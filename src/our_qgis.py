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
    QgsMapLayer,
    QgsLayerTreeGroup,
    QgsField,
    QgsCoordinateReferenceSystem,
    QgsReadWriteContext,
    QgsCategorizedSymbolRenderer,
    QgsSymbol,
    QgsRendererCategory,
)
from PyQt5.QtCore import QVariant
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtXml import QDomDocument
import logging
import csv
import typing
import itertools
from pathlib import Path
from sys import exit

# Keep in mind that this program will be running with python 3.9

CODE_PROJECT_DIRECTORY = Path(__file__).parent.parent
CODE_PARENT_DIRECTORY = CODE_PROJECT_DIRECTORY.parent
# change to name of folder of where saved project is
QGIS_PROJECT_FILE_DIRECTORY = CODE_PARENT_DIRECTORY / "current_qgis_map"

# recurse in this directory to get all metros
METRO_DIRECTORY = (
    Path(__file__).parent.parent.parent
    / "ResidentialElectrificationTracker"
    / "output"
    / "metro_data"
)
# do not recurse in this directory as other data is stored in sub folders
CENSUS_DIRECTORY = (
    Path(__file__).parent.parent.parent
    / "ResidentialElectrificationTracker"
    / "output"
    / "census_data"
)

LOCATION_HEATMAP_GPKG_OUTPUT = QGIS_PROJECT_FILE_DIRECTORY / "location_heatmap.gpkg"
CENSUS_DATA_GPKG_OUTPUT = QGIS_PROJECT_FILE_DIRECTORY / "census_data.gpkg"

# Attributes are what you want the layer to color with. allow list is ZCTA and the accompanying columns to the attributes
#! TODO make sure these are ordered the way they appear in the csv file
DP05_ALLOW_LIST = [
    "ESTSexAndAgeTPOP",
    "MOESexAndAgeTPOP",
    "PCTSexAndAgeTPOP",
    "PMESexAndAgeTPOP",
    "ESTSexAndAgeTPOPMedianAge(years)",
    "MOESexAndAgeTPOPMedianAge(years)",
    "PCTSexAndAgeTPOPMedianAge(years)",
    "PMESexAndAgeTPOPMedianAge(years)",
    "ESTSexAndAgeTPOPUnder18Years",
    "MOESexAndAgeTPOPUnder18Years",
    "PCTSexAndAgeTPOPUnder18Years",
    "PMESexAndAgeTPOPUnder18Years",
    "ESTSexAndAgeTPOP16Yearsplus",
    "MOESexAndAgeTPOP16Yearsplus",
    "PCTSexAndAgeTPOP16Yearsplus",
    "PMESexAndAgeTPOP16Yearsplus",
    "ESTSexAndAgeTPOP18Yearsplus",
    "MOESexAndAgeTPOP18Yearsplus",
    "PCTSexAndAgeTPOP18Yearsplus",
    "PMESexAndAgeTPOP18Yearsplus",
    "ESTSexAndAgeTPOP21Yearsplus",
    "MOESexAndAgeTPOP21Yearsplus",
    "PCTSexAndAgeTPOP21Yearsplus",
    "PMESexAndAgeTPOP21Yearsplus",
    "ESTSexAndAgeTPOP62Yearsplus",
    "MOESexAndAgeTPOP62Yearsplus",
    "PCTSexAndAgeTPOP62Yearsplus",
    "PMESexAndAgeTPOP62Yearsplus",
    "ESTSexAndAgeTPOP65Yearsplus",
    "MOESexAndAgeTPOP65Yearsplus",
    "PCTSexAndAgeTPOP65Yearsplus",
    "PMESexAndAgeTPOP65Yearsplus",
    "ESTRaceAloneOrInCombinationWith1plusOtherRacesTPOP_W_",
    "MOERaceAloneOrInCombinationWith1plusOtherRacesTPOP_W_",
    "PCTRaceAloneOrInCombinationWith1plusOtherRacesTPOP_W_",
    "PMERaceAloneOrInCombinationWith1plusOtherRacesTPOP_W_",
    "ESTRaceAloneOrInCombinationWith1plusOtherRacesTPOP_B_",
    "MOERaceAloneOrInCombinationWith1plusOtherRacesTPOP_B_",
    "PCTRaceAloneOrInCombinationWith1plusOtherRacesTPOP_B_",
    "PMERaceAloneOrInCombinationWith1plusOtherRacesTPOP_B_",
    "ESTRaceAloneOrInCombinationWith1plusOtherRacesTPOP_A_",
    "MOERaceAloneOrInCombinationWith1plusOtherRacesTPOP_A_",
    "PCTRaceAloneOrInCombinationWith1plusOtherRacesTPOP_A_",
    "PMERaceAloneOrInCombinationWith1plusOtherRacesTPOP_A_",
    "ESTRaceAloneOrInCombinationWith1plusOtherRacesTPOP_S_",
    "MOERaceAloneOrInCombinationWith1plusOtherRacesTPOP_S_",
    "PCTRaceAloneOrInCombinationWith1plusOtherRacesTPOP_S_",
    "PMERaceAloneOrInCombinationWith1plusOtherRacesTPOP_S_",
    "ESTRaceAloneOrInCombinationWith1plusOtherRacesTPOP_P_",
    "MOERaceAloneOrInCombinationWith1plusOtherRacesTPOP_P_",
    "PCTRaceAloneOrInCombinationWith1plusOtherRacesTPOP_P_",
    "PMERaceAloneOrInCombinationWith1plusOtherRacesTPOP_P_",
    "ESTRaceAloneOrInCombinationWith1plusOtherRacesTPOP_O_",
    "MOERaceAloneOrInCombinationWith1plusOtherRacesTPOP_O_",
    "PCTRaceAloneOrInCombinationWith1plusOtherRacesTPOP_O_",
    "PMERaceAloneOrInCombinationWith1plusOtherRacesTPOP_O_",
    "ESTTotalHousingUnits",
    "MOETotalHousingUnits",
    "PCTTotalHousingUnits",
    "PMETotalHousingUnits",
    "ZCTA",
]

DP05_ATTRIBUTES = [
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
    "ESTPCTAgeByEduAttainPop18To24YearsHighSchoolGraduate(includesEquivalency)",
    "MOEPCTAgeByEduAttainPop18To24YearsHighSchoolGraduate(includesEquivalency)",
    "ESTPCTAgeByEduAttainPop18To24YearsBachelorsDegreeOrHigher",
    "MOEPCTAgeByEduAttainPop18To24YearsBachelorsDegreeOrHigher",
    "ESTPCTAgeByEduAttainPop25YearsplusHighSchoolGraduate(includesEquivalency)",
    "MOEPCTAgeByEduAttainPop25YearsplusHighSchoolGraduate(includesEquivalency)",
    "ESTPCTAgeByEduAttainPop25YearsplusBachelorsDegreeOrHigher",
    "MOEPCTAgeByEduAttainPop25YearsplusBachelorsDegreeOrHigher",
    "ZCTA",
]

S1501_ATTRIBUTES = [
    "ESTPCTAgeByEduAttainPop18To24YearsHighSchoolGraduate(includesEquivalency)",
    "ESTPCTAgeByEduAttainPop18To24YearsBachelorsDegreeOrHigher",
    "ESTPCTAgeByEduAttainPop25YearsplusHighSchoolGraduate(includesEquivalency)",
    "ESTPCTAgeByEduAttainPop25YearsplusBachelorsDegreeOrHigher",
]

S1901_ALLOW_LIST = [
    "ESTHouseholdsTotal",
    "MOEHouseholdsTotal",
    "ESTHouseholdsTotalLessThanD10000",
    "MOEHouseholdsTotalLessThanD10000",
    "ESTHouseholdsTotalD10000ToD14999",
    "MOEHouseholdsTotalD10000ToD14999",
    "ESTHouseholdsTotalD15000ToD24999",
    "MOEHouseholdsTotalD15000ToD24999",
    "ESTHouseholdsTotalD25000ToD34999",
    "MOEHouseholdsTotalD25000ToD34999",
    "ESTHouseholdsTotalD35000ToD49999",
    "MOEHouseholdsTotalD35000ToD49999",
    "ESTHouseholdsTotalD50000ToD74999",
    "MOEHouseholdsTotalD50000ToD74999",
    "ESTHouseholdsTotalD75000ToD99999",
    "MOEHouseholdsTotalD75000ToD99999",
    "ESTHouseholdsTotalD100000ToD149999",
    "MOEHouseholdsTotalD100000ToD149999",
    "ESTHouseholdsTotalD150000ToD199999",
    "MOEHouseholdsTotalD150000ToD199999",
    "ESTHouseholdsTotalD200000plus",
    "MOEHouseholdsTotalD200000plus",
    "ESTHouseholdsMedianIncome(dollars)",
    "MOEHouseholdsMedianIncome(dollars)",
    "ESTHouseholdsMeanIncome(dollars)",
    "MOEHouseholdsMeanIncome(dollars)",
    "ZCTA",
]

S1901_ATTRIBUTES = [
    "ESTHouseholdsTotal",
    "ESTHouseholdsTotalLessThanD10000",
    "ESTHouseholdsTotalD10000ToD14999",
    "ESTHouseholdsTotalD15000ToD24999",
    "ESTHouseholdsTotalD25000ToD34999",
    "ESTHouseholdsTotalD35000ToD49999",
    "ESTHouseholdsTotalD50000ToD74999",
    "ESTHouseholdsTotalD75000ToD99999",
    "ESTHouseholdsTotalD100000ToD149999",
    "ESTHouseholdsTotalD150000ToD199999",
    "ESTHouseholdsTotalD200000plus",
    "ESTHouseholdsMedianIncome(dollars)",
    "ESTHouseholdsMeanIncome(dollars)",
]
# Set up project log file
LOG_FILE_PATH = CODE_PARENT_DIRECTORY / "qgisdebug.log"
logging.basicConfig(
    filename=LOG_FILE_PATH,
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

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
# demo_layers = []


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

    # layer, csv, headers, attributes
    return (
        QgsVectorLayer(csv_info, "Locations", "memory"),
        merged_csv_contents,
        headers,
        list(itertools.dropwhile(lambda x: x != "Electricity", headers)),
    )


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


def load_filtered_data_from_demo_file(
    file_path: Path
):  # -> tuple[dict[str | Any, dict[str, str | Any]] | None, Literal[4, 2] | None]
    """Filters csv to just be the allowed columns for that census table type

    Args:
        csv_headers (list[str]): the headers of the csv file
        file_path (Path): the path to the census data csv

    Returns:
        _type_: _description_
    """
    zip_data_dict = None
    range_type = None
    if "S1501" in file_path.stem:
        with open(file_path, encoding="utf-8") as csv_file:
            csv_reader = csv.DictReader(csv_file)
            zip_data_dict = {
                row["ZCTA"]: {attr: row[attr] for attr in S1501_ALLOW_LIST}
                for row in csv_reader
            }
        range_type = 2

    elif "S1901" in file_path.stem:
        with open(file_path, encoding="utf-8") as csv_file:
            csv_reader = csv.DictReader(csv_file)
            zip_data_dict = {
                row["ZCTA"]: {attr: row[attr] for attr in S1901_ALLOW_LIST}
                for row in csv_reader
            }
        range_type = 2

    elif "DP05" in file_path.stem:
        with open(file_path, encoding="utf-8") as csv_file:
            csv_reader = csv.DictReader(csv_file)
            zip_data_dict = {
                row["ZCTA"]: {attr: row[attr] for attr in DP05_ALLOW_LIST}
                for row in csv_reader
            }
        range_type = 4

    return (zip_data_dict, range_type)


# Used to create heatmap layers from csv demographic data
def create_demographic_layers(
    file_path: Path
) -> typing.Union[list[QgsVectorLayer], None]:
    # (table_name, layers)
    # doc = QDomDocument()
    # read_write_context = QgsReadWriteContext()
    possible_layers = project.mapLayersByName("BaseLayerDB — Zips_in_Metros")

    base_layer = None
    if possible_layers:
        base_layer = possible_layers[0].clone()

    assert isinstance(base_layer, QgsMapLayer)

    # organized as:
    # {"zipcode1" : {"ESTPCT...": value,
    #                "ESTPCT2...": value,
    #                ...},
    #  "zipcode2" : {},...
    # }
    zip_data_dict, range_type = load_filtered_data_from_demo_file(file_path)
    # un recognized table
    assert zip_data_dict is not None
    assert range_type is not None

    if range_type not in [2, 4]:
        logging.warning("could not recognize file format.")
        return None

    demo_layers: list[QgsVectorLayer] = []
    if "S1901" in file_path.stem:
        # testing
        first = True
        for attribute in S1901_ATTRIBUTES:
            if not first:
                break
            first = False
            logging.info(f"Making layer for {attribute =}")
            demo_layers.append(
                demographics_groups(
                    range_type, base_layer, attribute, S1901_ALLOW_LIST, zip_data_dict
                )
            )
        assert len(demo_layers) > 0
        color_demo_layer(S1901_ATTRIBUTES, demo_layers)
    if "S1501" in file_path.stem:
        first = True
        for attribute in S1501_ATTRIBUTES:
            if not first:
                break
            first = False
            logging.info(f"Making layer for {attribute =}")
            demo_layers.append(
                demographics_groups(
                    range_type, base_layer, attribute, S1501_ALLOW_LIST, zip_data_dict
                )
            )
        assert len(demo_layers) > 0
        color_demo_layer(S1501_ATTRIBUTES, demo_layers)
    if "DP05" in file_path.stem:
        first = True
        for attribute in DP05_ATTRIBUTES:
            if not first:
                break
            first = False
            logging.info(f"Making layer for {attribute =} with range {range_type}")
            demo_layers.append(
                demographics_groups(
                    range_type, base_layer, attribute, DP05_ALLOW_LIST, zip_data_dict
                ),
            )
        assert len(demo_layers) > 0
        color_demo_layer(DP05_ATTRIBUTES, demo_layers)

    return demo_layers


def color_demo_layer(
    table_attributes: list[str], table_layers: list[QgsVectorLayer]
) -> None:
    """Modifies vector layer list elements to have a graduated color scheme based on their attributes

    Args:
        table_attributes (list[str]): _description_
        table_layers (list[QgsVectorLayer]): _description_

    Returns:
        list[QgsVectorLayer]: _description_
    """
    # TODO layer should have fields ZCTA, Attr, and supporting attrs
    for cur_layer in table_layers:
        for field_name in cur_layer.fields().names():
            if field_name not in table_attributes:
                continue
            unique_values = cur_layer.uniqueValues(
                cur_layer.fields().indexOf(field_name)
            )
            new_uniques = []
            for variant in unique_values:
                if isinstance(variant, QVariant):
                    try:
                        if variant.isNull():
                            continue
                        else:
                            raise AttributeError
                    except AttributeError:
                        logging.info(f"{type(variant) = }, {variant = }")
                        exit()
                else:
                    formatted_val = float(variant)
                if formatted_val < 0.0:
                    continue
                new_uniques.append(formatted_val)

            if len(new_uniques) == 0:
                # this shouldnt hit, should always have at least one None in list
                continue
            try:
                unique_max = max(new_uniques)
            except ValueError:
                continue
            try:
                unique_min = min(new_uniques)
            except ValueError:
                continue

            color_ramp = QgsGradientColorRamp(
                QColor(255, 255, 255, 160), QColor(0, 0, 255, 160)
            )

            renderer = QgsCategorizedSymbolRenderer(field_name)
            cur_layer.startEditing()
            logging.info(f"{len(new_uniques) = }")
            for value in new_uniques:
                symbol = QgsSymbol.defaultSymbol(cur_layer.geometryType())
                symbol_layer = symbol.symbolLayer(0)
                translated_val = translate(value, unique_min, unique_max, 0, 1)
                symbol_layer.setColor(color_ramp.color(translated_val))
                category = QgsRendererCategory(value, symbol, str(value))
                renderer.addCategory(category)
            cur_layer.setRenderer(renderer)
            cur_layer.commitChanges()
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
    #     demo_layer.setRenderer(renderer)

    #     demo_layer.exportNamedStyle(doc, read_write_context)
    #     demo_layer.commitChanges()

    #     error = save_census_data_gpkg(demo_layer)

    #     if error == QgsVectorFileWriter.WriterError.NoError:
    #         demo_layer_path = f"{CENSUS_DATA_GPKG_OUTPUT}|layername={demo_layer.name()}"
    #         demo_layer = QgsVectorLayer(
    #             demo_layer_path, f"Demo-{attribute_name}", "ogr"
    #         )
    #         demo_layer.importNamedStyle(doc)
    #         demo_layer.saveStyleToDatabase(
    #             demo_layer.name(), f"{demo_layer.name()} style", True, ""
    #         )
    #         demo_layers.append(demo_layer)
    #     else:
    #         logging.error(f"Encountered error {error} when writing {demo_layer.name()}")
    #     # Add the layer to the Layer Tree
    #     # demo_layers.append(demo_layer)
    #     # csv_groups.insertChildNode(
    #     #     attributes.index(attribute_name), QgsLayerTreeLayer(demo_layer)
    #     # )
    #     # csv_groups.updateChildVisibilityMutuallyExclusive()

    #     layers.append(demo_layer)
    #     # Used to limit number of layers generated for testing
    #     # if index == 6:
    #     #     logging.info(index)
    #     #     break


def chunked(it, size):
    it = iter(it)
    while True:
        p = tuple(itertools.islice(it, size))
        if not p:
            break
        yield p


# Creates heatmap layers for csvs that are grouped in twos
def demographics_groups(
    range_type: int,
    base_layer: QgsVectorLayer,
    attr_name: str,
    table_allow_list: list,
    zip_data_dict: dict[str, dict[str, str]],
) -> QgsVectorLayer:
    """create layer based on census column


    Note:
        Features are rows in a layer, fields are columns in a layer. attributes are cells.

    Args:
        base_layer (QgsVectorLayer): base layer
        attr_name (str): census column name you would like a layer created for
        zip_data_dict (dict[str, dict[str, str]]): dictionary of all zip codes, and each desired column with this columns data. should be 33k long, and each entry should be a dict of length about 40
    """
    demo_layer = QgsVectorLayer("MultiPolygon?crs=EPSG:3857", f"{attr_name}", "memory")
    doc = QDomDocument()
    read_write_context = QgsReadWriteContext()
    # copy base layer information to our demographic layer
    demo_layer.startEditing()
    demo_prov = demo_layer.dataProvider()
    demo_prov.addAttributes(
        [QgsField("ZCTA5", QVariant.Type.String)]
    )
    demo_layer.updateFields()
    logging.info(f"{demo_layer.fields().names() = },{demo_layer.fields().toList() = }")
    demo_layer.commitChanges()

    # runs about 39k times per layer. see if can combine with other. also only copy zcta attr

    for old_feature in base_layer.getFeatures():
        new_zcta5_feature = QgsFeature()
        new_zcta5_feature.setFields(demo_layer.fields())
        # set feature to possible features
        new_zcta5_feature.setGeometry(old_feature.geometry())
        new_zcta5_feature.setAttribute("ZCTA5", old_feature.attributes()[old_feature.fieldNameIndex("ZCTA5")])
        demo_layer.startEditing()
        demo_layer.addFeature(new_zcta5_feature)
        demo_layer.commitChanges()

    demo_layer.startEditing()
    demo_layer.loadNamedStyle(base_layer.styleURI())
    demo_layer.styleManager().copyStylesFrom(base_layer.styleManager())
    demo_layer.commitChanges()
    # done copying

    # add the four related census column names as fields
    desired_census_columns = []
    for attr_chunk in chunked(table_allow_list, range_type):
        if len(attr_chunk) != range_type:
            break
        if attr_name not in attr_chunk:
            continue
        for i, _ in enumerate(attr_chunk):
            desired_census_columns.append(attr_chunk[i])
            demo_layer.startEditing()
            demo_prov.addAttributes([QgsField(attr_chunk[i], QVariant.Type.String)])
            demo_layer.commitChanges()
        break
    demo_layer.updateFields()
    # runs about 39k times per layer.
    for feature in demo_layer.getFeatures():
        # row id. this is each zip code shape
        feature_id = feature.id()
        # prepare zip code data
        target_zip_code_field_index = feature.fieldNameIndex("ZCTA5")
        target_zip_code: str = feature.attributes()[target_zip_code_field_index]
        target_zip_code_data_dict = zip_data_dict.get(target_zip_code, "")
        if isinstance(target_zip_code_data_dict, str):
            # theres a lot of these, so try not to enable
            # logging.warning(f"Could not find zip code dict entry for {target_zip_code}!")
            continue
        # the census_column_dict relies on the fact that desired_census_columns have been added as data provider attributes (fields) to the layer
        # since values in the raw dict can be erroneous, do not make a color map out of them. filter before you do
        census_column_dict = {
            column_name: column_value
            for column_name, column_value in target_zip_code_data_dict.items()
            if column_name in desired_census_columns
        }

        demo_layer.startEditing()
        # final values will either be < 0, NULL, or a valid number
        for key, value in census_column_dict.items():
            census_field_index = feature.fieldNameIndex(key)
            desired_attr_value = {census_field_index: value}
            demo_prov.changeAttributeValues({feature_id: desired_attr_value})
        demo_layer.commitChanges()

    # TODO DO NOT SAVE HERE. STYLING HAPPENS IN CALLER FUNCTION
    demo_layer.exportNamedStyle(doc, read_write_context)
    error = save_census_data_gpkg(demo_layer)

    if error == QgsVectorFileWriter.WriterError.NoError:
        demo_layer_path = f"{CENSUS_DATA_GPKG_OUTPUT}|layername={demo_layer.name()}"
        demo_layer = QgsVectorLayer(
            demo_layer_path, f"Census-{demo_layer.name()}", "ogr"
        )
        demo_layer.importNamedStyle(doc)
        demo_layer.saveStyleToDatabase(
            demo_layer.name(), f"{demo_layer.name()} style", True, ""
        )
    else:
        logging.error(f"Encountered error {error} when writing {demo_layer.name()}")
    return demo_layer


# Used to map a value from one scale to another scale
def translate(value, fromMin, fromMax, toMin, toMax):
    fromSpan = fromMax - fromMin
    toSpan = toMax - toMin
    valueScaled = float(value - fromMin) / float(fromSpan)
    return toMin + (valueScaled * toSpan)


def read_demographic_data(directory: Path) -> list[tuple[str, list[QgsVectorLayer]]]:
    """Read the census directory and create a list of vector layers for each filtered field in each file found in the dir.

    Args:
        directory (Path): census directory

    Returns:
        typing.List[typing.List[QgsVectorLayer]]: list of lists, grouped by filename
    """
    demo_groups: list[tuple[str, list[QgsVectorLayer]]] = []

    # All files in the other folders, in the layers folder, will be processed individually
    for file_path in directory.glob("*.csv"):
        logging.info(f"Found census table : {file_path.stem}")
        layers_for_file = create_demographic_layers(file_path)
        if layers_for_file is None:
            continue
        demo_groups.append((file_path.stem, layers_for_file))

    assert len(demo_groups) > 0
    return demo_groups


# Create layer groups cant be "saved" to gpkg. to keep the layering, the project must be saved.
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

project.addMapLayer(location_layer)

# Have to rearrange before saving
heatmap_group = layer_tree_root.addGroup("Heating Types")
assert isinstance(heatmap_group, QgsLayerTreeGroup)
for placed_layer in heatmap_layers:
    project.addMapLayer(placed_layer)
    heatmap_group.addLayer(placed_layer)
    project.layerTreeRoot().findLayer(placed_layer.id()).setItemVisibilityChecked(False)

demo_groups = read_demographic_data(CENSUS_DIRECTORY)
for table_layer_list in demo_groups:
    for layer in table_layer_list[1]:
        project.addMapLayer(layer)
        project.layerTreeRoot().findLayer(layer.id()).setItemVisibilityChecked(False)
# Have to rearrange before saving
# demo_group = layer_tree_root.addGroup("Demographic Data")
# assert isinstance(demo_group, QgsLayerTreeGroup)
# for index, placed_layer in enumerate(demo_groups):
#     project.addMapLayer(demo_groups[index], False)
#     demo_group.addLayer(demo_groups[index])

logging.debug("Last one")

# QgsProject.instance().layerTreeRoot().findLayer(layer_id/layername).setItemVisibilityChecked(False)
