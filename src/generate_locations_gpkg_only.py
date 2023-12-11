import our_qgis as script

if __name__ == "__console__":
    (
        csv_layer,
        csv_contents,
        csv_headers,
        csv_attributes,
    ) = script.read_housing_data_and_create_temp_location_points_layer(
        script.METRO_DIRECTORY
    )
    location_layer = script.create_locations_layer_from_csv(
        csv_contents, csv_headers, csv_layer
    )

    script.create_heatmap_layers(location_layer, csv_attributes)
