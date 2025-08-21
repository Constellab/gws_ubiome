import streamlit as st
from state import State
from typing import List, Dict
from gws_core.streamlit import StreamlitContainers, StreamlitRouter
from gws_ubiome.ubiome_dashboard._ubiome_dashboard.ubiome_config import UbiomeConfig
import pandas as pd
from gws_core import Tag, ScenarioSearchBuilder, TagValueModel, Scenario, ScenarioStatus
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

    # Create two columns
    left_col, right_col = st.columns([1, 4])

    # Left column - Home button
    with left_col:
        # Button to go home using config
        if ubiome_config.build_home_button():
            router.navigate("first-page")

    # Right column - Table with vertical separator
    with right_col:
        # Add vertical line to separate the two columns
        style = """
        [CLASS_NAME] {
            border-left: 2px solid #ccc;
            min-height: 100vh;
            padding-left: 20px !important;
        }
        """
        with StreamlitContainers.container_with_style('first-page-container', style):
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
            st.write("Retrieve Analysis")

            search_scenario_builder = ScenarioSearchBuilder() \
                .add_tag_filter(Tag(key=ubiome_state.TAG_BRICK, value=ubiome_state.TAG_UBIOME)) \
                .add_tag_filter(Tag(key=ubiome_state.TAG_UBIOME, value=ubiome_state.TAG_METADATA)) \
                .add_is_archived_filter(False)

            # We got here all the metadata scenarios
            list_scenario_user: List[Scenario] = search_scenario_builder.search_all()

            # Create data for SlickGrid table
            table_data = []
            for scenario in list_scenario_user:
                table_data.append({
                    "id": scenario.id,
                    "Name given": scenario.get_short_name(),# TODO : get the name from the tag
                    "Folder": scenario.folder, # TODO : get the folder associated to the scenario
                    "Fastq name": "", # TODO get the fastq name from the tags
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









