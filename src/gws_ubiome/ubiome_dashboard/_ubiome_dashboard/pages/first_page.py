import streamlit as st
from state import State
from typing import List
from gws_core.streamlit import StreamlitContainers, StreamlitRouter
from gws_core import Tag, ScenarioSearchBuilder, Scenario
from gws_core.tag.tag_entity_type import TagEntityType
from gws_core.tag.entity_tag_list import EntityTagList
from gws_ubiome.ubiome_dashboard._ubiome_dashboard.functions_steps import get_status_emoji
from streamlit_slickgrid import (
    slickgrid,
    FieldType,
    ExportServices,
)

def render_first_page(ubiome_state : State):

    # Add a button create new analysis using config
    # Create a container for the header with project title and action buttons
    col_empty, col_button_new = StreamlitContainers.columns_with_fit_content(
            key="button_new",
            cols=[1, 'fit-content'], vertical_align_items='center')

    with col_button_new:
        if st.button("Create new analysis", icon=":material/add:", use_container_width=False):
            # On click, navigate to a hidden page 'run new analysis'
            router = StreamlitRouter.load_from_session()
            router.navigate("new-analysis")


    # Add the table to retrieve the previous analysis
    st.markdown("## Retrieve Analysis")

    search_scenario_builder = ScenarioSearchBuilder() \
        .add_tag_filter(Tag(key=ubiome_state.TAG_BRICK, value=ubiome_state.TAG_UBIOME)) \
        .add_tag_filter(Tag(key=ubiome_state.TAG_UBIOME, value=ubiome_state.TAG_METADATA)) \
        .add_is_archived_filter(False)

    # We got here all the metadata scenarios
    list_scenario_user: List[Scenario] = search_scenario_builder.search_all()

    # Create data for SlickGrid table
    table_data = []
    for scenario in list_scenario_user:
        entity_tag_list = EntityTagList.find_by_entity(TagEntityType.SCENARIO, scenario.id)
        tag_analysis_name = entity_tag_list.get_tags_by_key(ubiome_state.TAG_ANALYSIS_NAME)[0].to_simple_tag()
        tag_fastq_name = entity_tag_list.get_tags_by_key(ubiome_state.TAG_FASTQ)[0].to_simple_tag()

        # Get pipeline ID to find all related scenarios
        pipeline_id_tags = entity_tag_list.get_tags_by_key(ubiome_state.TAG_UBIOME_PIPELINE_ID)
        if pipeline_id_tags:
            pipeline_id = pipeline_id_tags[0].to_simple_tag().value

            # Search for all scenarios with this pipeline ID
            pipeline_search_builder = ScenarioSearchBuilder() \
                .add_tag_filter(Tag(key=ubiome_state.TAG_UBIOME_PIPELINE_ID, value=pipeline_id)) \
                .add_is_archived_filter(False)

            pipeline_scenarios = pipeline_search_builder.search_all()

            # Create overview of step statuses
            step_statuses = []
            step_statuses.append(f"metadata: {get_status_emoji(scenario.status)}")

            # Check each step type
            step_types = [
                (ubiome_state.TAG_QC, "qc"),
                (ubiome_state.TAG_MULTIQC, "multiqc"),
                (ubiome_state.TAG_FEATURE_INFERENCE, "feature inference"),
                (ubiome_state.TAG_RAREFACTION, "rarefaction"),
                (ubiome_state.TAG_TAXONOMY, "taxonomy"),
                (ubiome_state.TAG_PCOA_DIVERSITY, "pcoa"),
                (ubiome_state.TAG_ANCOM, "ancom"),
                (ubiome_state.TAG_DB_ANNOTATOR, "taxa composition"),
                (ubiome_state.TAG_16S, "16s functional"),
                (ubiome_state.TAG_16S_VISU, "16s visualization")
            ]

            for tag_value, display_name in step_types:
                step_scenarios = [s for s in pipeline_scenarios if any(
                    tag.tag_key == ubiome_state.TAG_UBIOME and tag.tag_value == tag_value
                    for tag in EntityTagList.find_by_entity(TagEntityType.SCENARIO, s.id).get_tags()
                )]

                if step_scenarios:
                    # Get the most recent scenario for this step
                    latest_scenario = max(step_scenarios, key=lambda x: x.created_at)
                    step_statuses.append(f"{display_name}: {get_status_emoji(latest_scenario.status)}")

            overview = "\n".join(step_statuses)
        else:
            overview = f"metadata: {get_status_emoji(scenario.status)}"

        table_data.append({
            "id": scenario.id,
            "Name given": tag_analysis_name.value,
            "Folder": scenario.folder.name if scenario.folder else "",
            "Fastq name": tag_fastq_name.value,
            "Overview": overview
        })

    if table_data:
        columns = [
            {
                "id": "Name given",
                "name": "Analysis name",
                "field": "Name given",
                "sortable": True,
                "type": FieldType.string,
                "filterable": True,
            },
            {
                "id": "Folder",
                "name": "Folder",
                "field": "Folder",
                "sortable": True,
                "type": FieldType.string,
                "filterable": True,
            },
            {
                "id": "Fastq name",
                "name": "Fastq name",
                "field": "Fastq name",
                "sortable": True,
                "type": FieldType.string,
                "filterable": True,
            },
            {
                "id": "Overview",
                "name": "Status overview",
                "field": "Overview",
                "sortable": False,
                "type": FieldType.string,
                "filterable": True,
                "width": 300,
            },
        ]

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
            # Handle row click
            selected_scenario = next((s for s in list_scenario_user if s.id == row_id), None)
            if selected_scenario:
                ubiome_state.set_selected_analysis(selected_scenario)
                router = StreamlitRouter.load_from_session()
                router.navigate("analysis")

    else:
        st.info("No analysis found.")
