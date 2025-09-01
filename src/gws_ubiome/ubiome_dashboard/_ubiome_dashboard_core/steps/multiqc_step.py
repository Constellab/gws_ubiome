import streamlit as st
from gws_ubiome.ubiome_dashboard._ubiome_dashboard_core.state import State
from gws_core import GenerateShareLinkDTO, ShareLinkEntityType, ShareLinkService, FsNodeExtractor, Scenario, ScenarioProxy, ProtocolProxy, InputTask, ProcessProxy, Scenario, ScenarioStatus, ScenarioProxy, ProtocolProxy
from gws_omix.rna_seq.multiqc.multiqc import MultiQc
from gws_omix.rna_seq.quality_check.fastq_init import FastqcInit
from gws_ubiome.ubiome_dashboard._ubiome_dashboard_core.functions_steps import create_base_scenario_with_tags

def render_multiqc_step(selected_scenario: Scenario, ubiome_state: State) -> None:

    if not selected_scenario:
        # Check if QC has been run successfully
        qc_scenarios = ubiome_state.get_scenario_step_qc()
        if not qc_scenarios or qc_scenarios[0].status != ScenarioStatus.SUCCESS:
            st.info("Please run the QC step successfully before running MultiQC.")
            return
        if ubiome_state.get_is_standalone():
            st.info("MultiQC has not been run.")
            return

        if st.button("Run MultiQC", icon=":material/play_arrow:", use_container_width=False):
            # Create a new scenario for MultiQC
            scenario = create_base_scenario_with_tags(ubiome_state, ubiome_state.TAG_MULTIQC, f"{ubiome_state.get_current_analysis_name()} - MultiQC")
            protocol: ProtocolProxy = scenario.get_protocol()

            # Get input resources from the current MultiQC scenario or create new ones
            fastq_resource = protocol.add_process(
                InputTask, 'fastq_resource',
                {InputTask.config_name: ubiome_state.get_resource_id_fastq()})

            metadata_resource = protocol.add_process(
                InputTask, 'metadata_resource',
                {InputTask.config_name: ubiome_state.get_resource_id_metadata_table()})

            # FastQC and MultiQC tasks
            fastqc_process : ProcessProxy = protocol.add_process(FastqcInit, 'fastqc_process')
            protocol.add_connector(out_port=fastq_resource >> 'resource',
                                    in_port=fastqc_process << 'fastq_folder')
            protocol.add_connector(out_port=metadata_resource >> 'resource',
                                in_port=fastqc_process << 'metadata')

            multiqc_process : ProcessProxy = protocol.add_process(MultiQc, 'multiqc_process')
            protocol.add_connector(out_port=fastqc_process >> 'output',
                                    in_port=multiqc_process << 'fastqc_reports_folder')

            # Extract the html ressource
            fs_node_extractor_html = protocol.add_process(FsNodeExtractor, 'fs_node_extractor_html', {"fs_node_path": "multiqc_combined.html"})
            # Add connectors
            protocol.add_connector(out_port=multiqc_process >> 'output', in_port=fs_node_extractor_html << "source")
            protocol.add_output('multiqc_process_output_html', fs_node_extractor_html >> "target", flag_resource=False)
            scenario.add_to_queue()

            ubiome_state.reset_tree_analysis()
            ubiome_state.set_tree_default_item(scenario.get_model_id())
            st.rerun()

    else:
        # Visualize MultiQC results
        st.markdown("##### MultiQC Results")
        if selected_scenario.status != ScenarioStatus.SUCCESS:
            return

        scenario_proxy = ScenarioProxy.from_existing_scenario(selected_scenario.id)
        protocol_proxy: ProtocolProxy = scenario_proxy.get_protocol()

        # Retrieve html output
        multiqc_output = protocol_proxy.get_process('fs_node_extractor_html').get_output('target')

        # Generate a public share link for the html
        generate_link_dto = GenerateShareLinkDTO.get_1_hour_validity(
            entity_id=multiqc_output.get_model_id(),
            entity_type=ShareLinkEntityType.RESOURCE
        )

        share_link = ShareLinkService.get_or_create_valid_public_share_link(generate_link_dto)
        # Display html
        st.components.v1.iframe(share_link.get_public_link(), scrolling=True, height=500)
