import streamlit as st
from gws_core import (
    ProtocolProxy,
    ResourceSet,
    Scenario,
    ScenarioProxy,
    ScenarioStatus,
)

from ..functions_steps import (
    create_base_scenario_with_tags,
    search_updated_metadata_table,
)
from ..state import State
from ..ubiome_scenario_service import UbiomeScenarioService


def render_qc_step(selected_scenario: Scenario, ubiome_state: State) -> None:
    translate_service = ubiome_state.get_translate_service()

    if not selected_scenario:
        # If a metadata table has been saved, allow running QC
        # Check if there's an updated metadata table first
        file_metadata = search_updated_metadata_table(ubiome_state)
        if not file_metadata:
            st.info(translate_service.translate("save_metadata_table_info"))
            return

        if ubiome_state.get_is_standalone():
            return

        if st.button(
            translate_service.translate("run_quality_check"),
            icon=":material/play_arrow:",
            width="content",
        ):
            scenario = UbiomeScenarioService.create_qc_scenario(
                folder_id=ubiome_state.get_selected_folder_id(),
                fastq_name=ubiome_state.get_current_fastq_name(),
                analysis_name=ubiome_state.get_current_analysis_name(),
                pipeline_id=ubiome_state.get_current_ubiome_pipeline_id(),
                metadata_resource_id=ubiome_state.get_resource_id_metadata_table(),
                fastq_resource_id=ubiome_state.get_resource_id_fastq(),
                sequencing_type=ubiome_state.get_sequencing_type(),
            )
            scenario.add_to_queue()
            ubiome_state.reset_tree_analysis()
            ubiome_state.set_tree_default_item(scenario.get_model_id())
            st.rerun()

    else:
        # Visualize QC results
        st.markdown(f"##### {translate_service.translate('quality_control_results')}")
        if selected_scenario.status != ScenarioStatus.SUCCESS:
            return

        scenario_proxy = ScenarioProxy.from_existing_scenario(selected_scenario.id)
        protocol_proxy: ProtocolProxy = scenario_proxy.get_protocol()

        # Retrieve the resource set and save in a variable each visualization
        # Retrieve outputs
        resource_set_output: ResourceSet = protocol_proxy.get_process("qc_process").get_output(
            "quality_table"
        )
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
