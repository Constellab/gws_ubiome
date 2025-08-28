import os
from typing import List, Dict
import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
from state import State
from gws_core.streamlit import StreamlitAuthenticateUser, StreamlitContainers, StreamlitResourceSelect, StreamlitRouter, StreamlitTaskRunner
from gws_ubiome.ubiome_dashboard._ubiome_dashboard.ubiome_config import UbiomeConfig
import pandas as pd
from gws_core import FsNodeExtractor, Resource, Task, ResourceSet, Folder, Settings, ResourceModel, ResourceOrigin, Scenario, ScenarioProxy, ProtocolProxy, File, TableImporter, SpaceFolder, StringHelper, Tag, InputTask, SpaceService, ProcessProxy, ScenarioSearchBuilder, TagValueModel, Scenario, ScenarioStatus, ScenarioProxy, ProtocolProxy, ScenarioCreationType
from gws_ubiome import Qiime2QualityCheck, Qiime2FeatureTableExtractorPE, Qiime2FeatureTableExtractorSE, Qiime2RarefactionAnalysis, Qiime2TaxonomyDiversity, Qiime2DifferentialAnalysis, Qiime2TableDbAnnotator, Picrust2FunctionalAnalysis, Ggpicrust2FunctionalAnalysis
from gws_omix.rna_seq.multiqc.multiqc import MultiQc
from gws_omix.rna_seq.quality_check.fastq_init import FastqcInit

import streamlit.components.v1 as components
from streamlit_slickgrid import (
    slickgrid,
    Formatters,
    Filters,
    FieldType,
    ExportServices,
)
from gws_core.tag.tag_entity_type import TagEntityType
from gws_core.tag.entity_tag_list import EntityTagList
from gws_core.tag.entity_tag import EntityTag
from gws_core.tag.tag import TagOrigin
from gws_gaia import PCoATrainer


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
        scenarios_params.append((scenario, config_params))
        all_param_keys.update(config_params.keys())

    # Second pass: create table data with all parameters
    for scenario, config_params in scenarios_params:
        row_data = {
            "id": scenario.id,
            "Scenario Name": scenario.title,
            "Creation Date": scenario.created_at.strftime("%Y-%m-%d %H:%M") if scenario.created_at else "",
            "Status": scenario.status.value if scenario.status else ""
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
            "width": 150,
        },
        {
            "id": "Status",
            "name": "Status",
            "field": "Status",
            "sortable": True,
            "type": FieldType.string,
            "filterable": True,
            "width": 100,
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
            "width": 120,
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

    with st.expander("Parameters - Reminder"):
        param_data = []
        for key, value in config_params.items():
            readable_key = key.replace("_", " ").replace("-", " ").title()
            param_data.append({
                "Parameter": readable_key,
                "Value": str(value)
            })

        if param_data:
            param_df = pd.DataFrame(param_data)
            st.dataframe(param_df, use_container_width=True, hide_index=True)

def create_base_scenario_with_tags(ubiome_state: State, step_tag: str, title_suffix: str) -> ScenarioProxy:
    """Generic function to create a scenario with base tags."""
    folder = SpaceFolder.get_by_id(ubiome_state.get_selected_folder_id())
    scenario = ScenarioProxy(
        None, folder=folder,
        title=f"{ubiome_state.get_current_analysis_name()} - {title_suffix}",
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
        ResourceModel.get_by_id(existing_resource.id).delete_instance()

    # Create a new file with the updated content
    path_temp = os.path.join(os.path.abspath(os.path.dirname(__file__)), Settings.make_temp_dir())
    full_path = os.path.join(path_temp, f"Metadata_updated.txt")

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

def render_metadata_step(selected_scenario: Scenario, ubiome_state: State) -> None:
    # Check if there's an updated metadata table first
    file_metadata = search_updated_metadata_table(ubiome_state)

    # If no updated table found, use the original scenario output
    if file_metadata is None:
        scenario_proxy = ScenarioProxy.from_existing_scenario(selected_scenario.id)
        protocol_proxy: ProtocolProxy = scenario_proxy.get_protocol()
        file_metadata: File = protocol_proxy.get_process('metadata_process').get_output('metadata_table')

    # Read the raw file content to capture header lines
    raw_content = file_metadata.read()
    lines = raw_content.split('\n')

    # Find where the actual table data starts (usually after comment lines starting with #)
    header_lines = []
    for i, line in enumerate(lines):
        if line.strip().startswith('#') or (line.strip() and not '\t' in line and not ',' in line):
            header_lines.append(line)
        else:
            break

    # Display header lines if they exist
    if header_lines:
        st.write("### File Header Information")
        for line in header_lines:
            st.text(line)
        st.divider()

    # Import the file with Table importer
    table_metadata = TableImporter.call(file_metadata)
    df_metadata = table_metadata.get_data()
    # Define that all columns types must be string
    df_metadata = df_metadata.astype(str)

    st.write("### Metadata Table Editor")


    if not ubiome_state.get_scenario_step_qc():
        st.info("💡 **Instructions:** You can delete rows and must add at least one new metadata column for ANCOM differential analysis.")

        if st.button("Add Column", use_container_width=False):
            add_new_column_dialog(ubiome_state, header_lines)

        # Create column configuration for all columns
        column_config = {}

        # Configure all data columns
        for column in df_metadata.columns:
            column_config[column] = st.column_config.TextColumn(
                label=column,
                max_chars=200
            )

        # Use data editor for editing capabilities
        st.session_state[ubiome_state.EDITED_DF_METADATA] = st.data_editor(
            df_metadata,
            hide_index=True,
            use_container_width=True,
            num_rows="dynamic",
            column_config=column_config,
            key="data_editor"
        )
    else:
        st.dataframe(df_metadata, use_container_width=True, hide_index=True)

    # Save button only appear if QC task have not been created
    if not ubiome_state.get_scenario_step_qc():

        # Validation
        validation_errors = []

        # Check if at least one new column was added
        if len(ubiome_state.get_edited_df_metadata().columns) == 3:
            validation_errors.append("⚠️ You must add at least one new metadata column for ANCOM analysis.")

        # Check if all columns are completely filled
        for col in ubiome_state.get_edited_df_metadata().columns:
            if ubiome_state.get_edited_df_metadata()[col].isna().any() or (ubiome_state.get_edited_df_metadata()[col] == "").any():
                validation_errors.append(f"⚠️ Column '{col}' must be completely filled (no empty values).")

        # Check if there are any rows left
        if len(ubiome_state.get_edited_df_metadata()) == 0:
            validation_errors.append("⚠️ At least one sample must remain in the table.")

        # Display validation results
        if validation_errors:
            for error in validation_errors:
                st.error(error)
            save_disabled = True
        else:
            save_disabled = False

        if st.button("Save", disabled=save_disabled, use_container_width=True):
            with StreamlitAuthenticateUser():
                # Use the helper function to save
                save_metadata_table(ubiome_state.get_edited_df_metadata(), header_lines, ubiome_state)
                st.rerun()
    else:
        st.info("ℹ️ Metadata table is locked because QC analysis has already been run.")

def render_qc_step(selected_scenario: Scenario, ubiome_state: State) -> None:

    if not selected_scenario:
        # If a metadata table has been saved, allow running QC
        # Check if there's an updated metadata table first
        file_metadata = search_updated_metadata_table(ubiome_state)
        if not file_metadata:
            st.info("Please save a metadata table with at least one new metadata column to proceed.")

        if st.button("Run quality check", icon=":material/play_arrow:", use_container_width=False):
            # Create a new scenario in the lab
            folder : SpaceFolder = SpaceFolder.get_by_id(ubiome_state.get_selected_folder_id())
            scenario: ScenarioProxy = ScenarioProxy(
                None, folder=folder, title=f"{ubiome_state.get_current_analysis_name()} - Quality Check",
                creation_type=ScenarioCreationType.MANUAL,
            )
            protocol: ProtocolProxy = scenario.get_protocol()

            metadata_resource = protocol.add_process(
                InputTask, 'metadata_resource',
                {InputTask.config_name: ubiome_state.get_resource_id_metadata_table()})

            fastq_resource = protocol.add_process(
                InputTask, 'fastq_resource',
                {InputTask.config_name: ubiome_state.get_resource_id_fastq()})


            # Add tags to the scenario
            scenario.add_tag(Tag(ubiome_state.TAG_FASTQ, ubiome_state.get_current_fastq_name(), is_propagable=False, auto_parse=True))
            scenario.add_tag(Tag(ubiome_state.TAG_BRICK, ubiome_state.TAG_UBIOME, is_propagable=False, auto_parse=True))
            scenario.add_tag(Tag(ubiome_state.TAG_UBIOME, ubiome_state.TAG_QC, is_propagable=False))
            scenario.add_tag(Tag(ubiome_state.TAG_ANALYSIS_NAME, ubiome_state.get_current_analysis_name(), is_propagable=False, auto_parse=True))
            scenario.add_tag(Tag(ubiome_state.TAG_UBIOME_PIPELINE_ID, ubiome_state.get_current_ubiome_pipeline_id(), is_propagable=False, auto_parse=True))

            # Step 2 : QC task
            qc_process : ProcessProxy = protocol.add_process(Qiime2QualityCheck, 'qc_process') # TODO : mettre param depending of single or paired
            protocol.add_connector(out_port=fastq_resource >> 'resource',
                                       in_port=qc_process << 'fastq_folder')
            protocol.add_connector(out_port=metadata_resource >> 'resource',
                                   in_port=qc_process << 'metadata_table')
            # Add output
            protocol.add_output('qc_process_output_folder', qc_process >> 'result_folder', flag_resource=False)
            protocol.add_output('qc_process_output_quality_table', qc_process >> 'quality_table', flag_resource=False)
            scenario.add_to_queue()

            ubiome_state.reset_tree_analysis()
            st.rerun()


    else :
        # Visualize QC results
        st.write("### Quality Control Results")

        scenario_proxy = ScenarioProxy.from_existing_scenario(selected_scenario.id)
        protocol_proxy: ProtocolProxy = scenario_proxy.get_protocol()

        # Does the scenario contains the multiqc task ?
        try:
            multiqc_process = protocol_proxy.get_process('multiqc_process')
            multiqc_already_run = True
        except:
            multiqc_already_run = False

        tabqc, tabmultiqc = st.tabs(["QC", "MultiQC"])

        with tabqc:

            # Retrieve the resource set and save in a variable each visu
            # Retrieve outputs
            resource_set_output : ResourceSet = protocol_proxy.get_process('qc_process').get_output('quality_table')
            resource_set_result_dict = resource_set_output.get_resources()

            # Give the user the posibility to choose the result to display
            selected_result = st.selectbox("Select a result to display", options=resource_set_result_dict.keys())
            if selected_result:
                selected_resource = resource_set_result_dict.get(selected_result)
                if selected_resource.get_typing_name() == "RESOURCE.gws_core.Table":
                    st.dataframe(selected_resource.get_data())
                elif selected_resource.get_typing_name() == "RESOURCE.gws_core.PlotlyResource":
                    st.plotly_chart(selected_resource.get_figure())

        with tabmultiqc:
            if not multiqc_already_run:
                if st.button("Run MultiQC", icon=":material/play_arrow:", use_container_width=False):
                    scenario_proxy = ScenarioProxy.from_existing_scenario(selected_scenario.id)
                    protocol: ProtocolProxy = scenario_proxy.get_protocol()


                    # Step 2 bis : FastQC task and MultiQC task
                    fastqc_process : ProcessProxy = protocol.add_process(FastqcInit, 'fastqc_process')
                    fastq_resource = protocol.get_process('fastq_resource')
                    metadata_resource = protocol.get_process('metadata_resource')

                    protocol.add_connector(out_port=fastq_resource >> 'resource',
                                            in_port=fastqc_process << 'fastq_folder')
                    protocol.add_connector(out_port=metadata_resource >> 'resource',
                                        in_port=fastqc_process << 'metadata')

                    multiqc_process : ProcessProxy = protocol.add_process(MultiQc, 'multiqc_process')
                    protocol.add_connector(out_port=fastqc_process >> 'output',
                                            in_port=multiqc_process << 'fastqc_reports_folder')


                    # Add output
                    protocol.add_output('multiqc_process_output_folder', multiqc_process >> 'output', flag_resource=False)
                    scenario_proxy.add_to_queue()

                    ubiome_state.reset_tree_analysis()
                    st.rerun()
            else :
                st.write("### MultiQC Results")
                # Retrieve html output
                multiqc_output : Folder = protocol_proxy.get_process('multiqc_process').get_output('output')
                # Get the html file multiqc_combined.html
                path_full = os.path.join(multiqc_output.path, "multiqc_combined.html")
                with open(path_full,'r') as f:
                    html_data = f.read()

                st.components.v1.html(html_data, scrolling=True, height=500)

@st.dialog("Feature inference parameters")
def dialog_feature_inference_params(task_feature_inference: Task, ubiome_state: State):
    form_config = StreamlitTaskRunner(task_feature_inference)
    form_config.generate_config_form_without_run(
        session_state_key=ubiome_state.FEATURE_INFERENCE_CONFIG_KEY,
        default_config_values=task_feature_inference.config_specs.get_default_values())

    if st.button("Run Feature Inference", use_container_width=True, icon=":material/play_arrow:", key="button_fei"):
        if not ubiome_state.get_feature_inference_config()["is_valid"]:
            st.warning("Please fill all the mandatory fields.")
            return

        with StreamlitAuthenticateUser():
            scenario = create_base_scenario_with_tags(ubiome_state, ubiome_state.TAG_FEATURE_INFERENCE, "Feature Inference")
            scenario.add_tag(Tag(ubiome_state.TAG_FEATURE_INFERENCE_ID, scenario.get_model_id(), is_propagable=False, auto_parse=True))
            protocol = scenario.get_protocol()

            # Add feature inference process
            qiime2_feature_process = protocol.add_process(task_feature_inference, 'feature_process',
                                                        config_params=ubiome_state.get_feature_inference_config()["config"])

            # Retrieve qc output and connect
            scenario_qc_id = ubiome_state.get_scenario_step_qc()[0].id
            scenario_proxy_qc = ScenarioProxy.from_existing_scenario(scenario_qc_id)
            protocol_proxy_qc = scenario_proxy_qc.get_protocol()
            qc_output = protocol_proxy_qc.get_process('qc_process').get_output('result_folder')

            qc_resource = protocol.add_process(InputTask, 'qc_resource', {InputTask.config_name: qc_output.get_model_id()})
            protocol.add_connector(out_port=qc_resource >> 'resource', in_port=qiime2_feature_process << 'quality_check_folder')

            # Add outputs
            protocol.add_output('qiime2_feature_process_boxplot_output', qiime2_feature_process >> 'boxplot', flag_resource=False)
            protocol.add_output('qiime2_feature_process_stats_output', qiime2_feature_process >> 'stats', flag_resource=False)
            protocol.add_output('qiime2_feature_process_folder_output', qiime2_feature_process >> 'result_folder', flag_resource=False)

            scenario.add_to_queue()
            ubiome_state.reset_tree_analysis()
            st.rerun()

def render_feature_inference_step(selected_scenario: Scenario, ubiome_state: State) -> None:
    if not selected_scenario:
        # The task to display depends of single-end or paired-end
        if ubiome_state.get_sequencing_type() == "paired-end":
            task_feature_inference = Qiime2FeatureTableExtractorPE
        else:
            task_feature_inference = Qiime2FeatureTableExtractorSE

        # On click, open a dialog to allow the user to select params of feature inference
        st.button("Run new Feature Inference", icon=":material/play_arrow:", use_container_width=False,
                    on_click=lambda task=task_feature_inference, state=ubiome_state: dialog_feature_inference_params(task, state))

        # Display table of existing Feature Inference scenarios
        st.markdown("### Previous Feature Inference Analyses")

        list_scenario_fi = ubiome_state.get_scenario_step_feature_inference()
        render_scenario_table(list_scenario_fi, 'feature_process', 'feature_inference_grid', ubiome_state)
    else:
        # Display details about scenario feature inference
        st.write("### Feature Inference Scenario Results")
        display_scenario_parameters(selected_scenario, 'feature_process')

        # Display results if scenario is successful
        if selected_scenario.status == ScenarioStatus.SUCCESS:
            scenario_proxy = ScenarioProxy.from_existing_scenario(selected_scenario.id)
            protocol_proxy = scenario_proxy.get_protocol()

            tab_boxplot, tab_table = st.tabs(["Boxplot", "Table"])

            with tab_table:
                # Display stats
                stats_output = protocol_proxy.get_process('feature_process').get_output('stats')
                if stats_output and hasattr(stats_output, 'get_data'):
                    st.dataframe(stats_output.get_data())

            with tab_boxplot:
                # Display boxplot
                boxplot_output = protocol_proxy.get_process('feature_process').get_output('boxplot').get_figure()
                if boxplot_output:
                    st.plotly_chart(boxplot_output)

@st.dialog("Rarefaction parameters")
def dialog_rarefaction_params(ubiome_state: State):
    form_config = StreamlitTaskRunner(Qiime2RarefactionAnalysis)
    form_config.generate_config_form_without_run(
        session_state_key=ubiome_state.RAREFACTION_CONFIG_KEY,
        default_config_values=Qiime2RarefactionAnalysis.config_specs.get_default_values())

    if st.button("Run Rarefaction", use_container_width=True, icon=":material/play_arrow:", key="button_rarefaction"):
        if not ubiome_state.get_rarefaction_config()["is_valid"]:
            st.warning("Please fill all the mandatory fields.")
            return

        with StreamlitAuthenticateUser():
            scenario = create_base_scenario_with_tags(ubiome_state, ubiome_state.TAG_RAREFACTION, "Rarefaction")
            feature_scenario_id = ubiome_state.get_current_feature_scenario_id_parent()
            scenario.add_tag(Tag(ubiome_state.TAG_FEATURE_INFERENCE_ID, feature_scenario_id, is_propagable=False, auto_parse=True))
            protocol = scenario.get_protocol()

            # Add rarefaction process
            rarefaction_process = protocol.add_process(Qiime2RarefactionAnalysis, 'rarefaction_process',
                                                     config_params=ubiome_state.get_rarefaction_config()["config"])

            # Retrieve feature inference output and connect
            scenario_proxy_fi = ScenarioProxy.from_existing_scenario(feature_scenario_id)
            protocol_proxy_fi = scenario_proxy_fi.get_protocol()
            feature_output = protocol_proxy_fi.get_process('feature_process').get_output('result_folder')

            feature_resource = protocol.add_process(InputTask, 'feature_resource', {InputTask.config_name: feature_output.get_model_id()})
            protocol.add_connector(out_port=feature_resource >> 'resource', in_port=rarefaction_process << 'feature_frequency_folder')

            # Add outputs
            protocol.add_output('rarefaction_table_output', rarefaction_process >> 'rarefaction_table', flag_resource=False)
            protocol.add_output('rarefaction_folder_output', rarefaction_process >> 'result_folder', flag_resource=False)

            scenario.add_to_queue()
            ubiome_state.reset_tree_analysis()
            st.rerun()

def render_rarefaction_step(selected_scenario: Scenario, ubiome_state: State) -> None:
    # Get the selected tree menu item to determine which feature inference scenario is selected
    tree_menu = ubiome_state.get_tree_menu_object()
    selected_item = tree_menu.get_selected_item()
    if selected_item.key.startswith(ubiome_state.TAG_RAREFACTION):
        feature_scenario_parent_id = ubiome_state.get_parent_feature_inference_scenario_from_step()
        # save in session state
        ubiome_state.set_current_feature_scenario_id_parent(feature_scenario_parent_id)

    if not selected_scenario:
        # On click, open a dialog to allow the user to select params of rarefaction
        st.button("Run new Rarefaction", icon=":material/play_arrow:", use_container_width=False,
                    on_click=lambda state=ubiome_state: dialog_rarefaction_params(state))

        # Display table of existing Rarefaction scenarios
        st.markdown("### Previous Rarefaction Analyses")

        list_scenario_rarefaction = ubiome_state.get_scenario_step_rarefaction()
        render_scenario_table(list_scenario_rarefaction, 'rarefaction_process', 'rarefaction_grid', ubiome_state)
    else:
        # Display details about scenario rarefaction
        st.write("### Rarefaction Scenario Results")
        display_scenario_parameters(selected_scenario, 'rarefaction_process')

        # Display results if scenario is successful
        if selected_scenario.status == ScenarioStatus.SUCCESS:
            scenario_proxy = ScenarioProxy.from_existing_scenario(selected_scenario.id)
            protocol_proxy = scenario_proxy.get_protocol()
            # Display rarefaction table
            rarefaction_resource_set = protocol_proxy.get_process('rarefaction_process').get_output('rarefaction_table')
            if rarefaction_resource_set:
                resource_set_result_dict = rarefaction_resource_set.get_resources()
                # Give the user the posibility to choose the result to display
                selected_result = st.selectbox("Select a result to display", options=resource_set_result_dict.keys())
                if selected_result:
                    selected_resource = resource_set_result_dict.get(selected_result)
                    if selected_resource.get_typing_name() == "RESOURCE.gws_core.Table":
                        st.dataframe(selected_resource.get_data())
                    elif selected_resource.get_typing_name() == "RESOURCE.gws_core.PlotlyResource":
                        st.plotly_chart(selected_resource.get_figure())

@st.dialog("Taxonomy parameters")
def dialog_taxonomy_params(ubiome_state: State):
    form_config = StreamlitTaskRunner(Qiime2TaxonomyDiversity)
    form_config.generate_config_form_without_run(
        session_state_key=ubiome_state.TAXONOMY_CONFIG_KEY,
        default_config_values=Qiime2TaxonomyDiversity.config_specs.get_default_values())

    if st.button("Run Taxonomy", use_container_width=True, icon=":material/play_arrow:", key="button_taxonomy"):
        if not ubiome_state.get_taxonomy_config()["is_valid"]:
            st.warning("Please fill all the mandatory fields.")
            return

        with StreamlitAuthenticateUser():
            scenario = create_base_scenario_with_tags(ubiome_state, ubiome_state.TAG_TAXONOMY, "Taxonomy")
            feature_scenario_id = ubiome_state.get_current_feature_scenario_id_parent()
            scenario.add_tag(Tag(ubiome_state.TAG_FEATURE_INFERENCE_ID, feature_scenario_id, is_propagable=False, auto_parse=True))
            scenario.add_tag(Tag(ubiome_state.TAG_TAXONOMY_ID, scenario.get_model_id(), is_propagable=False, auto_parse=True))
            protocol = scenario.get_protocol()

            # Add taxonomy process
            taxonomy_process = protocol.add_process(Qiime2TaxonomyDiversity, 'taxonomy_process',
                                                  config_params=ubiome_state.get_taxonomy_config()["config"])

            # Retrieve feature inference output and connect
            scenario_proxy_fi = ScenarioProxy.from_existing_scenario(feature_scenario_id)
            protocol_proxy_fi = scenario_proxy_fi.get_protocol()
            feature_output = protocol_proxy_fi.get_process('feature_process').get_output('result_folder')

            feature_resource = protocol.add_process(InputTask, 'feature_resource', {InputTask.config_name: feature_output.get_model_id()})
            protocol.add_connector(out_port=feature_resource >> 'resource', in_port=taxonomy_process << 'rarefaction_analysis_result_folder')

            # Add outputs
            protocol.add_output('taxonomy_diversity_tables_output', taxonomy_process >> 'diversity_tables', flag_resource=False)
            protocol.add_output('taxonomy_taxonomy_tables_output', taxonomy_process >> 'taxonomy_tables', flag_resource=False)
            protocol.add_output('taxonomy_folder_output', taxonomy_process >> 'result_folder', flag_resource=False)


            scenario.add_to_queue()
            ubiome_state.reset_tree_analysis()
            st.rerun()

def render_taxonomy_step(selected_scenario: Scenario, ubiome_state: State) -> None:
    # Get the selected tree menu item to determine which feature inference scenario is selected
    tree_menu = ubiome_state.get_tree_menu_object()
    selected_item = tree_menu.get_selected_item()
    if selected_item.key.startswith(ubiome_state.TAG_TAXONOMY):
        feature_scenario_parent_id = ubiome_state.get_parent_feature_inference_scenario_from_step()
        # save in session state
        ubiome_state.set_current_feature_scenario_id_parent(feature_scenario_parent_id)

    if not selected_scenario:
        # On click, open a dialog to allow the user to select params of taxonomy
        st.button("Run new Taxonomy", icon=":material/play_arrow:", use_container_width=False,
                    on_click=lambda state=ubiome_state: dialog_taxonomy_params(state))

        # Display table of existing Taxonomy scenarios
        st.markdown("### Previous Taxonomy Analyses")

        list_scenario_taxonomy = ubiome_state.get_scenario_step_taxonomy()
        render_scenario_table(list_scenario_taxonomy, 'taxonomy_process', 'taxonomy_grid', ubiome_state)
    else:
        # Display details about scenario taxonomy
        st.write("### Taxonomy Scenario Results")
        display_scenario_parameters(selected_scenario, 'taxonomy_process')

        # Display results if scenario is successful
        if selected_scenario.status == ScenarioStatus.SUCCESS:
            scenario_proxy = ScenarioProxy.from_existing_scenario(selected_scenario.id)
            protocol_proxy = scenario_proxy.get_protocol()

            tab_diversity, tab_taxonomy = st.tabs(["Diversity Tables", "Taxonomy Tables"])

            with tab_diversity:
                # Display diversity tables
                diversity_resource_set = protocol_proxy.get_process('taxonomy_process').get_output('diversity_tables')
                if diversity_resource_set:
                    resource_set_result_dict = diversity_resource_set.get_resources()
                    selected_result = st.selectbox("Select a diversity table to display", options=resource_set_result_dict.keys(), key="diversity_select")
                    if selected_result:
                        selected_resource = resource_set_result_dict.get(selected_result)
                        if selected_resource.get_typing_name() == "RESOURCE.gws_core.Table":
                            st.dataframe(selected_resource.get_data())
                        elif selected_resource.get_typing_name() == "RESOURCE.gws_core.PlotlyResource":
                            st.plotly_chart(selected_resource.get_figure())

            with tab_taxonomy:
                # Display taxonomy tables
                taxonomy_resource_set = protocol_proxy.get_process('taxonomy_process').get_output('taxonomy_tables')
                if taxonomy_resource_set:
                    resource_set_result_dict = taxonomy_resource_set.get_resources()
                    selected_result = st.selectbox("Select a result to display", options=resource_set_result_dict.keys(), key="taxonomy_select")
                    if selected_result:
                        selected_resource = resource_set_result_dict.get(selected_result)
                        if selected_resource.get_typing_name() == "RESOURCE.gws_core.Table":
                            st.dataframe(selected_resource.get_data())
                        elif selected_resource.get_typing_name() == "RESOURCE.gws_core.PlotlyResource":
                            st.plotly_chart(selected_resource.get_figure())


@st.dialog("PCOA parameters")
def dialog_pcoa_params(ubiome_state: State):
    taxonomy_scenario_id = ubiome_state.get_current_taxonomy_scenario_id_parent()

    # Get available diversity tables from taxonomy results
    scenario_proxy_tax = ScenarioProxy.from_existing_scenario(taxonomy_scenario_id)
    protocol_proxy_tax = scenario_proxy_tax.get_protocol()
    diversity_resource_set = protocol_proxy_tax.get_process('taxonomy_process').get_output('diversity_tables')

    resource_set_result_dict = diversity_resource_set.get_resources()

    # Let user select which diversity table to use
    st.selectbox(
        "Select a diversity table for PCOA analysis:",
        options=list(resource_set_result_dict.keys()),
        key=ubiome_state.PCOA_DIVERSITY_TABLE_SELECT_KEY,
    )

    # Standard PCOA configuration
    form_config = StreamlitTaskRunner(PCoATrainer)
    form_config.generate_config_form_without_run(
        session_state_key=ubiome_state.PCOA_CONFIG_KEY,
        default_config_values=PCoATrainer.config_specs.get_default_values())


    if st.button("Run PCOA", use_container_width=True, icon=":material/play_arrow:", key="button_pcoa"):
        if not ubiome_state.get_pcoa_config()["is_valid"]:
            st.warning("Please fill all the mandatory fields.")
            return

        selected_table = ubiome_state.get_pcoa_diversity_table_select()
        if not selected_table:
            st.warning("Please select a diversity table.")
            return

        with StreamlitAuthenticateUser():
            scenario = create_base_scenario_with_tags(ubiome_state, ubiome_state.TAG_PCOA_DIVERSITY, "PCOA")
            feature_scenario_id = ubiome_state.get_current_feature_scenario_id_parent()
            scenario.add_tag(Tag(ubiome_state.TAG_FEATURE_INFERENCE_ID, feature_scenario_id, is_propagable=False, auto_parse=True))
            scenario.add_tag(Tag(ubiome_state.TAG_TAXONOMY_ID, taxonomy_scenario_id, is_propagable=False, auto_parse=True))
            protocol = scenario.get_protocol()

            # Add PCOA process
            pcoa_process = protocol.add_process(PCoATrainer, 'pcoa_process',
                                              config_params=ubiome_state.get_pcoa_config()["config"])

            # Get the selected diversity table as input
            diversity_table = resource_set_result_dict[selected_table]

            # Create an input task for the selected diversity table
            diversity_table_resource = protocol.add_process(InputTask, 'diversity_table_resource',
                                                          {InputTask.config_name: diversity_table.get_model_id()})

            # Connect to PCOA process
            protocol.add_connector(out_port=diversity_table_resource >> 'resource',
                                 in_port=pcoa_process << 'distance_table')

            # Add outputs
            protocol.add_output('pcoa_result_output', pcoa_process >> 'result', flag_resource=False)

            scenario.add_to_queue()
            ubiome_state.reset_tree_analysis()
            st.rerun()


def render_pcoa_step(selected_scenario: Scenario, ubiome_state: State) -> None:
    # Get the selected tree menu item to determine which taxonomy scenario is selected
    tree_menu = ubiome_state.get_tree_menu_object()
    selected_item = tree_menu.get_selected_item()
    if selected_item.key.startswith(ubiome_state.TAG_PCOA_DIVERSITY):
        taxonomy_scenario_parent_id = ubiome_state.get_parent_taxonomy_scenario_from_step()
        ubiome_state.set_current_taxonomy_scenario_id_parent(taxonomy_scenario_parent_id)
        # Retrieve the feature inference scenario ID using the utility function
        feature_inference_id = ubiome_state.get_feature_inference_id_from_taxonomy_scenario(taxonomy_scenario_parent_id)
        ubiome_state.set_current_feature_scenario_id_parent(feature_inference_id)

    if not selected_scenario:
        # On click, open a dialog to allow the user to select params of PCOA
        st.button("Run new PCOA", icon=":material/play_arrow:", use_container_width=False,
                    on_click=lambda state=ubiome_state: dialog_pcoa_params(state))

        # Display table of existing PCOA scenarios
        st.markdown("### Previous PCOA Analyses")

        list_scenario_pcoa = ubiome_state.get_scenario_step_pcoa()
        render_scenario_table(list_scenario_pcoa, 'pcoa_process', 'pcoa_grid', ubiome_state)
    else:
        # Display details about scenario PCOA
        st.write("### PCOA Scenario Results")
        display_scenario_parameters(selected_scenario, 'pcoa_process')

        # Display results if scenario is successful
        if selected_scenario.status == ScenarioStatus.SUCCESS:
            scenario_proxy = ScenarioProxy.from_existing_scenario(selected_scenario.id)
            protocol_proxy = scenario_proxy.get_protocol()

            # Get PCOA results
            pcoa_result = protocol_proxy.get_process('pcoa_process').get_output('result')

            if pcoa_result:
                tab_plot, tab_table = st.tabs(["2D Score Plot", "Tables"])
                transformed_table = pcoa_result.get_transformed_table()
                variance_table = pcoa_result.get_variance_table()

                with tab_plot:
                    # Manual plot creation
                    if transformed_table and variance_table:

                        data = transformed_table.get_data()
                        variance_data = variance_table.get_data()

                        # Create scatter plot of PC1 vs PC2
                        fig = px.scatter(
                            data,
                            x='PC1',
                            y='PC2',
                            title='PCOA - 2D Score Plot'
                        )

                        # Update axis labels with variance explained
                        pc1_var = variance_data.loc['PC1', 'ExplainedVariance'] * 100
                        pc2_var = variance_data.loc['PC2', 'ExplainedVariance'] * 100

                        fig.update_xaxes(title=f'PC1 ({pc1_var:.2f}%)')
                        fig.update_yaxes(title=f'PC2 ({pc2_var:.2f}%)')

                        fig.update_layout(
                            xaxis={
                                "showline": True,
                                "linecolor": 'black',
                                "linewidth": 1,
                                "zeroline": False
                            },
                            yaxis={
                                "showline": True,
                                "linecolor": 'black',
                                "linewidth": 1
                            })

                        st.plotly_chart(fig)
                with tab_table:
                    # Display the transformed data table
                    if transformed_table:
                        st.dataframe(transformed_table.get_data())

                    # Also show variance table
                    st.write("### Variance Explained")
                    if variance_table:
                        st.dataframe(variance_table.get_data())


@st.dialog("ANCOM parameters")
def dialog_ancom_params(ubiome_state: State):

    # Show header of metadata file
    metadata_table = ResourceModel.get_by_id(ubiome_state.get_resource_id_metadata_table())
    metadata_file = metadata_table.get_resource()

    table_metadata = TableImporter.call(metadata_file)
    df_metadata = table_metadata.get_data()

    st.write("### Metadata File")
    if metadata_table:
        # Display only column names and first 3 rows
        st.dataframe(df_metadata.head(3))

    form_config = StreamlitTaskRunner(Qiime2DifferentialAnalysis)
    form_config.generate_config_form_without_run(
        session_state_key=ubiome_state.ANCOM_CONFIG_KEY,
        default_config_values=Qiime2DifferentialAnalysis.config_specs.get_default_values())

    if st.button("Run ANCOM", use_container_width=True, icon=":material/play_arrow:", key="button_ancom"):
        if not ubiome_state.get_ancom_config()["is_valid"]:
            st.warning("Please fill all the mandatory fields.")
            return

        with StreamlitAuthenticateUser():
            scenario = create_base_scenario_with_tags(ubiome_state, ubiome_state.TAG_ANCOM, "ANCOM")
            taxonomy_scenario_id = ubiome_state.get_current_taxonomy_scenario_id_parent()
            feature_scenario_id = ubiome_state.get_current_feature_scenario_id_parent()
            scenario.add_tag(Tag(ubiome_state.TAG_FEATURE_INFERENCE_ID, feature_scenario_id, is_propagable=False, auto_parse=True))
            scenario.add_tag(Tag(ubiome_state.TAG_TAXONOMY_ID, taxonomy_scenario_id, is_propagable=False, auto_parse=True))
            protocol = scenario.get_protocol()


            # Add ANCOM process
            ancom_process = protocol.add_process(Qiime2DifferentialAnalysis, 'ancom_process',
                                               config_params=ubiome_state.get_ancom_config()["config"])

            # Get the taxonomy diversity folder
            scenario_proxy_tax = ScenarioProxy.from_existing_scenario(taxonomy_scenario_id)
            protocol_proxy_tax = scenario_proxy_tax.get_protocol()
            taxonomy_folder_output = protocol_proxy_tax.get_process('taxonomy_process').get_output('result_folder')

            # Add input resources
            taxonomy_folder_resource = protocol.add_process(InputTask, 'taxonomy_folder_resource',
                                                          {InputTask.config_name: taxonomy_folder_output.get_model_id()})

            metadata_file_resource = protocol.add_process(InputTask, 'metadata_file_resource',
                                                        {InputTask.config_name: ubiome_state.get_resource_id_metadata_table()})

            # Connect inputs to ANCOM process
            protocol.add_connector(out_port=taxonomy_folder_resource >> 'resource',
                                 in_port=ancom_process << 'taxonomy_diversity_folder')
            protocol.add_connector(out_port=metadata_file_resource >> 'resource',
                                 in_port=ancom_process << 'metadata_file')

            # Add outputs
            protocol.add_output('ancom_result_tables_output', ancom_process >> 'result_tables', flag_resource=False)
            protocol.add_output('ancom_result_folder_output', ancom_process >> 'result_folder', flag_resource=False)

            scenario.add_to_queue()
            ubiome_state.reset_tree_analysis()
            st.rerun()

def render_ancom_step(selected_scenario: Scenario, ubiome_state: State) -> None:
    # Get the selected tree menu item to determine which taxonomy scenario is selected
    tree_menu = ubiome_state.get_tree_menu_object()
    selected_item = tree_menu.get_selected_item()
    if selected_item.key.startswith(ubiome_state.TAG_ANCOM):
        taxonomy_scenario_parent_id = ubiome_state.get_parent_taxonomy_scenario_from_step()
        ubiome_state.set_current_taxonomy_scenario_id_parent(taxonomy_scenario_parent_id)
        # Retrieve the feature inference scenario ID using the utility function
        feature_inference_id = ubiome_state.get_feature_inference_id_from_taxonomy_scenario(taxonomy_scenario_parent_id)
        ubiome_state.set_current_feature_scenario_id_parent(feature_inference_id)

    if not selected_scenario:
        # On click, open a dialog to allow the user to select params of ANCOM
        st.button("Run new ANCOM", icon=":material/play_arrow:", use_container_width=False,
                        on_click=lambda state=ubiome_state: dialog_ancom_params(state))

        # Display table of existing ANCOM scenarios
        st.markdown("### Previous ANCOM Analyses")

        list_scenario_ancom = ubiome_state.get_scenario_step_ancom()
        render_scenario_table(list_scenario_ancom, 'ancom_process', 'ancom_grid', ubiome_state)

    else:
        # Display details about scenario ANCOM
        st.write("### ANCOM Scenario Results")
        display_scenario_parameters(selected_scenario, 'ancom_process')

        # Display results if scenario is successful
        if selected_scenario.status == ScenarioStatus.SUCCESS:
            scenario_proxy = ScenarioProxy.from_existing_scenario(selected_scenario.id)
            protocol_proxy = scenario_proxy.get_protocol()

            # Get ANCOM results
            ancom_result_tables = protocol_proxy.get_process('ancom_process').get_output('result_tables')

            if ancom_result_tables:
                resource_set_result_dict = ancom_result_tables.get_resources()

                # Separate different types of results
                ancom_stats = {}
                volcano_plots = {}
                percentile_abundances = {}

                for key, resource in resource_set_result_dict.items():
                    if "ANCOM Stat" in key:
                        ancom_stats[key] = resource
                    elif "Volcano plot" in key:
                        volcano_plots[key] = resource
                    elif "Percentile abundances" in key:
                        percentile_abundances[key] = resource

                tab_stats, tab_volcano, tab_percentile = st.tabs(["ANCOM Statistics", "Volcano Plots", "Percentile Abundances"])

                with tab_stats:
                    st.write("#### ANCOM Statistical Results")
                    if ancom_stats:
                        selected_stat = st.selectbox("Select taxonomic level for ANCOM stats:",
                                                   options=list(ancom_stats.keys()),
                                                   key="ancom_stats_select")
                        if selected_stat:
                            st.dataframe(ancom_stats[selected_stat].get_data())
                    else:
                        st.info("No ANCOM statistics available.")

                with tab_volcano:
                    st.write("#### Volcano Plot Data")
                    if volcano_plots:
                        selected_volcano = st.selectbox("Select taxonomic level for volcano plot:",
                                                      options=list(volcano_plots.keys()),
                                                      key="volcano_plot_select")
                        if selected_volcano:
                            volcano_data = volcano_plots[selected_volcano].get_data()
                            st.dataframe(volcano_data)

                            # Create a simple volcano plot if data has the right columns
                            if 'W' in volcano_data.columns and 'clr_F-score' in volcano_data.columns:
                                fig = px.scatter(volcano_data, x='W', y='clr_F-score',
                                               title=f"Volcano Plot - {selected_volcano}",
                                               hover_data=volcano_data.columns.tolist())
                                fig.update_layout(
                                    xaxis_title="W statistic",
                                    yaxis_title="F-score"
                                )
                                st.plotly_chart(fig)
                    else:
                        st.info("No volcano plot data available.")

                with tab_percentile:
                    st.write("#### Percentile Abundances")
                    if percentile_abundances:
                        selected_percentile = st.selectbox("Select taxonomic level for percentile abundances:",
                                                         options=list(percentile_abundances.keys()),
                                                         key="percentile_select")
                        if selected_percentile:
                            st.dataframe(percentile_abundances[selected_percentile].get_data())
                    else:
                        st.info("No percentile abundance data available.")

@st.dialog("DB annotator parameters")
def dialog_db_annotator_params(ubiome_state: State):
    # Display available annotation tables for user selection
    st.write("### Select Annotation Table")
    # Use StreamlitResourceSelect to let user choose an annotation table
    resource_select = StreamlitResourceSelect()
    resource_select.select_resource(
        placeholder='Select annotation table', key=ubiome_state.SELECTED_ANNOTATION_TABLE_KEY, defaut_resource=None)

    if st.button("Run Taxa Composition", use_container_width=True, icon=":material/play_arrow:", key="button_db_annotator"):
        selected_annotation_table_id = ubiome_state.get_selected_annotation_table()["resourceId"]
        if not selected_annotation_table_id:
            st.warning("Please select an annotation table.")
            return

        with StreamlitAuthenticateUser():
            scenario = create_base_scenario_with_tags(ubiome_state, ubiome_state.TAG_DB_ANNOTATOR, "Taxa Composition")
            taxonomy_scenario_id = ubiome_state.get_current_taxonomy_scenario_id_parent()
            feature_scenario_id = ubiome_state.get_current_feature_scenario_id_parent()
            scenario.add_tag(Tag(ubiome_state.TAG_FEATURE_INFERENCE_ID, feature_scenario_id, is_propagable=False, auto_parse=True))
            scenario.add_tag(Tag(ubiome_state.TAG_TAXONOMY_ID, taxonomy_scenario_id, is_propagable=False, auto_parse=True))
            protocol = scenario.get_protocol()

            # Add DB annotator process
            db_annotator_process = protocol.add_process(Qiime2TableDbAnnotator, 'db_annotator_process')

            # Get the taxonomy diversity folder
            scenario_proxy_tax = ScenarioProxy.from_existing_scenario(taxonomy_scenario_id)
            protocol_proxy_tax = scenario_proxy_tax.get_protocol()
            taxonomy_folder_output = protocol_proxy_tax.get_process('taxonomy_process').get_output('result_folder')

            # Add input resources
            taxonomy_folder_resource = protocol.add_process(InputTask, 'taxonomy_folder_resource',
                                                          {InputTask.config_name: taxonomy_folder_output.get_model_id()})

            annotation_table_resource = protocol.add_process(InputTask, 'annotation_table_resource',
                                                           {InputTask.config_name: selected_annotation_table_id})

            # Connect inputs to DB annotator process
            protocol.add_connector(out_port=taxonomy_folder_resource >> 'resource',
                                 in_port=db_annotator_process << 'diversity_folder')
            protocol.add_connector(out_port=annotation_table_resource >> 'resource',
                                 in_port=db_annotator_process << 'annotation_table')

            # Add outputs
            protocol.add_output('relative_abundance_table_output', db_annotator_process >> 'relative_abundance_table', flag_resource=False)
            protocol.add_output('relative_abundance_plotly_output', db_annotator_process >> 'relative_abundance_plotly_resource', flag_resource=False)
            protocol.add_output('absolute_abundance_table_output', db_annotator_process >> 'absolute_abundance_table', flag_resource=False)
            protocol.add_output('absolute_abundance_plotly_output', db_annotator_process >> 'absolute_abundance_plotly_resource', flag_resource=False)

            scenario.add_to_queue()
            ubiome_state.reset_tree_analysis()
            st.rerun()

def render_db_annotator_step(selected_scenario: Scenario, ubiome_state: State) -> None:
    # Get the selected tree menu item to determine which taxonomy scenario is selected
    tree_menu = ubiome_state.get_tree_menu_object()
    selected_item = tree_menu.get_selected_item()
    if selected_item.key.startswith(ubiome_state.TAG_DB_ANNOTATOR):
        taxonomy_scenario_parent_id = ubiome_state.get_parent_taxonomy_scenario_from_step()
        ubiome_state.set_current_taxonomy_scenario_id_parent(taxonomy_scenario_parent_id)
        # Retrieve the feature inference scenario ID using the utility function
        feature_inference_id = ubiome_state.get_feature_inference_id_from_taxonomy_scenario(taxonomy_scenario_parent_id)
        ubiome_state.set_current_feature_scenario_id_parent(feature_inference_id)

    if not selected_scenario:

        # On click, open a dialog to allow the user to select params of Taxa Composition
        st.button("Run new Taxa Composition", icon=":material/play_arrow:", use_container_width=False,
                        on_click=lambda state=ubiome_state: dialog_db_annotator_params(state))

        # Display table of existing Taxa Composition scenarios
        st.markdown("### Previous Taxa Composition Analyses")

        list_scenario_db_annotator = ubiome_state.get_scenario_step_db_annotator()
        render_scenario_table(list_scenario_db_annotator, 'db_annotator_process', 'db_annotator_grid', ubiome_state)

    else:
        # Display details about scenario DB annotator
        st.write("### Taxa Composition Scenario Results")
        display_scenario_parameters(selected_scenario, 'db_annotator_process')

        # Display results if scenario is successful
        if selected_scenario.status == ScenarioStatus.SUCCESS:
            scenario_proxy = ScenarioProxy.from_existing_scenario(selected_scenario.id)
            protocol_proxy = scenario_proxy.get_protocol()

            tab_relative, tab_absolute = st.tabs(["Relative Abundance", "Absolute Abundance"])

            with tab_relative:
                # Display relative abundance table and plot
                st.write("#### Relative Abundance Table")
                relative_table_output = protocol_proxy.get_process('db_annotator_process').get_output('relative_abundance_table')
                if relative_table_output:
                    st.dataframe(relative_table_output.get_data())

                st.write("#### Relative Abundance Plot")
                relative_plot_output = protocol_proxy.get_process('db_annotator_process').get_output('relative_abundance_plotly_resource')
                if relative_plot_output:
                    st.plotly_chart(relative_plot_output.get_figure())

            with tab_absolute:
                # Display absolute abundance table and plot
                st.write("#### Absolute Abundance Table")
                absolute_table_output = protocol_proxy.get_process('db_annotator_process').get_output('absolute_abundance_table')
                if absolute_table_output:
                    st.dataframe(absolute_table_output.get_data())

                st.write("#### Absolute Abundance Plot")
                absolute_plot_output = protocol_proxy.get_process('db_annotator_process').get_output('absolute_abundance_plotly_resource')
                if absolute_plot_output:
                    st.plotly_chart(absolute_plot_output.get_figure())

@st.dialog("16S parameters")
def dialog_16s_params(ubiome_state: State):
    form_config = StreamlitTaskRunner(Picrust2FunctionalAnalysis)
    form_config.generate_config_form_without_run(
        session_state_key=ubiome_state.FUNCTIONAL_ANALYSIS_CONFIG_KEY,
        default_config_values=Picrust2FunctionalAnalysis.config_specs.get_default_values())

    if st.button("Run 16S Functional Analysis", use_container_width=True, icon=":material/play_arrow:", key="button_16s"):
        if not ubiome_state.get_functional_analysis_config()["is_valid"]:
            st.warning("Please fill all the mandatory fields.")
            return

        with StreamlitAuthenticateUser():
            scenario = create_base_scenario_with_tags(ubiome_state, ubiome_state.TAG_16S, "16S Functional Analysis")
            feature_scenario_id = ubiome_state.get_current_feature_scenario_id_parent()
            scenario.add_tag(Tag(ubiome_state.TAG_FEATURE_INFERENCE_ID, feature_scenario_id, is_propagable=False, auto_parse=True))
            scenario.add_tag(Tag(ubiome_state.TAG_16S_ID, scenario.get_model_id(), is_propagable=False, auto_parse=True))
            protocol = scenario.get_protocol()

            # Retrieve feature inference outputs and extract table.qza and asv
            scenario_proxy_fi = ScenarioProxy.from_existing_scenario(feature_scenario_id)
            protocol_proxy_fi = scenario_proxy_fi.get_protocol()
            feature_output = protocol_proxy_fi.get_process('feature_process').get_output('result_folder')

            # Get the table.qza and ASV-sequences.fasta from feature inference output
            feature_resource = protocol.add_process(InputTask, 'feature_resource', {InputTask.config_name: feature_output.get_model_id()})
            fs_node_extractor_table = protocol.add_process(FsNodeExtractor, 'fs_node_extractor_table', {"fs_node_path": "table.qza"})
            fs_node_extractor_asv = protocol.add_process(FsNodeExtractor, 'fs_node_extractor_asv', {"fs_node_path": "ASV-sequences.fasta"})
            # Add connectors
            protocol.add_connector(out_port=feature_resource >> 'resource', in_port=fs_node_extractor_table << "source")
            protocol.add_connector(out_port=feature_resource >> 'resource', in_port=fs_node_extractor_asv << "source")
            # Add 16S functional analysis process
            functional_analysis_process = protocol.add_process(Picrust2FunctionalAnalysis, 'functional_analysis_process',
                                                             config_params=ubiome_state.get_functional_analysis_config()["config"])

            # The task expects table.qza for ASV_count_abundance and ASV-sequences.fasta for FASTA_of_asv
            protocol.add_connector(out_port=fs_node_extractor_table >> "target", in_port=functional_analysis_process << 'ASV_count_abundance')
            protocol.add_connector(out_port=fs_node_extractor_asv >> "target", in_port=functional_analysis_process << 'FASTA_of_asv')

            # Add outputs
            protocol.add_output('functional_analysis_result_output', functional_analysis_process >> 'Folder_result', flag_resource=False)

            scenario.add_to_queue()
            ubiome_state.reset_tree_analysis()
            st.rerun()

def render_16s_step(selected_scenario: Scenario, ubiome_state: State) -> None:
    # Get the selected tree menu item to determine which feature inference scenario is selected
    tree_menu = ubiome_state.get_tree_menu_object()
    selected_item = tree_menu.get_selected_item()
    if selected_item.key.startswith(ubiome_state.TAG_16S):
        feature_scenario_parent_id = ubiome_state.get_parent_feature_inference_scenario_from_step()
        # save in session state
        ubiome_state.set_current_feature_scenario_id_parent(feature_scenario_parent_id)

    if not selected_scenario:
        # On click, open a dialog to allow the user to select params of 16S functional analysis
        st.button("Run new 16S Functional Analysis", icon=":material/play_arrow:", use_container_width=False,
                    on_click=lambda state=ubiome_state: dialog_16s_params(state))

        # Display table of existing 16S Functional Analysis scenarios
        st.markdown("### Previous 16S Functional Analysis")

        list_scenario_16s = ubiome_state.get_scenario_step_16s()
        render_scenario_table(list_scenario_16s, 'functional_analysis_process', '16s_functional_grid', ubiome_state)
    else:
        # Display details about scenario 16S functional analysis
        st.write("### 16S Functional Analysis Scenario Results")
        display_scenario_parameters(selected_scenario, 'functional_analysis_process')

        # Display results if scenario is successful
        if selected_scenario.status == ScenarioStatus.SUCCESS:
            scenario_proxy = ScenarioProxy.from_existing_scenario(selected_scenario.id)
            protocol_proxy = scenario_proxy.get_protocol()

            # Get functional analysis results folder
            functional_result_folder = protocol_proxy.get_process('functional_analysis_process').get_output('Folder_result')

            if functional_result_folder:
                st.write("### PICRUSt2 Functional Analysis Results")

                # Display folder contents
                st.write("#### Result Folder Contents")
                folder_path = functional_result_folder.path

                if os.path.exists(folder_path):
                    # List key output folders
                    key_folders = ['EC_metagenome_out', 'KO_metagenome_out', 'pathways_out']

                    tabs = st.tabs(["EC Metagenome", "KO Metagenome", "Pathways"])

                    for i, (tab, folder_name) in enumerate(zip(tabs, key_folders)):
                        with tab:
                            folder_full_path = os.path.join(folder_path, folder_name)
                            if os.path.exists(folder_full_path):
                                st.write(f"#### {folder_name.replace('_', ' ').title()}")

                                # List files in the folder
                                try:
                                    files_in_folder = os.listdir(folder_full_path)
                                    if files_in_folder:
                                        st.write("**Available files:**")
                                        for file_name in files_in_folder:
                                            file_path = os.path.join(folder_full_path, file_name)
                                            if os.path.isfile(file_path):
                                                file_size = os.path.getsize(file_path)
                                                st.write(f"- {file_name} ({file_size} bytes)")

                                                # For TSV files, offer to display them
                                                if file_name.endswith(('.tsv', '.tsv.gz')):
                                                    if st.button(f"View {file_name}", key=f"view_{folder_name}_{file_name}"):
                                                        try:
                                                            if file_name.endswith('.gz'):
                                                                import gzip
                                                                with gzip.open(file_path, 'rt') as f:
                                                                    content = f.read()
                                                            else:
                                                                with open(file_path, 'r') as f:
                                                                    content = f.read()

                                                            # Display as dataframe if it's TSV
                                                            import io
                                                            df = pd.read_csv(io.StringIO(content), sep='\t')
                                                            st.dataframe(df.head(100))  # Show first 100 rows
                                                        except Exception as e:
                                                            st.error(f"Error reading file: {str(e)}")
                                    else:
                                        st.info(f"No files found in {folder_name}")
                                except Exception as e:
                                    st.error(f"Error accessing folder {folder_name}: {str(e)}")
                            else:
                                st.warning(f"Folder {folder_name} not found in results")
                else:
                    st.error("Result folder not found")

@st.dialog("16S Visualization parameters")
def dialog_16s_visu_params(ubiome_state: State):
    # Show metadata file preview
    metadata_table = ResourceModel.get_by_id(ubiome_state.get_resource_id_metadata_table())
    metadata_file = metadata_table.get_resource()

    table_metadata = TableImporter.call(metadata_file)
    df_metadata = table_metadata.get_data()

    st.write("### Metadata File Preview")
    if metadata_table:
        # Display only column names and first 3 rows
        st.dataframe(df_metadata.head(3))

    form_config = StreamlitTaskRunner(Ggpicrust2FunctionalAnalysis)
    default_config = Ggpicrust2FunctionalAnalysis.config_specs.get_default_values()
    default_config["Round_digit"] = True
    form_config.generate_config_form_without_run(
        session_state_key=ubiome_state.FUNCTIONAL_ANALYSIS_VISU_CONFIG_KEY,
        default_config_values=default_config)

    if st.button("Run 16S Visualization", use_container_width=True, icon=":material/play_arrow:", key="button_16s_visu"):
        if not ubiome_state.get_functional_analysis_visu_config()["is_valid"]:
            st.warning("Please fill all the mandatory fields.")
            return

        with StreamlitAuthenticateUser():
            scenario = create_base_scenario_with_tags(ubiome_state, ubiome_state.TAG_16S_VISU, "16S Visualization")
            feature_scenario_id = ubiome_state.get_current_feature_scenario_id_parent()
            functional_scenario_id = ubiome_state.get_current_16s_scenario_id_parent()
            scenario.add_tag(Tag(ubiome_state.TAG_FEATURE_INFERENCE_ID, feature_scenario_id, is_propagable=False, auto_parse=True))
            scenario.add_tag(Tag(ubiome_state.TAG_16S_ID, functional_scenario_id, is_propagable=False, auto_parse=True))
            protocol = scenario.get_protocol()

            # Add 16S visualization process
            visu_process = protocol.add_process(Ggpicrust2FunctionalAnalysis, 'functional_visu_process',
                                              config_params=ubiome_state.get_functional_analysis_visu_config()["config"])

            # Get the 16S functional analysis results folder
            scenario_proxy_16s = ScenarioProxy.from_existing_scenario(functional_scenario_id)
            protocol_proxy_16s = scenario_proxy_16s.get_protocol()
            functional_result_folder = protocol_proxy_16s.get_process('functional_analysis_process').get_output('Folder_result')

            # Extract the KO metagenome file from the results folder
            functional_folder_resource = protocol.add_process(InputTask, 'functional_folder_resource',
                                                             {InputTask.config_name: functional_result_folder.get_model_id()})

            # Extract the pred_metagenome_unstrat.tsv.gz file from KO_metagenome_out folder
            ko_file_extractor = protocol.add_process(FsNodeExtractor, 'ko_file_extractor',
                                                    {"fs_node_path": "KO_metagenome_out/pred_metagenome_unstrat.tsv.gz"})

            # Add metadata file resource
            metadata_file_resource = protocol.add_process(InputTask, 'metadata_file_resource',
                                                        {InputTask.config_name: ubiome_state.get_resource_id_metadata_table()})

            # Connect inputs
            protocol.add_connector(out_port=functional_folder_resource >> 'resource',
                                 in_port=ko_file_extractor << 'source')
            protocol.add_connector(out_port=ko_file_extractor >> 'target',
                                 in_port=visu_process << 'ko_abundance_file')
            protocol.add_connector(out_port=metadata_file_resource >> 'resource',
                                 in_port=visu_process << 'metadata_file')

            # Add outputs
            protocol.add_output('visu_resource_set_output', visu_process >> 'resource_set', flag_resource=False)
            protocol.add_output('visu_plotly_output', visu_process >> 'plotly_result', flag_resource=False)

            scenario.add_to_queue()
            ubiome_state.reset_tree_analysis()
            st.rerun()

def render_16s_visu_step(selected_scenario: Scenario, ubiome_state: State) -> None:
    # Get the selected tree menu item to determine which 16s scenario is selected
    tree_menu = ubiome_state.get_tree_menu_object()
    selected_item = tree_menu.get_selected_item()
    if selected_item.key.startswith(ubiome_state.TAG_16S_VISU):
        functional_scenario_parent_id = ubiome_state.get_parent_16s_scenario_from_step()
        ubiome_state.set_current_16s_scenario_id_parent(functional_scenario_parent_id)
        # Retrieve the feature inference scenario ID
        feature_inference_id = ubiome_state.get_feature_inference_id_from_16s_scenario(functional_scenario_parent_id)
        ubiome_state.set_current_feature_scenario_id_parent(feature_inference_id)

    if not selected_scenario:
        # Check if we have a valid 16S functional analysis scenario to run visualization
        functional_scenario_id = ubiome_state.get_current_16s_scenario_id_parent()

        # Validate that the required KO metagenome file exists
        ko_file_available = False
        if functional_scenario_id:
            try:
                scenario_proxy_16s = ScenarioProxy.from_existing_scenario(functional_scenario_id)
                protocol_proxy_16s = scenario_proxy_16s.get_protocol()
                functional_result_folder = protocol_proxy_16s.get_process('functional_analysis_process').get_output('Folder_result')

                if functional_result_folder and os.path.exists(functional_result_folder.path):
                    ko_file_path = os.path.join(functional_result_folder.path, "KO_metagenome_out", "pred_metagenome_unstrat.tsv.gz")
                    ko_file_available = os.path.exists(ko_file_path)
            except Exception:
                ko_file_available = False

        if not ko_file_available:
            st.warning("⚠️ **Cannot run 16S Visualization**: The required file `KO_metagenome_out/pred_metagenome_unstrat.tsv.gz` is not available from the 16S Functional Analysis results.")
        else:
            # On click, open a dialog to allow the user to select params of 16S visualization
            st.button("Run new 16S Visualization", icon=":material/play_arrow:", use_container_width=False,
                        on_click=lambda state=ubiome_state: dialog_16s_visu_params(state))

        # Display table of existing 16S Visualization scenarios
        st.markdown("### Previous 16S Visualizations")

        list_scenario_16s_visu = ubiome_state.get_scenario_step_16s_visu()
        render_scenario_table(list_scenario_16s_visu, 'functional_visu_process', '16s_visu_grid', ubiome_state)
    else:
        # Display details about scenario 16S visualization
        st.write("### 16S Visualization Scenario Results")
        display_scenario_parameters(selected_scenario, 'functional_visu_process')

        # Display results if scenario is successful
        if selected_scenario.status == ScenarioStatus.SUCCESS:
            scenario_proxy = ScenarioProxy.from_existing_scenario(selected_scenario.id)
            protocol_proxy = scenario_proxy.get_protocol()

            tab_pca, tab_results = st.tabs(["PCA Plot", "Analysis Results"])

            with tab_pca:
                # Display PCA plot
                st.write("### Principal Component Analysis")
                plotly_result = protocol_proxy.get_process('functional_visu_process').get_output('plotly_result')
                if plotly_result:
                    st.plotly_chart(plotly_result.get_figure())

            with tab_results:
                # Display resource set results
                st.write("### Differential Abundance Analysis Results")
                resource_set_output = protocol_proxy.get_process('functional_visu_process').get_output('resource_set')

                if resource_set_output:
                    resource_dict = resource_set_output.get_resources()

                    # Separate different types of results
                    error_bar_plots = {}
                    heatmap_plots = {}
                    analysis_tables = {}

                    for key, resource in resource_dict.items():
                        if "pathway_errorbar" in key and key.endswith(".png"):
                            error_bar_plots[key] = resource
                        elif "pathway_heatmap" in key and key.endswith(".png"):
                            heatmap_plots[key] = resource
                        elif "daa_annotated_results" in key and key.endswith(".csv"):
                            analysis_tables[key] = resource

                    # Create sub-tabs for different result types
                    if error_bar_plots or heatmap_plots or analysis_tables:
                        sub_tabs = []
                        if analysis_tables:
                            sub_tabs.append("Analysis Tables")
                        if error_bar_plots:
                            sub_tabs.append("Error Bar Plots")
                        if heatmap_plots:
                            sub_tabs.append("Heatmap Plots")

                        if len(sub_tabs) > 1:
                            tab_tables, *other_tabs = st.tabs(sub_tabs)
                        else:
                            tab_tables = st.container()
                            other_tabs = []

                        # Analysis Tables
                        if analysis_tables:
                            with tab_tables if len(sub_tabs) > 1 else st.container():
                                st.write("#### Differential Abundance Analysis Tables")
                                selected_table = st.selectbox("Select analysis table:",
                                                             options=list(analysis_tables.keys()),
                                                             key="analysis_table_select")
                                if selected_table:
                                    st.dataframe(analysis_tables[selected_table].get_data())

                        # Error Bar Plots
                        if error_bar_plots and other_tabs:
                            with other_tabs[0]:
                                st.write("#### Pathway Error Bar Plots")
                                selected_errorbar = st.selectbox("Select error bar plot:",
                                                               options=list(error_bar_plots.keys()),
                                                               key="errorbar_select")
                                if selected_errorbar:
                                    try:
                                        st.image(error_bar_plots[selected_errorbar].path)
                                    except Exception as e:
                                        st.error(f"Error displaying image: {str(e)}")

                        # Heatmap Plots
                        if heatmap_plots and len(other_tabs) > 1:
                            with other_tabs[1]:
                                st.write("#### Pathway Heatmap Plots")
                                selected_heatmap = st.selectbox("Select heatmap plot:",
                                                              options=list(heatmap_plots.keys()),
                                                              key="heatmap_select")
                                if selected_heatmap:
                                    try:
                                        st.image(heatmap_plots[selected_heatmap].path)
                                    except Exception as e:
                                        st.error(f"Error displaying image: {str(e)}")
                    else:
                        st.info("No visualization results available.")
                else:
                    st.info("No analysis results available.")