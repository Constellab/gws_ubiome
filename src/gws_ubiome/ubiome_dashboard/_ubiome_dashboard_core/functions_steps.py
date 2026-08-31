import numpy as np
import pandas as pd
import streamlit as st
from gws_core import (
    File,
    ProtocolProxy,
    Scenario,
    ScenarioProxy,
    ScenarioStatus,
)
from gws_streamlit_main import StreamlitTaskRunner
from streamlit_slickgrid import (
    ExportServices,
    FieldType,
    slickgrid,
)

from .state import State
from .ubiome_scenario_service import UbiomeScenarioService


def get_status_emoji(status: ScenarioStatus) -> str:
    """Return appropriate emoji for scenario status"""
    return UbiomeScenarioService.get_status_emoji(status)


def get_status_prettify(status: ScenarioStatus) -> str:
    """Return a human-readable string for scenario status"""
    return UbiomeScenarioService.get_status_prettify(status)


# Generic helper functions
def create_scenario_table_data(scenarios: list[Scenario], process_name: str) -> tuple:
    """Generic function to create table data from scenarios with their parameters."""
    return UbiomeScenarioService.create_scenario_table_data(scenarios, process_name)


def create_slickgrid_columns(param_keys: set, ubiome_state: State) -> list[dict]:
    """Generic function to create SlickGrid columns."""
    translate_service = ubiome_state.get_translate_service()
    columns = [
        {
            "id": "Scenario Name",
            "name": translate_service.translate("scenario_name"),
            "field": "Scenario Name",
            "sortable": True,
            "type": FieldType.string,
            "filterable": True,
            "width": 200,
        },
        {
            "id": "Creation Date",
            "name": translate_service.translate("creation_date"),
            "field": "Creation Date",
            "sortable": True,
            "type": FieldType.string,
            "filterable": True,
            "width": 100,
        },
        {
            "id": "Status",
            "name": translate_service.translate("status"),
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
        columns.append(
            {
                "id": param_key,
                "name": column_name,
                "field": param_key,
                "sortable": True,
                "type": FieldType.string,
                "filterable": True,
                "width": 70,
            }
        )

    return columns


def render_scenario_table(
    scenarios: list[Scenario], process_name: str, grid_key: str, ubiome_state: State
) -> None:
    """Generic function to render a scenario table with parameters."""
    translate_service = ubiome_state.get_translate_service()
    if scenarios:
        table_data, all_param_keys = create_scenario_table_data(scenarios, process_name)
        columns = create_slickgrid_columns(all_param_keys, ubiome_state)

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

        out = slickgrid(
            table_data, columns=columns, options=options, key=grid_key, on_click="rerun"
        )

        if out is not None:
            row_id, col = out
            selected_scenario = next((s for s in scenarios if s.id == row_id), None)
            if selected_scenario:
                ubiome_state.update_tree_menu_selection(selected_scenario.id)
                st.rerun()
    else:
        st.info(
            f"{translate_service.translate('no_analyses_found_prefix')} {process_name.replace('_', ' ').title()} {translate_service.translate('no_analyses_found')}"
        )


def display_scenario_parameters(scenario: Scenario, process_name: str, ubiome_state: State) -> None:
    """Generic function to display scenario parameters in an expander."""
    translate_service = ubiome_state.get_translate_service()
    task_name, config_params = UbiomeScenarioService.get_scenario_process_info(
        scenario.id, process_name
    )

    with st.expander(f"{translate_service.translate('parameters')} - {task_name}"):
        param_data = [
            {
                translate_service.translate("parameter"): translate_service.translate("task"),
                translate_service.translate("value"): task_name,
            }
        ]

        for key, value in config_params.items():
            readable_key = key.replace("_", " ").replace("-", " ").title()
            param_data.append(
                {
                    translate_service.translate("parameter"): readable_key,
                    translate_service.translate("value"): str(value),
                }
            )

        if param_data:
            st.dataframe(pd.DataFrame(param_data), width="stretch", hide_index=True)


def export_scenario_to_lab_large(scenario_id: str, credentials, translate_service) -> None:
    """Export a scenario to Lab Large and display success/error feedback."""
    try:
        with st.spinner(translate_service.translate("sending_data")):
            UbiomeScenarioService.export_scenario_to_lab_large(scenario_id, credentials)
        st.success(translate_service.translate("data_sent_successfully"))
    except Exception:
        st.error(translate_service.translate("error_sending_data"))


def create_base_scenario_with_tags(ubiome_state: State, step_tag: str, title: str) -> ScenarioProxy:
    """Create a new scenario with the standard ubiome base tags."""
    return UbiomeScenarioService.create_base_scenario_with_tags(
        folder_id=ubiome_state.get_selected_folder_id(),
        step_tag=step_tag,
        title=title,
        fastq_name=ubiome_state.get_current_fastq_name(),
        analysis_name=ubiome_state.get_current_analysis_name(),
        pipeline_id=ubiome_state.get_current_ubiome_pipeline_id(),
    )


def save_metadata_table(
    edited_df: pd.DataFrame, header_lines: list[str], ubiome_state: State, protocol: ProtocolProxy
) -> None:
    """Save metadata table to resource."""
    existing_resource = search_updated_metadata_table(ubiome_state)
    metadata_model_id = UbiomeScenarioService.save_metadata_table_to_resource(
        edited_df=edited_df,
        header_lines=header_lines,
        analysis_name=ubiome_state.get_current_analysis_name(),
        pipeline_id=ubiome_state.get_current_ubiome_pipeline_id(),
        protocol=protocol,
        existing_resource=existing_resource,
    )
    ubiome_state.set_resource_id_metadata_table(metadata_model_id)


@st.dialog("Add New Metadata Column")
def add_new_column_dialog(
    ubiome_state: State, header_lines: list[str], protocol_proxy: ProtocolProxy
) -> None:
    translate_service = ubiome_state.get_translate_service()
    st.text_input(
        translate_service.translate("new_column_name"),
        placeholder=translate_service.translate("enter_column_name"),
        key=UbiomeScenarioService.NEW_COLUMN_INPUT_KEY,
    )
    if st.button(translate_service.translate("add_column"), width="stretch", key="add_column_btn"):
        df_metadata = ubiome_state.get_edited_df_metadata()
        if not ubiome_state.get_new_column_name():
            st.warning("Please enter a column name")
            return

        column_name = ubiome_state.get_new_column_name()
        if column_name in df_metadata.columns:
            st.warning(f"'{column_name}' : {translate_service.translate('column_already_exists')}")
            return

        # Add new column with NaN values
        df_metadata[column_name] = np.nan

        # Use the helper function to save
        save_metadata_table(df_metadata, header_lines, ubiome_state, protocol_proxy)

        st.rerun()


def add_tags_on_metadata(edited_metadata: File, ubiome_state: State) -> None:
    """Add tags on metadata resource."""
    metadata_model_id = edited_metadata.get_model_id()
    UbiomeScenarioService.add_tags_on_metadata_resource(
        metadata_model_id=metadata_model_id,
        pipeline_id=ubiome_state.get_current_ubiome_pipeline_id(),
    )
    ubiome_state.set_resource_id_metadata_table(metadata_model_id)


def search_updated_metadata_table(ubiome_state: State) -> File | None:
    """Search for an updated metadata table resource in the current metadata scenario."""
    metadata_scenarios = ubiome_state.get_scenario_step_metadata()
    return UbiomeScenarioService.search_updated_metadata_table(metadata_scenarios[0].id)


def build_scenarios_by_step_dict(
    ubiome_pipeline_id: str, ubiome_state: State
) -> dict[str, list | dict]:
    """Build scenarios_by_step dictionary for a given ubiome_pipeline_id."""
    return UbiomeScenarioService.build_scenarios_by_step_dict(
        ubiome_pipeline_id=ubiome_pipeline_id,
        has_ratio_step=ubiome_state.get_has_ratio_step(),
    )


def display_saved_scenario_actions(scenario: Scenario, ubiome_state: State) -> None:
    """Display Run and Edit actions for saved scenarios."""
    translate_service = ubiome_state.get_translate_service()
    step_tag = UbiomeScenarioService.get_scenario_step_tag(scenario.id)

    # if there is a param credential to lab large entered in the dashboard, we will send the scenario to lab large to be executed
    # so the lab large need to be open
    if step_tag == UbiomeScenarioService.TAG_16S and ubiome_state.get_credentials_lab_large():
        st.info(translate_service.translate("lab_large_must_be_open"))
    col1, col2 = st.columns(2)

    with col1:
        if st.button(
            translate_service.translate("run"),
            icon=":material/play_arrow:",
            key=f"run_{scenario.id}",
            width="stretch",
        ):
            if (
                step_tag == UbiomeScenarioService.TAG_16S
                and ubiome_state.get_credentials_lab_large()
            ):
                export_scenario_to_lab_large(
                    scenario.id,
                    ubiome_state.get_credentials_lab_large(),
                    translate_service,
                )
            else:
                UbiomeScenarioService.run_scenario(scenario.id)
            ubiome_state.reset_tree_analysis()
            ubiome_state.set_tree_default_item(scenario.id)
            st.rerun()

    with col2:
        if st.button(
            translate_service.translate("edit"),
            icon=":material/edit:",
            key=f"edit_{scenario.id}",
            width="stretch",
        ):
            dialog_edit_scenario_params(scenario, ubiome_state)


@st.dialog("Edit Scenario Parameters")
def dialog_edit_scenario_params(scenario: Scenario, ubiome_state: State):
    """Dialog to edit scenario parameters with Save and Run options."""
    translate_service = ubiome_state.get_translate_service()

    try:
        step_tag, task_class, current_config = UbiomeScenarioService.get_scenario_edit_data(
            scenario.id
        )
    except Exception as e:
        st.error(str(e))
        return

    # Create a unique session state key for this edit dialog
    edit_config_key = f"edit_config_{scenario.id}"

    # Initialize the form with current configuration
    form_config = StreamlitTaskRunner(task_class)
    form_config.generate_config_form_without_run(
        session_state_key=edit_config_key,
        default_config_values=current_config,
        is_default_config_valid=True,
    )

    if step_tag == UbiomeScenarioService.TAG_16S and ubiome_state.get_credentials_lab_large():
        st.info(translate_service.translate("lab_large_must_be_open"))

    # Add Save and Run buttons
    col1, col2 = st.columns(2)

    with col1:
        save_clicked = st.button(
            translate_service.translate("save_changes"),
            icon=":material/save:",
            width="stretch",
            key=f"save_edit_{scenario.id}",
        )

    with col2:
        run_clicked = st.button(
            translate_service.translate("save_and_run"),
            icon=":material/play_arrow:",
            width="stretch",
            key=f"run_edit_{scenario.id}",
        )

    if save_clicked or run_clicked:
        # Get the updated configuration from session state
        updated_config = st.session_state.get(edit_config_key, {}).get("config", {})

        if not st.session_state.get(edit_config_key, {}).get("is_valid", False):
            st.warning(translate_service.translate("fill_mandatory_fields"))
            return

        # Update the process configuration
        UbiomeScenarioService.update_scenario_process_config(scenario.id, updated_config)

        if run_clicked:
            # If run is clicked, also add to queue
            if (
                step_tag == UbiomeScenarioService.TAG_16S
                and ubiome_state.get_credentials_lab_large()
            ):
                export_scenario_to_lab_large(
                    scenario.id,
                    ubiome_state.get_credentials_lab_large(),
                    translate_service,
                )
            else:
                UbiomeScenarioService.run_scenario(scenario.id)
            ubiome_state.reset_tree_analysis()
            ubiome_state.set_tree_default_item(scenario.id)

        # Clear the edit session state
        if edit_config_key in st.session_state:
            del st.session_state[edit_config_key]

        st.rerun()
