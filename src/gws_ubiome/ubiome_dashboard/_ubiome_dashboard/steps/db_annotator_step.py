import streamlit as st
from state import State
from gws_core.streamlit import StreamlitAuthenticateUser, StreamlitResourceSelect
from gws_core import Scenario, ScenarioProxy, Tag, InputTask, Scenario, ScenarioStatus, ScenarioProxy
from gws_ubiome import Qiime2TableDbAnnotator
from gws_ubiome.ubiome_dashboard._ubiome_dashboard.functions_steps import create_base_scenario_with_tags, render_scenario_table, display_scenario_parameters


@st.dialog("DB annotator parameters")
def dialog_db_annotator_params(ubiome_state: State):
    st.text_input("Taxa Composition scenario name:", placeholder="Enter taxa composition scenario name", value=f"{ubiome_state.get_current_analysis_name()} - Taxa Composition", key=ubiome_state.DB_ANNOTATOR_SCENARIO_NAME_INPUT_KEY)
    # Display available annotation tables for user selection
    st.markdown("##### Select Annotation Table")
    # Use StreamlitResourceSelect to let user choose an annotation table
    resource_select = StreamlitResourceSelect()
    resource_select.select_resource(
        placeholder='Select annotation table', key=ubiome_state.SELECTED_ANNOTATION_TABLE_KEY, defaut_resource=None)

    if st.button("Run Taxa Composition", use_container_width=True, icon=":material/play_arrow:", key="button_db_annotator"):
        selected_annotation_table_id = ubiome_state.get_selected_annotation_table()["resourceId"]
        if not selected_annotation_table_id:
            st.warning("Please select an annotation table.")
            return

        with StreamlitAuthenticateUser():
            scenario = create_base_scenario_with_tags(ubiome_state, ubiome_state.TAG_DB_ANNOTATOR, ubiome_state.get_scenario_user_name(ubiome_state.DB_ANNOTATOR_SCENARIO_NAME_INPUT_KEY))
            taxonomy_scenario_id = ubiome_state.get_current_taxonomy_scenario_id_parent()
            feature_scenario_id = ubiome_state.get_current_feature_scenario_id_parent()
            scenario.add_tag(Tag(ubiome_state.TAG_FEATURE_INFERENCE_ID, feature_scenario_id, is_propagable=False, auto_parse=True))
            scenario.add_tag(Tag(ubiome_state.TAG_TAXONOMY_ID, taxonomy_scenario_id, is_propagable=False, auto_parse=True))
            protocol = scenario.get_protocol()

            # Add DB annotator process
            db_annotator_process = protocol.add_process(Qiime2TableDbAnnotator, 'db_annotator_process')

            # Get the taxonomy diversity folder
            scenario_proxy_tax = ScenarioProxy.from_existing_scenario(taxonomy_scenario_id)
            protocol_proxy_tax = scenario_proxy_tax.get_protocol()
            taxonomy_folder_output = protocol_proxy_tax.get_process('taxonomy_process').get_output('result_folder')

            # Add input resources
            taxonomy_folder_resource = protocol.add_process(InputTask, 'taxonomy_folder_resource',
                                                          {InputTask.config_name: taxonomy_folder_output.get_model_id()})

            annotation_table_resource = protocol.add_process(InputTask, 'annotation_table_resource',
                                                           {InputTask.config_name: selected_annotation_table_id})

            # Connect inputs to DB annotator process
            protocol.add_connector(out_port=taxonomy_folder_resource >> 'resource',
                                 in_port=db_annotator_process << 'diversity_folder')
            protocol.add_connector(out_port=annotation_table_resource >> 'resource',
                                 in_port=db_annotator_process << 'annotation_table')

            # Add outputs
            protocol.add_output('relative_abundance_table_output', db_annotator_process >> 'relative_abundance_table', flag_resource=False)
            protocol.add_output('relative_abundance_plotly_output', db_annotator_process >> 'relative_abundance_plotly_resource', flag_resource=False)
            protocol.add_output('absolute_abundance_table_output', db_annotator_process >> 'absolute_abundance_table', flag_resource=False)
            protocol.add_output('absolute_abundance_plotly_output', db_annotator_process >> 'absolute_abundance_plotly_resource', flag_resource=False)

            scenario.add_to_queue()
            ubiome_state.reset_tree_analysis()
            ubiome_state.set_tree_default_item(scenario.get_model_id())
            st.rerun()

def render_db_annotator_step(selected_scenario: Scenario, ubiome_state: State) -> None:
    # Get the selected tree menu item to determine which taxonomy scenario is selected
    tree_menu = ubiome_state.get_tree_menu_object()
    selected_item = tree_menu.get_selected_item()
    if selected_item.key.startswith(ubiome_state.TAG_DB_ANNOTATOR):
        taxonomy_scenario_parent_id = ubiome_state.get_parent_taxonomy_scenario_from_step()
        ubiome_state.set_current_taxonomy_scenario_id_parent(taxonomy_scenario_parent_id)
        # Retrieve the feature inference scenario ID using the utility function
        feature_inference_id = ubiome_state.get_feature_inference_id_from_taxonomy_scenario(taxonomy_scenario_parent_id)
        ubiome_state.set_current_feature_scenario_id_parent(feature_inference_id)

    if not selected_scenario:

        # On click, open a dialog to allow the user to select params of Taxa Composition
        st.button("Run new Taxa Composition", icon=":material/play_arrow:", use_container_width=False,
                        on_click=lambda state=ubiome_state: dialog_db_annotator_params(state))

        # Display table of existing Taxa Composition scenarios
        st.markdown("### Previous Taxa Composition Analyses")

        list_scenario_db_annotator = ubiome_state.get_scenario_step_db_annotator()
        render_scenario_table(list_scenario_db_annotator, 'db_annotator_process', 'db_annotator_grid', ubiome_state)

    else:
        # Display details about scenario DB annotator
        st.markdown("##### Taxa Composition Scenario Results")
        display_scenario_parameters(selected_scenario, 'db_annotator_process')

        if selected_scenario.status != ScenarioStatus.SUCCESS:
            return

        # Display results if scenario is successful
        scenario_proxy = ScenarioProxy.from_existing_scenario(selected_scenario.id)
        protocol_proxy = scenario_proxy.get_protocol()

        tab_relative, tab_absolute = st.tabs(["Relative Abundance", "Absolute Abundance"])

        with tab_relative:
            # Display relative abundance table and plot
            st.markdown("##### Relative Abundance Table")
            relative_table_output = protocol_proxy.get_process('db_annotator_process').get_output('relative_abundance_table')
            if relative_table_output:
                st.dataframe(relative_table_output.get_data())

            st.markdown("##### Relative Abundance Plot")
            relative_plot_output = protocol_proxy.get_process('db_annotator_process').get_output('relative_abundance_plotly_resource')
            if relative_plot_output:
                st.plotly_chart(relative_plot_output.get_figure())

        with tab_absolute:
            # Display absolute abundance table and plot
            st.markdown("##### Absolute Abundance Table")
            absolute_table_output = protocol_proxy.get_process('db_annotator_process').get_output('absolute_abundance_table')
            if absolute_table_output:
                st.dataframe(absolute_table_output.get_data())

            st.markdown("##### Absolute Abundance Plot")
            absolute_plot_output = protocol_proxy.get_process('db_annotator_process').get_output('absolute_abundance_plotly_resource')
            if absolute_plot_output:
                st.plotly_chart(absolute_plot_output.get_figure())