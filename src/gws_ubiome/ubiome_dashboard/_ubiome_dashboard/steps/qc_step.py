import streamlit as st
from state import State
from gws_core import ResourceSet, Scenario, ScenarioProxy, ProtocolProxy, InputTask, ProcessProxy, Scenario, ScenarioStatus, ScenarioProxy, ProtocolProxy
from gws_ubiome import Qiime2QualityCheck
from gws_ubiome.ubiome_dashboard._ubiome_dashboard.functions_steps import create_base_scenario_with_tags

def render_qc_step(selected_scenario: Scenario, ubiome_state: State) -> None:

    if not selected_scenario:
        # If a metadata table has been saved, allow running QC
        # Check if there's an updated metadata table first
        file_metadata = search_updated_metadata_table(ubiome_state)
        if not file_metadata:
            st.info("Please save a metadata table with at least one new metadata column to proceed.")
            return

        if st.button("Run quality check", icon=":material/play_arrow:", use_container_width=False):
            # Create a new scenario in the lab
            scenario = create_base_scenario_with_tags(ubiome_state, ubiome_state.TAG_QC, f"{ubiome_state.get_current_analysis_name()} - Quality check")
            protocol: ProtocolProxy = scenario.get_protocol()

            metadata_resource = protocol.add_process(
                InputTask, 'metadata_resource',
                {InputTask.config_name: ubiome_state.get_resource_id_metadata_table()})

            fastq_resource = protocol.add_process(
                InputTask, 'fastq_resource',
                {InputTask.config_name: ubiome_state.get_resource_id_fastq()})


            # Step 2 : QC task
            qc_process : ProcessProxy = protocol.add_process(Qiime2QualityCheck, 'qc_process', config_params= {"sequencing_type": ubiome_state.get_sequencing_type()})
            protocol.add_connector(out_port=fastq_resource >> 'resource',
                                       in_port=qc_process << 'fastq_folder')
            protocol.add_connector(out_port=metadata_resource >> 'resource',
                                   in_port=qc_process << 'metadata_table')
            # Add output
            protocol.add_output('qc_process_output_folder', qc_process >> 'result_folder', flag_resource=False)
            protocol.add_output('qc_process_output_quality_table', qc_process >> 'quality_table', flag_resource=False)
            scenario.add_to_queue()

            ubiome_state.reset_tree_analysis()
            ubiome_state.set_tree_default_item(scenario.get_model_id())
            st.rerun()

    else :
        # Visualize QC results
        st.markdown("##### Quality Control Results")
        if selected_scenario.status != ScenarioStatus.SUCCESS:
            return

        scenario_proxy = ScenarioProxy.from_existing_scenario(selected_scenario.id)
        protocol_proxy: ProtocolProxy = scenario_proxy.get_protocol()

        # Retrieve the resource set and save in a variable each visualization
        # Retrieve outputs
        resource_set_output : ResourceSet = protocol_proxy.get_process('qc_process').get_output('quality_table')
        resource_set_result_dict = resource_set_output.get_resources()

        # Create tabs for each result

        tab_names = list(resource_set_result_dict.keys())
        tabs = st.tabs(tab_names)

        for tab, result_name in zip(tabs, tab_names):
            with tab:
                selected_resource = resource_set_result_dict.get(result_name)
                if selected_resource.get_typing_name() == "RESOURCE.gws_core.Table":
                    st.dataframe(selected_resource.get_data())
                elif selected_resource.get_typing_name() == "RESOURCE.gws_core.PlotlyResource":
                    st.plotly_chart(selected_resource.get_figure())