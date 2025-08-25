import streamlit as st
from state import State
from typing import List, Dict
from gws_core.streamlit import StreamlitContainers, StreamlitRouter
from gws_ubiome.ubiome_dashboard._ubiome_dashboard.ubiome_config import UbiomeConfig
import pandas as pd
from gws_core import Tag, ScenarioSearchBuilder, TagValueModel, Scenario, ScenarioStatus, StringHelper
from gws_core.tag.tag_entity_type import TagEntityType
from gws_core.tag.entity_tag_list import EntityTagList
from streamlit_slickgrid import (
    slickgrid,
    Formatters,
    Filters,
    FieldType,
    ExportServices,
)

def render_first_page():
    # Get the config instance
    ubiome_config = UbiomeConfig.get_instance()
    ubiome_state = State()


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

        table_data.append({
            "id": scenario.id,
            "Name given": tag_analysis_name.value,
            "Folder": scenario.folder.name if scenario.folder else "",
            "Fastq name": tag_fastq_name.value,
            "Status": scenario.status.value if scenario.status else "" # TODO mettre le status de la dernière tâche ou de toutes
        })

    if table_data:
        columns = [
            {
                "id": "Name given",
                "name": "Name given",
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
                "id": "Status",
                "name": "Status",
                "field": "Status",
                "sortable": True,
                "type": FieldType.string,
                "filterable": True,
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
