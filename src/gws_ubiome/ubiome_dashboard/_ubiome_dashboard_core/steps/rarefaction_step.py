import streamlit as st
from gws_ubiome.ubiome_dashboard._ubiome_dashboard_core.state import State
from gws_core.streamlit import StreamlitAuthenticateUser, StreamlitTaskRunner
from gws_core import Scenario, ScenarioProxy, Tag, InputTask, Scenario, ScenarioStatus, ScenarioProxy
from gws_ubiome import Qiime2RarefactionAnalysis
from gws_ubiome.ubiome_dashboard._ubiome_dashboard_core.functions_steps import display_saved_scenario_actions, create_base_scenario_with_tags, render_scenario_table, display_scenario_parameters

@st.dialog("Rarefaction parameters")
def dialog_rarefaction_params(ubiome_state: State):
    st.text_input("Rarefaction scenario name:", placeholder="Enter rarefaction scenario name", value=f"{ubiome_state.get_current_analysis_name()} - Rarefaction", key=ubiome_state.RAREFACTION_SCENARIO_NAME_INPUT_KEY)
    form_config = StreamlitTaskRunner(Qiime2RarefactionAnalysis)
    form_config.generate_config_form_without_run(
        session_state_key=ubiome_state.RAREFACTION_CONFIG_KEY,
        default_config_values=Qiime2RarefactionAnalysis.config_specs.get_default_values(),
        is_default_config_valid=Qiime2RarefactionAnalysis.config_specs.mandatory_values_are_set(
            Qiime2RarefactionAnalysis.config_specs.get_default_values()))

    # Add both Save and Run buttons
    col1, col2 = st.columns(2)

    with col1:
        save_clicked = st.button("Save Rarefaction", use_container_width=True, icon=":material/save:", key="button_rarefaction_save")

    with col2:
        run_clicked = st.button("Run Rarefaction", use_container_width=True, icon=":material/play_arrow:", key="button_rarefaction_run")

    if save_clicked or run_clicked:
        if not ubiome_state.get_rarefaction_config()["is_valid"]:
            st.warning("Please fill all the mandatory fields.")
            return

        with StreamlitAuthenticateUser():
            scenario = create_base_scenario_with_tags(ubiome_state, ubiome_state.TAG_RAREFACTION, ubiome_state.get_scenario_user_name(ubiome_state.RAREFACTION_SCENARIO_NAME_INPUT_KEY))
            feature_scenario_id = ubiome_state.get_current_feature_scenario_id_parent()
            scenario.add_tag(Tag(ubiome_state.TAG_FEATURE_INFERENCE_ID, feature_scenario_id, is_propagable=False, auto_parse=True))
            protocol = scenario.get_protocol()

            # Add rarefaction process
            rarefaction_process = protocol.add_process(Qiime2RarefactionAnalysis, 'rarefaction_process',
                                                     config_params=ubiome_state.get_rarefaction_config()["config"])

            # Retrieve feature inference output and connect
            scenario_proxy_fi = ScenarioProxy.from_existing_scenario(feature_scenario_id)
            protocol_proxy_fi = scenario_proxy_fi.get_protocol()
            feature_output = protocol_proxy_fi.get_process('feature_process').get_output('result_folder')

            feature_resource = protocol.add_process(InputTask, 'feature_resource', {InputTask.config_name: feature_output.get_model_id()})
            protocol.add_connector(out_port=feature_resource >> 'resource', in_port=rarefaction_process << 'feature_frequency_folder')

            # Add outputs
            protocol.add_output('rarefaction_table_output', rarefaction_process >> 'rarefaction_table', flag_resource=False)
            protocol.add_output('rarefaction_folder_output', rarefaction_process >> 'result_folder', flag_resource=False)

            # Only add to queue if Run was clicked
            if run_clicked:
                scenario.add_to_queue()
                ubiome_state.reset_tree_analysis()
                ubiome_state.set_tree_default_item(scenario.get_model_id())

            st.rerun()

def render_rarefaction_step(selected_scenario: Scenario, ubiome_state: State) -> None:
    # Get the selected tree menu item to determine which feature inference scenario is selected
    tree_menu = ubiome_state.get_tree_menu_object()
    selected_item = tree_menu.get_selected_item()
    if selected_item.key.startswith(ubiome_state.TAG_RAREFACTION):
        feature_scenario_parent_id = ubiome_state.get_parent_feature_inference_scenario_from_step()
        # save in session state
        ubiome_state.set_current_feature_scenario_id_parent(feature_scenario_parent_id.id)

    if not selected_scenario:
        if not ubiome_state.get_is_standalone():
            # On click, open a dialog to allow the user to select params of rarefaction
            st.button("Configure new Rarefaction scenario", icon=":material/edit:", use_container_width=False,
                        on_click=lambda state=ubiome_state: dialog_rarefaction_params(state))

        # Display table of existing Rarefaction scenarios
        st.markdown("### List of scenarios")

        list_scenario_rarefaction = ubiome_state.get_scenario_step_rarefaction()
        render_scenario_table(list_scenario_rarefaction, 'rarefaction_process', 'rarefaction_grid', ubiome_state)
    else:
        # Display details about scenario rarefaction
        st.markdown("##### Rarefaction Scenario Results")
        display_scenario_parameters(selected_scenario, 'rarefaction_process')

        if selected_scenario.status == ScenarioStatus.DRAFT:
            display_saved_scenario_actions(selected_scenario, ubiome_state)

        if selected_scenario.status != ScenarioStatus.SUCCESS:
            return

        # Display results if scenario is successful
        scenario_proxy = ScenarioProxy.from_existing_scenario(selected_scenario.id)
        protocol_proxy = scenario_proxy.get_protocol()
        # Display rarefaction table
        rarefaction_resource_set = protocol_proxy.get_process('rarefaction_process').get_output('rarefaction_table')
        if not rarefaction_resource_set:
            return

        resource_set_result_dict = rarefaction_resource_set.get_resources()
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