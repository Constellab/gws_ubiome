import streamlit as st
from gws_core import (
    GenerateShareLinkDTO,
    ProtocolProxy,
    Scenario,
    ScenarioProxy,
    ScenarioStatus,
    ShareLinkEntityType,
    ShareLinkService,
)
from gws_streamlit_main import StreamlitContainers

from ..state import State
from ..ubiome_scenario_service import UbiomeScenarioService


def render_multiqc_step(selected_scenario: Scenario, ubiome_state: State) -> None:
    translate_service = ubiome_state.get_translate_service()

    if not selected_scenario:
        # Check if QC has been run successfully
        qc_scenarios = ubiome_state.get_scenario_step_qc()
        if not qc_scenarios or qc_scenarios[0].status != ScenarioStatus.SUCCESS:
            st.info(translate_service.translate("qc_run_successfully_info"))
            return
        if ubiome_state.get_is_standalone():
            st.info(translate_service.translate("multiqc_not_run"))
            return

        if st.button(
            translate_service.translate("run_multiqc"),
            icon=":material/play_arrow:",
            width="content",
        ):
            scenario = UbiomeScenarioService.create_multiqc_scenario(
                folder_id=ubiome_state.get_selected_folder_id(),
                fastq_name=ubiome_state.get_current_fastq_name(),
                analysis_name=ubiome_state.get_current_analysis_name(),
                pipeline_id=ubiome_state.get_current_ubiome_pipeline_id(),
                fastq_resource_id=ubiome_state.get_resource_id_fastq(),
                metadata_resource_id=ubiome_state.get_resource_id_metadata_table(),
            )
            scenario.add_to_queue()
            ubiome_state.reset_tree_analysis()
            ubiome_state.set_tree_default_item(scenario.get_model_id())
            st.rerun()

    else:
        # Visualize MultiQC results
        col_title, col_button_html = StreamlitContainers.columns_with_fit_content(
            key="container_html_header", cols=[1, "fit-content"], vertical_align_items="center"
        )
        with col_title:
            st.markdown(f"##### {translate_service.translate('multiqc_results')}")
        if selected_scenario.status != ScenarioStatus.SUCCESS:
            return

        scenario_proxy = ScenarioProxy.from_existing_scenario(selected_scenario.id)
        protocol_proxy: ProtocolProxy = scenario_proxy.get_protocol()

        # Retrieve html output
        multiqc_output = protocol_proxy.get_process("fs_node_extractor_html").get_output("target")

        # Generate a public share link for the html
        generate_link_dto = GenerateShareLinkDTO.get_1_hour_validity(
            entity_id=multiqc_output.get_model_id(), entity_type=ShareLinkEntityType.RESOURCE
        )

        share_link = ShareLinkService.get_or_create_valid_public_share_link(generate_link_dto)
        with col_button_html:
            st.markdown(
                f"[{translate_service.translate('view_multiqc_report')}]({share_link.get_public_link()})"
            )
        # Display html
        st.components.v1.iframe(share_link.get_public_link(), scrolling=True, height=500)
