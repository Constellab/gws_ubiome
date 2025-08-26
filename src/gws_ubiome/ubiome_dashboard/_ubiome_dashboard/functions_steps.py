import os
import streamlit as st
import pandas as pd
from state import State
from gws_core.streamlit import StreamlitAuthenticateUser, StreamlitContainers, StreamlitResourceSelect, StreamlitRouter, StreamlitTaskRunner
from gws_ubiome.ubiome_dashboard._ubiome_dashboard.ubiome_config import UbiomeConfig
import pandas as pd
from gws_core import Task, ResourceSet, Folder, Settings, ResourceModel, ResourceOrigin, Scenario, ScenarioProxy, ProtocolProxy, File, TableImporter, SpaceFolder, StringHelper, Tag, InputTask, SpaceService, ProcessProxy, ScenarioSearchBuilder, TagValueModel, Scenario, ScenarioStatus, ScenarioProxy, ProtocolProxy, ScenarioCreationType
from gws_ubiome import Qiime2QualityCheck, Qiime2FeatureTableExtractorPE, Qiime2FeatureTableExtractorSE, Qiime2RarefactionAnalysis
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


def render_metadata_step(selected_scenario: Scenario, ubiome_state: State) -> None:
    scenario_proxy = ScenarioProxy.from_existing_scenario(selected_scenario.id)
    # Retrieve the protocol
    protocol_proxy: ProtocolProxy = scenario_proxy.get_protocol()

    # Retrieve outputs
    file_metadata : File = protocol_proxy.get_process('metadata_process').get_output('metadata_table')

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
    # TODO : faire que l'user puisse modifier : ajouter colonne, supprimer ligne etc
    st.dataframe(df_metadata, use_container_width=True)

    # Save button only appear if QC task have not been created
    if not ubiome_state.get_scenario_step_qc():
        if st.button("Save"):
            path_temp = os.path.join(os.path.abspath(os.path.dirname(__file__)), Settings.make_temp_dir())
            full_path = os.path.join(path_temp, f"Metadata_updated.txt")
            metadata_manually: File = File(full_path)

            # Combine header lines with updated table data
            content_to_save = ""
            if header_lines:
                content_to_save = '\n'.join(header_lines) + '\n'
            content_to_save += df_metadata.to_csv(index=False, sep='\t')

            metadata_manually.write(content_to_save)
            # Add the metadata_updated tag to this resource
            metadata_manually.tags.add_tag(Tag(ubiome_state.TAG_UBIOME, ubiome_state.TAG_METADATA_UPDATED, is_propagable=True))
            selected_metadata = ResourceModel.save_from_resource(
                metadata_manually, ResourceOrigin.UPLOADED, flagged=True)
            ubiome_state.set_resource_id_metadata_table(metadata_manually.get_model_id())


def render_qc_step(selected_scenario: Scenario, ubiome_state: State) -> None:

    if not selected_scenario:
        if st.button("Run new QC", icon=":material/play_arrow:", use_container_width=False):
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
            scenario.add_tag(Tag(ubiome_state.TAG_FASTQ, ubiome_state.get_current_fastq_name(), is_propagable=True, auto_parse=True))
            scenario.add_tag(Tag(ubiome_state.TAG_BRICK, ubiome_state.TAG_UBIOME, is_propagable=True, auto_parse=True))
            scenario.add_tag(Tag(ubiome_state.TAG_UBIOME, ubiome_state.TAG_QC, is_propagable=True))
            scenario.add_tag(Tag(ubiome_state.TAG_ANALYSIS_NAME, ubiome_state.get_current_analysis_name(), is_propagable=True, auto_parse=True))
            scenario.add_tag(Tag(ubiome_state.TAG_UBIOME_PIPELINE_ID, ubiome_state.get_current_ubiome_pipeline_id(), is_propagable=True, auto_parse=True))

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
def dialog_feature_inference_params(task_feature_inference : Task, ubiome_state: State):
    form_config = StreamlitTaskRunner(task_feature_inference)
    form_config.generate_config_form_without_run(
        session_state_key=ubiome_state.FEATURE_INFERENCE_CONFIG_KEY, default_config_values=task_feature_inference.config_specs.get_default_values())

    if st.button("Run Feature Inference", use_container_width=True, icon=":material/play_arrow:", key = "button_fei"):
        if not ubiome_state.get_feature_inference_config()["is_valid"]:
            st.warning("Please fill all the mandatory fields.")
            return
        with StreamlitAuthenticateUser():
            # Create a new scenario in the lab
            folder : SpaceFolder = SpaceFolder.get_by_id(ubiome_state.get_selected_folder_id())
            scenario: ScenarioProxy = ScenarioProxy(
                None, folder=folder, title=f"{ubiome_state.get_current_analysis_name()} - Feature Inference", # TODO demander à l'user un nom
                creation_type=ScenarioCreationType.MANUAL,
            )
            protocol: ProtocolProxy = scenario.get_protocol()

            # Add tags to the scenario
            scenario.add_tag(Tag(ubiome_state.TAG_FASTQ, ubiome_state.get_current_fastq_name(), is_propagable=True, auto_parse=True))
            scenario.add_tag(Tag(ubiome_state.TAG_BRICK, ubiome_state.TAG_UBIOME, is_propagable=True, auto_parse=True))
            scenario.add_tag(Tag(ubiome_state.TAG_UBIOME, ubiome_state.TAG_FEATURE_INFERENCE, is_propagable=True))
            scenario.add_tag(Tag(ubiome_state.TAG_ANALYSIS_NAME, ubiome_state.get_current_analysis_name(), is_propagable=True, auto_parse=True))
            scenario.add_tag(Tag(ubiome_state.TAG_UBIOME_PIPELINE_ID, ubiome_state.get_current_ubiome_pipeline_id(), is_propagable=True, auto_parse=True))
            scenario.add_tag(Tag(ubiome_state.TAG_FEATURE_INFERENCE_ID, scenario.get_model_id(), is_propagable=True, auto_parse=True))

            # Step 3 : Qiime2FeatureTableExtractorPE or SE task
            # Depending of Paire end ou single end param choose at the beggining, set the corresponding task
            qiime2_feature_process : ProcessProxy = protocol.add_process(task_feature_inference, 'feature_process', config_params=ubiome_state.get_feature_inference_config()["config"])

            # Retrieve qc output
            scenario_qc_id = ubiome_state.get_scenario_step_qc()[0].id
            scenario_proxy_qc = ScenarioProxy.from_existing_scenario(scenario_qc_id)
            protocol_proxy_qc: ProtocolProxy = scenario_proxy_qc.get_protocol()
            qc_output : Folder = protocol_proxy_qc.get_process('qc_process').get_output('result_folder')

            qc_resource = protocol.add_process(
                InputTask, 'qc_resource',
                {InputTask.config_name: qc_output.get_model_id()})

            # Connect it to the input of the task
            protocol.add_connector(out_port=qc_resource >> 'resource',
                                        in_port=qiime2_feature_process << 'quality_check_folder')
            # Add output
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

        if list_scenario_fi:
            # Create data for SlickGrid table
            table_data = []
            all_param_keys = set()  # To collect all unique parameter keys

            # First pass: collect all parameter data and unique keys
            scenarios_params = []
            for scenario in list_scenario_fi:
                scenario_proxy = ScenarioProxy.from_existing_scenario(scenario.id)
                protocol_proxy = scenario_proxy.get_protocol()
                feature_process = protocol_proxy.get_process('feature_process')
                config_params = feature_process._process_model.config.to_simple_dto().values
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

            # Create columns dynamically
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
            for param_key in sorted(all_param_keys):
                # Create a more readable column name
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

            out = slickgrid(table_data, columns=columns, options=options, key="feature_inference_grid", on_click="rerun")

            if out is not None:
                row_id, col = out
                # Handle row click - you can add specific actions here
                selected_fi_scenario = next((s for s in list_scenario_fi if s.id == row_id), None)
                if selected_fi_scenario:
                    # Update tree menu selection using the state method
                    ubiome_state.update_tree_menu_selection(selected_fi_scenario.id)
                    st.rerun()
        else:
            st.info("No Feature Inference analyses found.")
    else:
        # Display details about scenario feature inference
        scenario_proxy = ScenarioProxy.from_existing_scenario(selected_scenario.id)
        protocol_proxy: ProtocolProxy = scenario_proxy.get_protocol()

        # Get parameters
        feature_process = protocol_proxy.get_process('feature_process')
        config_params = feature_process._process_model.config.to_simple_dto().values

        st.write("### Feature Inference Scenario Results")

        # Display parameters in a table
        with st.expander("Parameters - Reminder"):

            # Create a DataFrame for parameters
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

        # Display results if scenario is successful
        if selected_scenario.status == ScenarioStatus.SUCCESS:

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
        session_state_key=ubiome_state.RAREFACTION_CONFIG_KEY, default_config_values=Qiime2RarefactionAnalysis.config_specs.get_default_values())

    if st.button("Run Rarefaction", use_container_width=True, icon=":material/play_arrow:", key="button_rarefaction"):
        if not ubiome_state.get_rarefaction_config()["is_valid"]:
            st.warning("Please fill all the mandatory fields.")
            return
        with StreamlitAuthenticateUser():
            # Create a new scenario in the lab
            folder : SpaceFolder = SpaceFolder.get_by_id(ubiome_state.get_selected_folder_id())
            scenario: ScenarioProxy = ScenarioProxy(
                None, folder=folder, title=f"{ubiome_state.get_current_analysis_name()} - Rarefaction",
                creation_type=ScenarioCreationType.MANUAL,
            )
            protocol: ProtocolProxy = scenario.get_protocol()

            feature_scenario_id = ubiome_state.get_current_feature_scenario_id_parent()

            # Add tags to the scenario
            scenario.add_tag(Tag(ubiome_state.TAG_FASTQ, ubiome_state.get_current_fastq_name(), is_propagable=True, auto_parse=True))
            scenario.add_tag(Tag(ubiome_state.TAG_BRICK, ubiome_state.TAG_UBIOME, is_propagable=True, auto_parse=True))
            scenario.add_tag(Tag(ubiome_state.TAG_UBIOME, ubiome_state.TAG_RAREFACTION, is_propagable=True))
            scenario.add_tag(Tag(ubiome_state.TAG_ANALYSIS_NAME, ubiome_state.get_current_analysis_name(), is_propagable=True, auto_parse=True))
            scenario.add_tag(Tag(ubiome_state.TAG_UBIOME_PIPELINE_ID, ubiome_state.get_current_ubiome_pipeline_id(), is_propagable=True, auto_parse=True))
            scenario.add_tag(Tag(ubiome_state.TAG_FEATURE_INFERENCE_ID, feature_scenario_id, is_propagable=True, auto_parse=True))
            # Add rarefaction process
            rarefaction_process : ProcessProxy = protocol.add_process(Qiime2RarefactionAnalysis, 'rarefaction_process', config_params=ubiome_state.get_rarefaction_config()["config"])

            # Retrieve feature inference output
            # Get the feature inference scenario
            scenario_proxy_fi = ScenarioProxy.from_existing_scenario(feature_scenario_id)
            protocol_proxy_fi: ProtocolProxy = scenario_proxy_fi.get_protocol()
            feature_output : Folder = protocol_proxy_fi.get_process('feature_process').get_output('result_folder')

            feature_resource = protocol.add_process(
                InputTask, 'feature_resource',
                {InputTask.config_name: feature_output.get_model_id()})

            # Connect it to the input of the rarefaction task
            protocol.add_connector(out_port=feature_resource >> 'resource',
                                    in_port=rarefaction_process << 'feature_frequency_folder')

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
        # We're in the general rarefaction view, show all feature inference scenarios
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

        if list_scenario_rarefaction:
            # Create data for SlickGrid table
            table_data = []
            all_param_keys = set()  # To collect all unique parameter keys

            # First pass: collect all parameter data and unique keys
            scenarios_params = []
            for scenario in list_scenario_rarefaction:
                scenario_proxy = ScenarioProxy.from_existing_scenario(scenario.id)
                protocol_proxy = scenario_proxy.get_protocol()
                rarefaction_process = protocol_proxy.get_process('rarefaction_process')
                config_params = rarefaction_process._process_model.config.to_simple_dto().values
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

            # Create columns dynamically
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
            for param_key in sorted(all_param_keys):
                # Create a more readable column name
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

            out = slickgrid(table_data, columns=columns, options=options, key="rarefaction_grid", on_click="rerun")

            if out is not None:
                row_id, col = out
                # Handle row click
                selected_rarefaction_scenario = next((s for s in list_scenario_rarefaction if s.id == row_id), None)
                if selected_rarefaction_scenario:
                    # Update tree menu selection using the state method
                    ubiome_state.update_tree_menu_selection(selected_rarefaction_scenario.id)
                    st.rerun()
        else:
            st.info("No Rarefaction analyses found.")
    else:
        # Display details about scenario rarefaction
        scenario_proxy = ScenarioProxy.from_existing_scenario(selected_scenario.id)
        protocol_proxy: ProtocolProxy = scenario_proxy.get_protocol()

        # Get parameters
        rarefaction_process = protocol_proxy.get_process('rarefaction_process')
        config_params = rarefaction_process._process_model.config.to_simple_dto().values

        st.write("### Rarefaction Scenario Results")

        # Display parameters in a table
        with st.expander("Parameters - Reminder"):

            # Create a DataFrame for parameters
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

        # Display results if scenario is successful
        if selected_scenario.status == ScenarioStatus.SUCCESS:
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