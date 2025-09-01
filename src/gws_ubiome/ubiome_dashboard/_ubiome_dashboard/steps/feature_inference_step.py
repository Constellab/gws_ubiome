import streamlit as st
from state import State
from gws_core.streamlit import StreamlitAuthenticateUser, StreamlitTaskRunner
from gws_core import Task, Scenario, ScenarioProxy, Tag, InputTask, Scenario, ScenarioStatus, ScenarioProxy
from gws_ubiome import Qiime2FeatureTableExtractorPE, Qiime2FeatureTableExtractorSE
from gws_ubiome.ubiome_dashboard._ubiome_dashboard.functions_steps import create_base_scenario_with_tags, render_scenario_table, display_scenario_parameters

@st.dialog("Feature inference parameters")
def dialog_feature_inference_params(task_feature_inference: Task, ubiome_state: State):
    st.text_input("Feature inference scenario name:", placeholder="Enter feature inference scenario name", value=f"{ubiome_state.get_current_analysis_name()} - Feature Inference", key=ubiome_state.FEATURE_SCENARIO_NAME_INPUT_KEY)
    form_config = StreamlitTaskRunner(task_feature_inference)
    form_config.generate_config_form_without_run(
        session_state_key=ubiome_state.FEATURE_INFERENCE_CONFIG_KEY,
        default_config_values=task_feature_inference.config_specs.get_default_values(),
        is_default_config_valid=task_feature_inference.config_specs.mandatory_values_are_set(
            task_feature_inference.config_specs.get_default_values()))

    if st.button("Run Feature Inference", use_container_width=True, icon=":material/play_arrow:", key="button_fei"):
        if not ubiome_state.get_feature_inference_config()["is_valid"]:
            st.warning("Please fill all the mandatory fields.")
            return

        with StreamlitAuthenticateUser():
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

            scenario.add_to_queue()
            ubiome_state.reset_tree_analysis()
            ubiome_state.set_tree_default_item(scenario.get_model_id())
            st.rerun()

def render_feature_inference_step(selected_scenario: Scenario, ubiome_state: State) -> None:
    if not selected_scenario:
        # The task to display depends of single-end or paired-end
        if ubiome_state.get_sequencing_type() == "paired-end":
            task_feature_inference = Qiime2FeatureTableExtractorPE
        else:
            task_feature_inference = Qiime2FeatureTableExtractorSE

        if not ubiome_state.get_is_standalone():

            # On click, open a dialog to allow the user to select params of feature inference
            st.button("Run new Feature Inference", icon=":material/play_arrow:", use_container_width=False,
                    on_click=lambda task=task_feature_inference, state=ubiome_state: dialog_feature_inference_params(task, state))

        # Display table of existing Feature Inference scenarios
        st.markdown("### Previous Feature Inference Analyses")

        list_scenario_fi = ubiome_state.get_scenario_step_feature_inference()
        render_scenario_table(list_scenario_fi, 'feature_process', 'feature_inference_grid', ubiome_state)
    else:
        # Display details about scenario feature inference
        st.markdown("##### Feature Inference Scenario Results")
        display_scenario_parameters(selected_scenario, 'feature_process')
        if selected_scenario.status != ScenarioStatus.SUCCESS:
            return

        # Display results if scenario is successful
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