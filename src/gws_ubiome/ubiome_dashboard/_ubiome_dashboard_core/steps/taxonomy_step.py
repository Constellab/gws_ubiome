import streamlit as st
from gws_ubiome.ubiome_dashboard._ubiome_dashboard_core.state import State
from gws_core.streamlit import StreamlitAuthenticateUser, StreamlitTaskRunner
from gws_core import Scenario, ScenarioProxy, Tag, InputTask, Scenario, ScenarioStatus, ScenarioProxy
from gws_ubiome import  Qiime2TaxonomyDiversity
from gws_ubiome.ubiome_dashboard._ubiome_dashboard_core.functions_steps import display_saved_scenario_actions, create_base_scenario_with_tags, render_scenario_table, display_scenario_parameters

@st.dialog("Taxonomy parameters")
def dialog_taxonomy_params(ubiome_state: State):
    st.text_input("Taxonomy scenario name:", placeholder="Enter taxonomy scenario name", value=f"{ubiome_state.get_current_analysis_name()} - Taxonomy", key=ubiome_state.TAXONOMY_SCENARIO_NAME_INPUT_KEY)
    form_config = StreamlitTaskRunner(Qiime2TaxonomyDiversity)
    form_config.generate_config_form_without_run(
        session_state_key=ubiome_state.TAXONOMY_CONFIG_KEY,
        default_config_values=Qiime2TaxonomyDiversity.config_specs.get_default_values(),
        is_default_config_valid=Qiime2TaxonomyDiversity.config_specs.mandatory_values_are_set(
            Qiime2TaxonomyDiversity.config_specs.get_default_values()))

    # Add both Save and Run buttons
    col1, col2 = st.columns(2)

    with col1:
        save_clicked = st.button("Save Taxonomy", use_container_width=True, icon=":material/save:", key="button_taxonomy_save")

    with col2:
        run_clicked = st.button("Run Taxonomy", use_container_width=True, icon=":material/play_arrow:", key="button_taxonomy_run")

    if save_clicked or run_clicked:
        if not ubiome_state.get_taxonomy_config()["is_valid"]:
            st.warning("Please fill all the mandatory fields.")
            return

        with StreamlitAuthenticateUser():
            scenario = create_base_scenario_with_tags(ubiome_state, ubiome_state.TAG_TAXONOMY, ubiome_state.get_scenario_user_name(ubiome_state.TAXONOMY_SCENARIO_NAME_INPUT_KEY))
            feature_scenario_id = ubiome_state.get_current_feature_scenario_id_parent()
            scenario.add_tag(Tag(ubiome_state.TAG_FEATURE_INFERENCE_ID, feature_scenario_id, is_propagable=False, auto_parse=True))
            scenario.add_tag(Tag(ubiome_state.TAG_TAXONOMY_ID, scenario.get_model_id(), is_propagable=False, auto_parse=True))
            protocol = scenario.get_protocol()

            # Add taxonomy process
            taxonomy_process = protocol.add_process(Qiime2TaxonomyDiversity, 'taxonomy_process',
                                                  config_params=ubiome_state.get_taxonomy_config()["config"])

            # Retrieve feature inference output and connect
            scenario_proxy_fi = ScenarioProxy.from_existing_scenario(feature_scenario_id)
            protocol_proxy_fi = scenario_proxy_fi.get_protocol()
            feature_output = protocol_proxy_fi.get_process('feature_process').get_output('result_folder')

            feature_resource = protocol.add_process(InputTask, 'feature_resource', {InputTask.config_name: feature_output.get_model_id()})
            protocol.add_connector(out_port=feature_resource >> 'resource', in_port=taxonomy_process << 'rarefaction_analysis_result_folder')

            # Add outputs
            protocol.add_output('taxonomy_diversity_tables_output', taxonomy_process >> 'diversity_tables', flag_resource=False)
            protocol.add_output('taxonomy_taxonomy_tables_output', taxonomy_process >> 'taxonomy_tables', flag_resource=False)
            protocol.add_output('taxonomy_folder_output', taxonomy_process >> 'result_folder', flag_resource=False)

            # Only add to queue if Run was clicked
            if run_clicked:
                scenario.add_to_queue()
                ubiome_state.reset_tree_analysis()
                ubiome_state.set_tree_default_item(scenario.get_model_id())

            st.rerun()

def render_taxonomy_step(selected_scenario: Scenario, ubiome_state: State) -> None:
    # Get the selected tree menu item to determine which feature inference scenario is selected
    tree_menu = ubiome_state.get_tree_menu_object()
    selected_item = tree_menu.get_selected_item()
    if selected_item.key.startswith(ubiome_state.TAG_TAXONOMY):
        feature_scenario_parent_id = ubiome_state.get_parent_feature_inference_scenario_from_step()
        # save in session state
        ubiome_state.set_current_feature_scenario_id_parent(feature_scenario_parent_id.id)

    if not selected_scenario:
        if not ubiome_state.get_is_standalone():
            # On click, open a dialog to allow the user to select params of taxonomy
            st.button("Configure new Taxonomy scenario", icon=":material/edit:", use_container_width=False,
                        on_click=lambda state=ubiome_state: dialog_taxonomy_params(state))

        # Display table of existing Taxonomy scenarios
        st.markdown("### List of scenarios")

        list_scenario_taxonomy = ubiome_state.get_scenario_step_taxonomy()
        render_scenario_table(list_scenario_taxonomy, 'taxonomy_process', 'taxonomy_grid', ubiome_state)
    else:
        # Display details about scenario taxonomy
        st.markdown("##### Taxonomy Scenario Results")
        display_scenario_parameters(selected_scenario, 'taxonomy_process')

        if selected_scenario.status == ScenarioStatus.DRAFT:
            display_saved_scenario_actions(selected_scenario, ubiome_state)

        if selected_scenario.status != ScenarioStatus.SUCCESS:
            return

        # Display results if scenario is successful
        scenario_proxy = ScenarioProxy.from_existing_scenario(selected_scenario.id)
        protocol_proxy = scenario_proxy.get_protocol()

        tab_diversity, tab_taxonomy = st.tabs(["Diversity Tables", "Taxonomy Tables"])

        with tab_diversity:
            # Display diversity tables
            diversity_resource_set = protocol_proxy.get_process('taxonomy_process').get_output('diversity_tables')
            if diversity_resource_set:
                resource_set_result_dict = diversity_resource_set.get_resources()
                selected_result = st.selectbox("Select a diversity table to display", options=resource_set_result_dict.keys(), key="diversity_select")
                if selected_result:
                    selected_resource = resource_set_result_dict.get(selected_result)
                    if selected_resource.get_typing_name() == "RESOURCE.gws_core.Table":
                        st.dataframe(selected_resource.get_data())
                    elif selected_resource.get_typing_name() == "RESOURCE.gws_core.PlotlyResource":
                        st.plotly_chart(selected_resource.get_figure())

        with tab_taxonomy:
            # Display taxonomy tables
            taxonomy_resource_set = protocol_proxy.get_process('taxonomy_process').get_output('taxonomy_tables')
            if taxonomy_resource_set:
                resource_set_result_dict = taxonomy_resource_set.get_resources()
                selected_result = st.selectbox("Select a result to display", options=resource_set_result_dict.keys(), key="taxonomy_select")
                if selected_result:
                    selected_resource = resource_set_result_dict.get(selected_result)
                    if selected_resource.get_typing_name() == "RESOURCE.gws_core.Table":
                        st.dataframe(selected_resource.get_data())
                    elif selected_resource.get_typing_name() == "RESOURCE.gws_core.PlotlyResource":
                        st.plotly_chart(selected_resource.get_figure())