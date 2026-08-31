import streamlit as st
from gws_core import (
    Scenario,
    ScenarioProxy,
    ScenarioStatus,
)
from gws_streamlit_main import StreamlitTaskRunner
from gws_ubiome import Picrust2FunctionalAnalysis

from ..functions_steps import (
    display_saved_scenario_actions,
    display_scenario_parameters,
    export_scenario_to_lab_large,
    render_scenario_table,
)
from ..state import State
from ..ubiome_scenario_service import UbiomeScenarioService


@st.dialog("16S parameters")
def dialog_16s_params(ubiome_state: State):
    translate_service = ubiome_state.get_translate_service()
    st.text_input(
        translate_service.translate("16s_functional_analysis_scenario_name"),
        placeholder=translate_service.translate("enter_16s_functional_analysis_name"),
        value=f"{ubiome_state.get_current_analysis_name()} - 16S Functional Analysis",
        key=UbiomeScenarioService.FUNCTIONAL_ANALYSIS_SCENARIO_NAME_INPUT_KEY,
    )
    form_config = StreamlitTaskRunner(Picrust2FunctionalAnalysis)
    form_config.generate_config_form_without_run(
        session_state_key=UbiomeScenarioService.FUNCTIONAL_ANALYSIS_CONFIG_KEY,
        default_config_values=Picrust2FunctionalAnalysis.config_specs.get_default_values(),
        is_default_config_valid=Picrust2FunctionalAnalysis.config_specs.mandatory_values_are_set(
            Picrust2FunctionalAnalysis.config_specs.get_default_values()
        ),
    )
    # if there is a param credential to lab large entered in the dashboard, we will send the scenario to lab large to be executed
    # so the lab large need to be open
    if ubiome_state.get_credentials_lab_large():
        st.info(translate_service.translate("lab_large_must_be_open"))

    col1, col2 = st.columns(2)

    with col1:
        save_clicked = st.button(
            translate_service.translate("save_16s_functional_analysis"),
            width="stretch",
            icon=":material/save:",
            key="button_16s_save",
        )

    with col2:
        run_clicked = st.button(
            translate_service.translate("run_16s_functional_analysis"),
            width="stretch",
            icon=":material/play_arrow:",
            key="button_16s_run",
        )

    if save_clicked or run_clicked:
        if not ubiome_state.get_functional_analysis_config()["is_valid"]:
            st.warning(translate_service.translate("fill_mandatory_fields"))
            return

        scenario = create_base_scenario_with_tags(
            ubiome_state,
            UbiomeScenarioService.TAG_16S,
            ubiome_state.get_scenario_user_name(
                UbiomeScenarioService.FUNCTIONAL_ANALYSIS_SCENARIO_NAME_INPUT_KEY
            ),
        )
        feature_scenario_id = ubiome_state.get_current_feature_scenario_id_parent()
        scenario.add_tag(
            Tag(
                UbiomeScenarioService.TAG_FEATURE_INFERENCE_ID,
                feature_scenario_id,
                is_propagable=False,
                auto_parse=True,
            )
        )
        scenario.add_tag(
            Tag(
                UbiomeScenarioService.TAG_16S_ID,
                scenario.get_model_id(),
                is_propagable=False,
                auto_parse=True,
            )
        )
        protocol = scenario.get_protocol()

        # Retrieve feature inference outputs and extract table.qza and asv
        scenario_proxy_fi = ScenarioProxy.from_existing_scenario(feature_scenario_id)
        protocol_proxy_fi = scenario_proxy_fi.get_protocol()
        feature_output = protocol_proxy_fi.get_process("feature_process").get_output(
            "result_folder"
        )

        # Get the table.qza and ASV-sequences.fasta from feature inference output
        feature_resource = protocol.add_process(
            InputTask, "feature_resource", {InputTask.config_name: feature_output.get_model_id()}
        )
        fs_node_extractor_table = protocol.add_process(
            FsNodeExtractor, "fs_node_extractor_table", {"fs_node_path": "table.qza"}
        )
        fs_node_extractor_asv = protocol.add_process(
            FsNodeExtractor, "fs_node_extractor_asv", {"fs_node_path": "ASV-sequences.fasta"}
        )
        # Add connectors
        protocol.add_connector(
            out_port=feature_resource >> "resource", in_port=fs_node_extractor_table << "source"
        )
        protocol.add_connector(
            out_port=feature_resource >> "resource", in_port=fs_node_extractor_asv << "source"
        )
        # Add 16S functional analysis process
        functional_analysis_process = protocol.add_process(
            Picrust2FunctionalAnalysis,
            "functional_analysis_process",
            config_params=ubiome_state.get_functional_analysis_config()["config"],
        )

        # The task expects table.qza for ASV_count_abundance and ASV-sequences.fasta for FASTA_of_asv
        protocol.add_connector(
            out_port=fs_node_extractor_table >> "target",
            in_port=functional_analysis_process << "ASV_count_abundance",
        )
        protocol.add_connector(
            out_port=fs_node_extractor_asv >> "target",
            in_port=functional_analysis_process << "FASTA_of_asv",
        )

        # Add outputs
        protocol.add_output(
            "functional_analysis_result_output",
            functional_analysis_process >> "Folder_result",
            flag_resource=False,
        )

        # Only add to queue or transfer if Run was clicked
        if run_clicked:
            # if there is a param credential to lab large entered in the dashboard, send the scenario to lab large to be executed
            if ubiome_state.get_credentials_lab_large():
                export_scenario_to_lab_large(
                    scenario.get_model_id(),
                    ubiome_state.get_credentials_lab_large(),
                    translate_service,
                )

            # if there is no param credential to lab large entered in the dashboard, the scenario will be executed in the current environment
            else:
                scenario.add_to_queue()
            ubiome_state.reset_tree_analysis()
            ubiome_state.set_tree_default_item(scenario.get_model_id())
        st.rerun()


def render_16s_step(selected_scenario: Scenario, ubiome_state: State) -> None:
    translate_service = ubiome_state.get_translate_service()

    # Get the selected tree menu item to determine which feature inference scenario is selected
    tree_menu = ubiome_state.get_tree_menu_object()
    selected_item = tree_menu.get_selected_item()
    if selected_item.key.startswith(UbiomeScenarioService.TAG_16S):
        feature_scenario_parent_id = ubiome_state.get_parent_feature_inference_scenario_from_step()
        # save in session state
        ubiome_state.set_current_feature_scenario_id_parent(feature_scenario_parent_id.id)

    if not selected_scenario:
        if not ubiome_state.get_is_standalone():
            # On click, open a dialog to allow the user to select params of 16S functional analysis
            st.button(
                translate_service.translate("configure_new_16s_functional_analysis_scenario"),
                icon=":material/edit:",
                width="content",
                on_click=lambda state=ubiome_state: dialog_16s_params(state),
            )

        # Display table of existing 16S Functional Analysis scenarios
        st.markdown(f"### {translate_service.translate('list_scenarios')}")

        list_scenario_16s = ubiome_state.get_scenario_step_16s()
        render_scenario_table(
            list_scenario_16s, "functional_analysis_process", "16s_functional_grid", ubiome_state
        )
    else:
        # Display details about scenario 16S functional analysis
        st.markdown(
            f"##### {translate_service.translate('16s_functional_analysis_scenario_results')}"
        )
        display_scenario_parameters(selected_scenario, "functional_analysis_process", ubiome_state)

        if ubiome_state.get_is_standalone():
            return

        if (
            selected_scenario.status == ScenarioStatus.DRAFT
            and not ubiome_state.get_is_standalone()
        ):
            display_saved_scenario_actions(selected_scenario, ubiome_state)

        if selected_scenario.status != ScenarioStatus.SUCCESS:
            return
