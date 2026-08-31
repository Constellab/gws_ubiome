import streamlit as st
from gws_core import Scenario, ScenarioProxy, ScenarioStatus
from gws_streamlit_main import StreamlitTaskRunner
from gws_ubiome import Qiime2TaxonomyDiversity

from ..functions_steps import (
    display_saved_scenario_actions,
    display_scenario_parameters,
    render_scenario_table,
)
from ..state import State
from ..ubiome_scenario_service import UbiomeScenarioService


@st.dialog("Taxonomy parameters")
def dialog_taxonomy_params(ubiome_state: State):
    translate_service = ubiome_state.get_translate_service()
    st.text_input(
        translate_service.translate("taxonomy_scenario_name"),
        placeholder=translate_service.translate("enter_taxonomy_name"),
        value=f"{ubiome_state.get_current_analysis_name()} - Taxonomy",
        key=UbiomeScenarioService.TAXONOMY_SCENARIO_NAME_INPUT_KEY,
    )
    form_config = StreamlitTaskRunner(Qiime2TaxonomyDiversity)
    form_config.generate_config_form_without_run(
        session_state_key=UbiomeScenarioService.TAXONOMY_CONFIG_KEY,
        default_config_values=Qiime2TaxonomyDiversity.config_specs.get_default_values(),
        is_default_config_valid=Qiime2TaxonomyDiversity.config_specs.mandatory_values_are_set(
            Qiime2TaxonomyDiversity.config_specs.get_default_values()
        ),
    )

    # Add both Save and Run buttons
    col1, col2 = st.columns(2)

    with col1:
        save_clicked = st.button(
            translate_service.translate("save_taxonomy"),
            width="stretch",
            icon=":material/save:",
            key="button_taxonomy_save",
        )

    with col2:
        run_clicked = st.button(
            translate_service.translate("run_taxonomy"),
            width="stretch",
            icon=":material/play_arrow:",
            key="button_taxonomy_run",
        )

    if save_clicked or run_clicked:
        if not ubiome_state.get_taxonomy_config()["is_valid"]:
            st.warning(translate_service.translate("fill_mandatory_fields"))
            return

        scenario = UbiomeScenarioService.create_taxonomy_scenario(
            folder_id=ubiome_state.get_selected_folder_id(),
            fastq_name=ubiome_state.get_current_fastq_name(),
            analysis_name=ubiome_state.get_current_analysis_name(),
            pipeline_id=ubiome_state.get_current_ubiome_pipeline_id(),
            title=ubiome_state.get_scenario_user_name(
                UbiomeScenarioService.TAXONOMY_SCENARIO_NAME_INPUT_KEY
            ),
            config=ubiome_state.get_taxonomy_config()["config"],
            feature_scenario_id=ubiome_state.get_current_feature_scenario_id_parent(),
        )
        if run_clicked:
            scenario.add_to_queue()
            ubiome_state.reset_tree_analysis()
            ubiome_state.set_tree_default_item(scenario.get_model_id())
        st.rerun()


def render_taxonomy_step(selected_scenario: Scenario, ubiome_state: State) -> None:
    translate_service = ubiome_state.get_translate_service()

    # Get the selected tree menu item to determine which feature inference scenario is selected
    tree_menu = ubiome_state.get_tree_menu_object()
    selected_item = tree_menu.get_selected_item()
    if selected_item.key.startswith(UbiomeScenarioService.TAG_TAXONOMY):
        feature_scenario_parent_id = ubiome_state.get_parent_feature_inference_scenario_from_step()
        # save in session state
        ubiome_state.set_current_feature_scenario_id_parent(feature_scenario_parent_id.id)

    if not selected_scenario:
        if not ubiome_state.get_is_standalone():
            # On click, open a dialog to allow the user to select params of taxonomy
            st.button(
                translate_service.translate("configure_new_taxonomy_scenario"),
                icon=":material/edit:",
                width="content",
                on_click=lambda state=ubiome_state: dialog_taxonomy_params(state),
            )

        # Display table of existing Taxonomy scenarios
        st.markdown(f"### {translate_service.translate('list_scenarios')}")

        list_scenario_taxonomy = ubiome_state.get_scenario_step_taxonomy()
        render_scenario_table(
            list_scenario_taxonomy, "taxonomy_process", "taxonomy_grid", ubiome_state
        )
    else:
        # Display details about scenario taxonomy
        st.markdown(f"##### {translate_service.translate('taxonomy_scenario_results')}")
        display_scenario_parameters(selected_scenario, "taxonomy_process", ubiome_state)

        if (
            selected_scenario.status == ScenarioStatus.DRAFT
            and not ubiome_state.get_is_standalone()
        ):
            display_saved_scenario_actions(selected_scenario, ubiome_state)

        if selected_scenario.status != ScenarioStatus.SUCCESS:
            return

        # Display results if scenario is successful
        scenario_proxy = ScenarioProxy.from_existing_scenario(selected_scenario.id)
        protocol_proxy = scenario_proxy.get_protocol()

        tab_diversity, tab_taxonomy = st.tabs(
            [
                translate_service.translate("diversity_tables"),
                translate_service.translate("taxonomy_tables"),
            ]
        )

        with tab_diversity:
            # Display diversity tables
            diversity_resource_set = protocol_proxy.get_process("taxonomy_process").get_output(
                "diversity_tables"
            )
            if diversity_resource_set:
                resource_set_result_dict = diversity_resource_set.get_resources()
                selected_result = st.selectbox(
                    translate_service.translate("select_diversity_table"),
                    options=resource_set_result_dict.keys(),
                    key="diversity_select",
                )
                if selected_result:
                    selected_resource = resource_set_result_dict.get(selected_result)
                    if selected_resource.get_typing_name() == "RESOURCE.gws_core.Table":
                        st.dataframe(selected_resource.get_data())
                    elif selected_resource.get_typing_name() == "RESOURCE.gws_core.PlotlyResource":
                        st.plotly_chart(selected_resource.get_figure())

        with tab_taxonomy:
            # Display taxonomy tables
            taxonomy_resource_set = protocol_proxy.get_process("taxonomy_process").get_output(
                "taxonomy_tables"
            )
            if taxonomy_resource_set:
                resource_set_result_dict = taxonomy_resource_set.get_resources()
                selected_result = st.selectbox(
                    translate_service.translate("select_result_display"),
                    options=resource_set_result_dict.keys(),
                    key="taxonomy_select",
                )
                if selected_result:
                    selected_resource = resource_set_result_dict.get(selected_result)
                    if selected_resource.get_typing_name() == "RESOURCE.gws_core.Table":
                        st.dataframe(selected_resource.get_data())
                    elif selected_resource.get_typing_name() == "RESOURCE.gws_core.PlotlyResource":
                        st.plotly_chart(selected_resource.get_figure())
