import os
from typing import List, Dict
import streamlit as st
import numpy as np
import pandas as pd
from streamlit_slickgrid import (
    slickgrid,
    FieldType,
    ExportServices,
)
from gws_ubiome.ubiome_dashboard._ubiome_dashboard_core.state import State
from gws_core.streamlit import StreamlitAuthenticateUser
from gws_core import ScenarioSearchBuilder, Settings, ResourceModel, ResourceOrigin, Scenario, ScenarioProxy, File, SpaceFolder, Tag, Scenario, ScenarioStatus, ScenarioProxy, ScenarioCreationType
from gws_core.tag.tag_entity_type import TagEntityType
from gws_core.tag.entity_tag_list import EntityTagList
from gws_core.tag.entity_tag import EntityTag
from gws_core.tag.tag import TagOrigin

def get_status_emoji(status: ScenarioStatus) -> str:
    """Return appropriate emoji for scenario status"""
    emoji_map = {
        ScenarioStatus.DRAFT: "📝",
        ScenarioStatus.IN_QUEUE: "⏳",
        ScenarioStatus.WAITING_FOR_CLI_PROCESS: "⏸️",
        ScenarioStatus.RUNNING: "🔄",
        ScenarioStatus.SUCCESS: "✅",
        ScenarioStatus.ERROR: "❌",
        ScenarioStatus.PARTIALLY_RUN: "✔️"
    }
    return emoji_map.get(status, "")

def get_status_prettify(status: ScenarioStatus) -> str:
    """Return a human-readable string for scenario status"""
    prettify_map = {
        ScenarioStatus.DRAFT: "Draft",
        ScenarioStatus.IN_QUEUE: "In Queue",
        ScenarioStatus.WAITING_FOR_CLI_PROCESS: "Waiting",
        ScenarioStatus.RUNNING: "Running",
        ScenarioStatus.SUCCESS: "Success",
        ScenarioStatus.ERROR: "Error",
        ScenarioStatus.PARTIALLY_RUN: "Partially Run"
    }
    return prettify_map.get(status, "")

# Generic helper functions
def create_scenario_table_data(scenarios: List[Scenario], process_name: str) -> tuple:
    """Generic function to create table data from scenarios with their parameters."""
    table_data = []
    all_param_keys = set()
    scenarios_params = []

    # First pass: collect all parameter data and unique keys
    for scenario in scenarios:
        scenario_proxy = ScenarioProxy.from_existing_scenario(scenario.id)
        protocol_proxy = scenario_proxy.get_protocol()
        process = protocol_proxy.get_process(process_name)
        config_params = process._process_model.config.to_simple_dto().values

        # For PCOA scenarios, add diversity table name from input resource
        if process_name == 'pcoa_process':
            config_params["Diversity Table"] = process.get_input('distance_table').name.split(" - ")[1]

        scenarios_params.append((scenario, config_params))
        all_param_keys.update(config_params.keys())

    # Second pass: create table data with all parameters
    for scenario, config_params in scenarios_params:
        row_data = {
            "id": scenario.id,
            "Scenario Name": scenario.title,
            "Creation Date": scenario.created_at.strftime("%Y-%m-%d %H:%M") if scenario.created_at else "",
            "Status": f"{get_status_emoji(scenario.status)} {get_status_prettify(scenario.status)}" if scenario.status else ""
        }

        # Add each parameter as a separate column
        for param_key in all_param_keys:
            row_data[param_key] = config_params.get(param_key, "")

        table_data.append(row_data)

    return table_data, all_param_keys

def create_slickgrid_columns(param_keys: set) -> List[Dict]:
    """Generic function to create SlickGrid columns."""
    columns = [
        {
            "id": "Scenario Name",
            "name": "Scenario Name",
            "field": "Scenario Name",
            "sortable": True,
            "type": FieldType.string,
            "filterable": True,
            "width": 200,
        },
        {
            "id": "Creation Date",
            "name": "Creation Date",
            "field": "Creation Date",
            "sortable": True,
            "type": FieldType.string,
            "filterable": True,
            "width": 100,
        },
        {
            "id": "Status",
            "name": "Status",
            "field": "Status",
            "sortable": True,
            "type": FieldType.string,
            "filterable": True,
            "width": 60,
        },
    ]

    # Add parameter columns
    for param_key in sorted(param_keys):
        column_name = param_key.replace("_", " ").replace("-", " ").title()
        columns.append({
            "id": param_key,
            "name": column_name,
            "field": param_key,
            "sortable": True,
            "type": FieldType.string,
            "filterable": True,
            "width": 70,
        })

    return columns

def render_scenario_table(scenarios: List[Scenario], process_name: str, grid_key: str, ubiome_state: State) -> None:
    """Generic function to render a scenario table with parameters."""
    if scenarios:
        table_data, all_param_keys = create_scenario_table_data(scenarios, process_name)
        columns = create_slickgrid_columns(all_param_keys)

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

        out = slickgrid(table_data, columns=columns, options=options, key=grid_key, on_click="rerun")

        if out is not None:
            row_id, col = out
            selected_scenario = next((s for s in scenarios if s.id == row_id), None)
            if selected_scenario:
                ubiome_state.update_tree_menu_selection(selected_scenario.id)
                st.rerun()
    else:
        st.info(f"No {process_name.replace('_', ' ').title()} analyses found.")

def display_scenario_parameters(scenario: Scenario, process_name: str) -> None:
    """Generic function to display scenario parameters in an expander."""
    scenario_proxy = ScenarioProxy.from_existing_scenario(scenario.id)
    protocol_proxy = scenario_proxy.get_protocol()
    process = protocol_proxy.get_process(process_name)
    config_params = process._process_model.config.to_simple_dto().values

    # Add task name to parameters
    readable_task_name = process._process_model.name

    with st.expander(f"Parameters - {readable_task_name}"):
        param_data = []

        # Add task name as first parameter
        param_data.append({
            "Parameter": "Task",
            "Value": readable_task_name
        })

        for key, value in config_params.items():
            readable_key = key.replace("_", " ").replace("-", " ").title()
            param_data.append({
                "Parameter": readable_key,
                "Value": str(value)
            })

        if param_data:
            param_df = pd.DataFrame(param_data)
            st.dataframe(param_df, use_container_width=True, hide_index=True)

def create_base_scenario_with_tags(ubiome_state: State, step_tag: str, title: str) -> ScenarioProxy:
    """Generic function to create a scenario with base tags."""
    folder : SpaceFolder = SpaceFolder.get_by_id(ubiome_state.get_selected_folder_id())
    scenario: ScenarioProxy = ScenarioProxy(
        None, folder=folder,
        title=title,
        creation_type=ScenarioCreationType.MANUAL,
    )

    # Add base tags
    scenario.add_tag(Tag(ubiome_state.TAG_FASTQ, ubiome_state.get_current_fastq_name(), is_propagable=False, auto_parse=True))
    scenario.add_tag(Tag(ubiome_state.TAG_BRICK, ubiome_state.TAG_UBIOME, is_propagable=False, auto_parse=True))
    scenario.add_tag(Tag(ubiome_state.TAG_UBIOME, step_tag, is_propagable=False))
    scenario.add_tag(Tag(ubiome_state.TAG_ANALYSIS_NAME, ubiome_state.get_current_analysis_name(), is_propagable=False, auto_parse=True))
    scenario.add_tag(Tag(ubiome_state.TAG_UBIOME_PIPELINE_ID, ubiome_state.get_current_ubiome_pipeline_id(), is_propagable=False, auto_parse=True))

    return scenario

def save_metadata_table(edited_df: pd.DataFrame, header_lines: List[str], ubiome_state: State) -> None:
    """
    Helper function to save metadata table to resource.
    """

    # Search for existing updated metadata resource
    existing_resource = search_updated_metadata_table(ubiome_state)

    # If there's an existing resource, delete it first
    if existing_resource:
        ResourceModel.get_by_id(existing_resource.get_model_id()).delete_instance()

    # Create a new file with the updated content
    path_temp = os.path.join(os.path.abspath(os.path.dirname(__file__)), Settings.make_temp_dir())
    full_path = os.path.join(path_temp, f"{ubiome_state.get_current_analysis_name()}_Metadata_updated.txt")

    # Prepare content to save
    content_to_save = ""
    if header_lines:
        content_to_save = '\n'.join(header_lines) + '\n'
    content_to_save += edited_df.to_csv(index=False, sep='\t')

    # Write content to file
    with open(full_path, 'w') as f:
        f.write(content_to_save)

    # Create File resource and save it properly using save_from_resource
    metadata_file = File(full_path)

    # Use save_from_resource which properly handles fs_node creation
    resource_model = ResourceModel.save_from_resource(
        metadata_file,
        origin=ResourceOrigin.UPLOADED,
        flagged=True
    )

    # Add tags using EntityTagList
    user_origin = TagOrigin.current_user_origin()
    entity_tags = EntityTagList(TagEntityType.RESOURCE, resource_model.id, default_origin=user_origin)

    # Add the required tags
    entity_tags.add_tag(Tag(ubiome_state.TAG_UBIOME, ubiome_state.TAG_METADATA_UPDATED, is_propagable=False))
    entity_tags.add_tag(Tag(ubiome_state.TAG_UBIOME_PIPELINE_ID, ubiome_state.get_current_ubiome_pipeline_id(), is_propagable=False))

    ubiome_state.set_resource_id_metadata_table(resource_model.id)

@st.dialog("Add New Metadata Column")
def add_new_column_dialog(ubiome_state: State, header_lines: List[str]):
    st.text_input("New column name:", placeholder="Enter column name", key=ubiome_state.NEW_COLUMN_INPUT_KEY)
    if st.button("Add Column", use_container_width=True, key="add_column_btn"):
        df_metadata = ubiome_state.get_edited_df_metadata()
        if not ubiome_state.get_new_column_name():
            st.warning("Please enter a column name")
            return

        column_name = ubiome_state.get_new_column_name()
        if column_name in df_metadata.columns:
            st.warning(f"Column '{column_name}' already exists.")
            return

        with StreamlitAuthenticateUser():
            # Add new column with NaN values
            df_metadata[column_name] = np.nan

            # Use the helper function to save
            save_metadata_table(df_metadata, header_lines, ubiome_state)

            st.rerun()

def search_updated_metadata_table(ubiome_state: State) -> File | None:
    """
    Helper function to search for updated metadata table resource.
    Returns the File resource if found, None otherwise.
    """
    try:
        # Search for existing updated metadata resource
        pipeline_id_entities = EntityTag.select().where(
            (EntityTag.entity_type == TagEntityType.RESOURCE) &
            (EntityTag.tag_key == ubiome_state.TAG_UBIOME_PIPELINE_ID) &
            (EntityTag.tag_value == ubiome_state.get_current_ubiome_pipeline_id())
        )

        metadata_updated_entities = EntityTag.select().where(
            (EntityTag.entity_type == TagEntityType.RESOURCE) &
            (EntityTag.tag_key == ubiome_state.TAG_UBIOME) &
            (EntityTag.tag_value == ubiome_state.TAG_METADATA_UPDATED)
        )

        pipeline_id_entity_ids = [entity.entity_id for entity in pipeline_id_entities]
        metadata_updated_entity_ids = [entity.entity_id for entity in metadata_updated_entities]
        common_entity_ids = list(set(pipeline_id_entity_ids) & set(metadata_updated_entity_ids))

        if common_entity_ids:
            metadata_table_resource_search = ResourceModel.select().where(
                (ResourceModel.id.in_(common_entity_ids)) &
                (ResourceModel.resource_typing_name.contains('File'))
            )
            updated_resource = metadata_table_resource_search.first()

            if updated_resource:
                return updated_resource.get_resource()

    except Exception:
        pass

    return None


def build_scenarios_by_step_dict(ubiome_pipeline_id: str, ubiome_state: State) -> Dict[str, List[Scenario]]:
    """
    Build scenarios_by_step dictionary for a given ubiome_pipeline_id.

    Args:
        ubiome_pipeline_id: The pipeline ID to search for scenarios
        ubiome_state: State object containing tag constants

    Returns:
        Dictionary mapping step names to lists of scenarios
    """
    ubiome_pipeline_id_parsed = Tag.parse_tag(ubiome_pipeline_id)

    # Get all scenarios for this analysis, we retrieve all the other thanks to the id ubiome pipeline id
    search_scenario_builder = ScenarioSearchBuilder() \
        .add_tag_filter(Tag(key=ubiome_state.TAG_UBIOME_PIPELINE_ID, value=ubiome_pipeline_id_parsed, auto_parse=True)) \
        .add_is_archived_filter(False)

    all_scenarios: List[Scenario] = search_scenario_builder.search_all()

    # Group scenarios by step type with parent relationships
    scenarios_by_step = {}
    for scenario in all_scenarios:
        entity_tag_list = EntityTagList.find_by_entity(TagEntityType.SCENARIO, scenario.id)
        tag_step_name = entity_tag_list.get_tags_by_key(ubiome_state.TAG_UBIOME)[0].to_simple_tag()
        step_name = tag_step_name.value

        if step_name in [ubiome_state.TAG_METADATA, ubiome_state.TAG_QC, ubiome_state.TAG_MULTIQC, ubiome_state.TAG_FEATURE_INFERENCE]:
            # These steps don't have parent dependencies
            if step_name not in scenarios_by_step:
                scenarios_by_step[step_name] = []
            scenarios_by_step[step_name].append(scenario)
        elif step_name in [ubiome_state.TAG_RAREFACTION, ubiome_state.TAG_TAXONOMY, ubiome_state.TAG_16S, ubiome_state.TAG_16S_VISU]:
            # These steps depend on feature inference
            feature_id_tags = entity_tag_list.get_tags_by_key(ubiome_state.TAG_FEATURE_INFERENCE_ID)
            if feature_id_tags:
                parent_id = feature_id_tags[0].to_simple_tag().value
                if step_name not in scenarios_by_step:
                    scenarios_by_step[step_name] = {}
                if parent_id not in scenarios_by_step[step_name]:
                    scenarios_by_step[step_name][parent_id] = []
                scenarios_by_step[step_name][parent_id].append(scenario)
        elif step_name in [ubiome_state.TAG_PCOA_DIVERSITY, ubiome_state.TAG_ANCOM, ubiome_state.TAG_DB_ANNOTATOR]:
            # These steps depend on taxonomy
            taxonomy_id_tags = entity_tag_list.get_tags_by_key(ubiome_state.TAG_TAXONOMY_ID)
            if taxonomy_id_tags:
                parent_id = taxonomy_id_tags[0].to_simple_tag().value
                if step_name not in scenarios_by_step:
                    scenarios_by_step[step_name] = {}
                if parent_id not in scenarios_by_step[step_name]:
                    scenarios_by_step[step_name][parent_id] = []
                scenarios_by_step[step_name][parent_id].append(scenario)

    return scenarios_by_step