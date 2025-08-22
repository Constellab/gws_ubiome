import os
import streamlit as st
import pandas as pd
from state import State
from gws_core.streamlit import StreamlitContainers, StreamlitResourceSelect, StreamlitRouter
from gws_ubiome.ubiome_dashboard._ubiome_dashboard.ubiome_config import UbiomeConfig
import pandas as pd
from gws_core import ResourceSet, Folder, Settings, ResourceModel, ResourceOrigin, Scenario, ScenarioProxy, ProtocolProxy, File, TableImporter, SpaceFolder, StringHelper, Tag, InputTask, SpaceService, ProcessProxy, ScenarioSearchBuilder, TagValueModel, Scenario, ScenarioStatus, ScenarioProxy, ProtocolProxy, ScenarioCreationType
from gws_ubiome import Qiime2QualityCheck
from gws_omix.rna_seq.multiqc.multiqc import MultiQc
from gws_omix.rna_seq.quality_check.fastq_init import FastqcInit
import streamlit.components.v1 as components


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

    # TODO Save button only appear if QC task have not been created

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
                    st.plotly_chart(selected_resource) # TODO : vérifier que c'est bon une fois que ce sera transformé en plotly

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

def render_feature_inference_step(selected_scenario: Scenario, ubiome_state: State) -> None:
    pass