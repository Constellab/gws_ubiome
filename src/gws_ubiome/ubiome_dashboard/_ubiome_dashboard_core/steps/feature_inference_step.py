import streamlit as st
from gws_core import InputTask, Scenario, ScenarioProxy, ScenarioStatus, Tag, Task
from gws_streamlit_main import StreamlitTaskRunner
from gws_ubiome import Qiime2FeatureTableExtractorPE, Qiime2FeatureTableExtractorSE
from ..functions_steps import (
    create_base_scenario_with_tags,
    display_saved_scenario_actions,
    display_scenario_parameters,
    render_scenario_table,
)
from ..state import State


@st.dialog("Feature inference parameters")
def dialog_feature_inference_params(task_feature_inference: Task, ubiome_state: State):
    translate_service = ubiome_state.get_translate_service()
    st.text_input(translate_service.translate("feature_inference_scenario_name"), placeholder=translate_service.translate("enter_feature_inference_name"), value=f"{ubiome_state.get_current_analysis_name()} - Feature Inference", key=ubiome_state.FEATURE_SCENARIO_NAME_INPUT_KEY)
    form_config = StreamlitTaskRunner(task_feature_inference)
    form_config.generate_config_form_without_run(
        session_state_key=ubiome_state.FEATURE_INFERENCE_CONFIG_KEY,
        default_config_values=task_feature_inference.config_specs.get_default_values(),
        is_default_config_valid=task_feature_inference.config_specs.mandatory_values_are_set(
            task_feature_inference.config_specs.get_default_values()))

    # Add both Save and Run buttons
    col1, col2 = st.columns(2)

    with col1:
        save_clicked = st.button(translate_service.translate("save_feature_inference"), width="stretch", icon=":material/save:", key="button_fei_save")

    with col2:
        run_clicked = st.button(translate_service.translate("run_feature_inference"), width="stretch", icon=":material/play_arrow:", key="button_fei_run")

    if save_clicked or run_clicked:
        if not ubiome_state.get_feature_inference_config()["is_valid"]:
            st.warning(translate_service.translate("fill_mandatory_fields"))
            return

        scenario = create_base_scenario_with_tags(ubiome_state, ubiome_state.TAG_FEATURE_INFERENCE, ubiome_state.get_scenario_user_name(ubiome_state.FEATURE_SCENARIO_NAME_INPUT_KEY))
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

        # Only add to queue if Run was clicked
        if run_clicked:
            scenario.add_to_queue()
            ubiome_state.reset_tree_analysis()
            ubiome_state.set_tree_default_item(scenario.get_model_id())
        st.rerun()

def render_feature_inference_step(selected_scenario: Scenario, ubiome_state: State) -> None:
    translate_service = ubiome_state.get_translate_service()

    if not selected_scenario:
        # The task to display depends of single-end or paired-end
        if ubiome_state.get_sequencing_type() == "paired-end":
            task_feature_inference = Qiime2FeatureTableExtractorPE
        else:
            task_feature_inference = Qiime2FeatureTableExtractorSE

        if not ubiome_state.get_is_standalone():
            # On click, open a dialog to allow the user to select params of feature inference
            st.button(translate_service.translate("configure_new_feature_inference_scenario"), icon=":material/edit:", width="content",
                    on_click=lambda task=task_feature_inference, state=ubiome_state: dialog_feature_inference_params(task, state))

        # Display table of existing Feature Inference scenarios
        st.markdown(f"### {translate_service.translate('list_scenarios')}")

        list_scenario_fi = ubiome_state.get_scenario_step_feature_inference()
        render_scenario_table(list_scenario_fi, 'feature_process', 'feature_inference_grid', ubiome_state)
    else:
        # Display details about scenario feature inference
        st.markdown(f"##### {translate_service.translate('feature_inference_scenario_results')}")
        display_scenario_parameters(selected_scenario, 'feature_process', ubiome_state)

        if selected_scenario.status == ScenarioStatus.DRAFT and not ubiome_state.get_is_standalone():
            display_saved_scenario_actions(selected_scenario, ubiome_state)

        if selected_scenario.status != ScenarioStatus.SUCCESS:
            return

        # Display results if scenario is successful
        scenario_proxy = ScenarioProxy.from_existing_scenario(selected_scenario.id)
        protocol_proxy = scenario_proxy.get_protocol()

        tab_boxplot, tab_table = st.tabs([translate_service.translate("boxplot"), translate_service.translate("table")])

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
