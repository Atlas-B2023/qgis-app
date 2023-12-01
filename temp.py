        # logging.info("inside feature in demo layer")
        # logging.info(
        #     f"{zip_code in data.keys() =}, {attribute_name not in demo_fields.names() =}"
        # )
        # Makes sure there is data for a zip code and the attribute does not already exist in the fields

    
#         for i in range(0, 2):
    #             if next_atter_name == "ZCTA" or attributes[index] == "ZCTA":
    #                 break
    #             demo_layer.addAttribute(
    #                 QgsField(next_atter_name, QVariant.String)
    #             )
    #             new_feat.fields().append(
    #                 QgsField(next_atter_name, QVariant.String),
    #                 originIndex=features_size + i,
    #             )
    #             field_idx = new_feat.fields().indexOf(next_atter_name)
    #             value = data[zip_code].get(next_atter_name).strip()

    #             if field_idx == -1 and features_size == 27:
    #                 new_feat.setAttribute(features_size + i, value)
    #             elif field_idx == -1 and not features_size == 27:
    #                 new_feat.setAttribute(features_size + i - 4, value)
    #             else:
    #                 new_feat.setAttribute(field_idx, value)
    #         logging.info("Starting update")
    #         demo_layer.updateFeature(new_feat)
    # return demo_layer