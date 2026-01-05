
import streamlit as st
from gws_core import Scenario, ScenarioSearchBuilder, Tag
from gws_core.streamlit import StreamlitContainers, StreamlitRouter
from gws_core.tag.entity_tag_list import EntityTagList
from gws_core.tag.tag_entity_type import TagEntityType
from gws_ubiome.ubiome_dashboard._ubiome_dashboard_core.functions_steps import (
    build_scenarios_by_step_dict,
    get_status_emoji,
)
from gws_ubiome.ubiome_dashboard._ubiome_dashboard_core.state import State
from streamlit_slickgrid import (
    ExportServices,
    FieldType,
    slickgrid,
)


def render_first_page(ubiome_state : State):
    translate_service = ubiome_state.get_translate_service()

    style = """
    [CLASS_NAME] {
        padding: 40px;
    }
    """

    with StreamlitContainers.container_full_min_height('container-center_first_page',
                additional_style=style):

        # Add a button create new analysis using config
        # Create a container for the header with project title and action buttons
        col_title, col_button_new = StreamlitContainers.columns_with_fit_content(
                key="button_new",
                cols=[1, 'fit-content'], vertical_align_items='center')

        with col_title:
            st.markdown(f"## {translate_service.translate('retrieve_recipes')}")

        with col_button_new:
            if not ubiome_state.get_is_standalone():
                if st.button(translate_service.translate("create_new_recipe"), icon=":material/add:", width="content", type = "primary"):
                    # On click, navigate to a hidden page 'run new recipe'
                    router = StreamlitRouter.load_from_session()
                    router.navigate("new-analysis")


        # Add the table to retrieve the previous analysis

        search_scenario_builder = ScenarioSearchBuilder() \
            .add_tag_filter(Tag(key=ubiome_state.TAG_BRICK, value=ubiome_state.TAG_UBIOME)) \
            .add_tag_filter(Tag(key=ubiome_state.TAG_UBIOME, value=ubiome_state.TAG_METADATA)) \
            .add_is_archived_filter(False)

        # We got here all the metadata scenarios
        list_scenario_user: list[Scenario] = search_scenario_builder.search_all()

        # Create data for SlickGrid table
        table_data = []
        for scenario in list_scenario_user:
            entity_tag_list = EntityTagList.find_by_entity(TagEntityType.SCENARIO, scenario.id)
            tag_analysis_name = entity_tag_list.get_tags_by_key(ubiome_state.TAG_ANALYSIS_NAME)[0].to_simple_tag()

            # Initialize row data with basic info
            row_data = {
                "id": scenario.id,
                "Name given": tag_analysis_name.value,
                "Folder": scenario.folder.name if scenario.folder else "",
                "metadata": get_status_emoji(scenario.status)
            }

            # Get pipeline ID to find all related scenarios
            pipeline_id_tags = entity_tag_list.get_tags_by_key(ubiome_state.TAG_UBIOME_PIPELINE_ID)
            if pipeline_id_tags:
                pipeline_id = pipeline_id_tags[0].to_simple_tag().value

                # Search for all scenarios with this pipeline ID
                pipeline_search_builder = ScenarioSearchBuilder() \
                    .add_tag_filter(Tag(key=ubiome_state.TAG_UBIOME_PIPELINE_ID, value=pipeline_id)) \
                    .add_is_archived_filter(False)

                pipeline_scenarios = pipeline_search_builder.search_all()

                # Check each step type and add status to row data
                step_types = [
                    (ubiome_state.TAG_QC, "quality_control"),
                    (ubiome_state.TAG_MULTIQC, "multiqc"),
                    (ubiome_state.TAG_FEATURE_INFERENCE, "feature_inference"),
                    (ubiome_state.TAG_RAREFACTION, "rarefaction"),
                    (ubiome_state.TAG_TAXONOMY, "taxonomy"),
                    (ubiome_state.TAG_PCOA_DIVERSITY, "pcoa"),
                    (ubiome_state.TAG_ANCOM, "ancom"),
                    (ubiome_state.TAG_DB_ANNOTATOR, "db_annotator"),
                ]

                # Add ratio step if enabled (before 16S steps)
                if ubiome_state.get_has_ratio_step():
                    step_types.append((ubiome_state.TAG_RATIO, "ratio"))

                # Add 16S steps at the end
                step_types.extend([
                    (ubiome_state.TAG_16S, "16S"),
                    (ubiome_state.TAG_16S_VISU, "16S_visualization")
                ])

                for tag_value, field_name in step_types:
                    step_scenarios = [s for s in pipeline_scenarios if any(
                        tag.tag_key == ubiome_state.TAG_UBIOME and tag.tag_value == tag_value
                        for tag in EntityTagList.find_by_entity(TagEntityType.SCENARIO, s.id).get_tags()
                    )]

                    if step_scenarios:
                        # Get the most recent scenario for this step
                        latest_scenario = max(step_scenarios, key=lambda x: x.created_at)
                        row_data[field_name] = get_status_emoji(latest_scenario.status)
                    else:
                        row_data[field_name] = ""
            else:
                # Initialize empty status for other steps when no pipeline ID
                step_fields = ["quality_control", "multiqc", "feature_inference", "rarefaction", "taxonomy",
                            "pcoa", "ancom", "db_annotator"]
                if ubiome_state.get_has_ratio_step():
                    step_fields.append("ratio")
                step_fields.extend(["16S", "16S_visualization"])
                for field in step_fields:
                    row_data[field] = ""

            table_data.append(row_data)

        if table_data:
            columns = [
                {
                    "id": "Name given",
                    "name": translate_service.translate("recipe_name"),
                    "field": "Name given",
                    "sortable": True,
                    "type": FieldType.string,
                    "filterable": True,
                    "width": 120,
                },
                {
                    "id": "Folder",
                    "name": translate_service.translate("folder"),
                    "field": "Folder",
                    "sortable": True,
                    "type": FieldType.string,
                    "filterable": True,
                    "width": 100,
                },
                {
                    "id": "metadata",
                    "name": translate_service.translate("metadata"),
                    "field": "metadata",
                    "sortable": True,
                    "type": FieldType.string,
                    "filterable": True,
                    "width": 60,
                },
                {
                    "id": "quality_control",
                    "name": translate_service.translate("quality_control"),
                    "field": "quality_control",
                    "sortable": True,
                    "type": FieldType.string,
                    "filterable": True,
                    "width": 40,
                },
                {
                    "id": "multiqc",
                    "name": translate_service.translate("multiqc"),
                    "field": "multiqc",
                    "sortable": True,
                    "type": FieldType.string,
                    "filterable": True,
                    "width": 60,
                },
                {
                    "id": "feature_inference",
                    "name": translate_service.translate("feature_inference"),
                    "field": "feature_inference",
                    "sortable": True,
                    "type": FieldType.string,
                    "filterable": True,
                    "width": 60,
                },
                {
                    "id": "rarefaction",
                    "name": translate_service.translate("rarefaction"),
                    "field": "rarefaction",
                    "sortable": True,
                    "type": FieldType.string,
                    "filterable": True,
                    "width": 60,
                },
                {
                    "id": "taxonomy",
                    "name": translate_service.translate("taxonomy"),
                    "field": "taxonomy",
                    "sortable": True,
                    "type": FieldType.string,
                    "filterable": True,
                    "width": 60,
                },
                {
                    "id": "pcoa",
                    "name": translate_service.translate("pcoa"),
                    "field": "pcoa",
                    "sortable": True,
                    "type": FieldType.string,
                    "filterable": True,
                    "width": 40,
                },
                {
                    "id": "ancom",
                    "name": translate_service.translate("ancom"),
                    "field": "ancom",
                    "sortable": True,
                    "type": FieldType.string,
                    "filterable": True,
                    "width": 50,
                },
                {
                    "id": "db_annotator",
                    "name": translate_service.translate("taxa_composition"),
                    "field": "db_annotator",
                    "sortable": True,
                    "type": FieldType.string,
                    "filterable": True,
                    "width": 70,
                },
            ]

            # Add ratio column if enabled
            if ubiome_state.get_has_ratio_step():
                columns.append({
                    "id": "ratio",
                    "name": translate_service.translate("ratio"),
                    "field": "ratio",
                    "sortable": True,
                    "type": FieldType.string,
                    "filterable": True,
                    "width": 50,
                })

            # Add remaining columns after ratio
            columns.extend([
                {
                    "id": "16S",
                    "name": translate_service.translate("16s_functional"),
                    "field": "16S",
                    "sortable": True,
                    "type": FieldType.string,
                    "filterable": True,
                    "width": 60,
                },
                {
                    "id": "16S_visualization",
                    "name": translate_service.translate("16s_visualization"),
                    "field": "16S_visualization",
                    "sortable": True,
                    "type": FieldType.string,
                    "filterable": True,
                    "width": 65,
                },
            ])

            options = {
                "enableFiltering": True,
                "enableTextExport": True,
                "enableExcelExport": True,
                "enableColumnPicker": True,
                "externalResources": [
                    ExportServices.ExcelExportService,
                    ExportServices.TextExportService,
                ],
                "autoResize": {
                    "minHeight": 400,
                },
                "multiColumnSort": False,
            }

            out = slickgrid(table_data, columns=columns, options=options, key="analysis_grid", on_click="rerun")

            if out is not None:
                row_id, col = out
                if col != 0 and col != 1: # because two first columns are not related to a step
                    # Parse the table_data to find the scenario with the matching id
                    dict_id = next((entry for entry in table_data if entry["id"] == row_id), None)
                    # Parse the dict_id and keep the n key where n is the number given by the col variable
                    n = 0
                    for key, value in dict_id.items():
                        if n == col+1:# because first column is the id (not displayed)
                            if value != "":
                                selected_scenario = next((s for s in list_scenario_user if s.id == row_id), None)
                                ubiome_state.set_selected_analysis(selected_scenario)
                                # Get analysis name from scenario tag
                                entity_tag_list = EntityTagList.find_by_entity(TagEntityType.SCENARIO, selected_scenario.id)

                                # Get ubiome pipeline id from scenario tag
                                tag_ubiome_pipeline_id = entity_tag_list.get_tags_by_key(ubiome_state.TAG_UBIOME_PIPELINE_ID)[0].to_simple_tag()
                                ubiome_pipeline_id = tag_ubiome_pipeline_id.value

                                # Build scenarios_by_step dictionary using helper function
                                scenarios_by_step = build_scenarios_by_step_dict(ubiome_pipeline_id, ubiome_state)
                                ubiome_state.set_scenarios_by_step_dict(scenarios_by_step)
                                if isinstance(ubiome_state.get_scenarios_by_step_dict().get(key), list):
                                    list_scenario = ubiome_state.get_scenarios_by_step_dict().get(key)
                                    # Get the most recent scenario for this step
                                    latest_scenario = max(list_scenario, key=lambda x: x.created_at)
                                    ubiome_state.set_tree_default_item(latest_scenario.id)
                                elif isinstance(ubiome_state.get_scenarios_by_step_dict().get(key), dict):
                                    keys_parent = list(ubiome_state.get_scenarios_by_step_dict().get(key))
                                    list_scenario = []
                                    for key_parent in keys_parent:
                                        for scenario in ubiome_state.get_scenarios_by_step_dict().get(key).get(key_parent):
                                            list_scenario.append(scenario)
                                    # Get the most recent scenario for this step
                                    latest_scenario = max(list_scenario, key=lambda x: x.created_at)
                                    ubiome_state.set_tree_default_item(latest_scenario.id)

                                router = StreamlitRouter.load_from_session()
                                router.navigate("analysis")
                            break
                        n +=1

                # Handle row click
                selected_scenario = next((s for s in list_scenario_user if s.id == row_id), None)
                if selected_scenario:
                    ubiome_state.set_selected_analysis(selected_scenario)
                    router = StreamlitRouter.load_from_session()
                    router.navigate("analysis")

        else:
            st.info(translate_service.translate("no_recipe_found"))
