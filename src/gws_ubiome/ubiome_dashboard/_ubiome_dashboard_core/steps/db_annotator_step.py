import streamlit as st
from gws_core import InputTask, Scenario, ScenarioProxy, ScenarioStatus, Tag
from gws_core.streamlit import StreamlitAuthenticateUser, StreamlitResourceSelect
from gws_ubiome import Qiime2TableDbAnnotator
from gws_ubiome.ubiome_dashboard._ubiome_dashboard_core.functions_steps import (
    create_base_scenario_with_tags,
    display_saved_scenario_actions,
    display_scenario_parameters,
    render_scenario_table,
)
from gws_ubiome.ubiome_dashboard._ubiome_dashboard_core.state import State


@st.dialog("DB annotator parameters")
def dialog_db_annotator_params(ubiome_state: State):
    translate_service = ubiome_state.get_translate_service()
    st.text_input(translate_service.translate("taxa_composition_scenario_name"), placeholder=translate_service.translate("enter_taxa_composition_name"), value=f"{ubiome_state.get_current_analysis_name()} - Taxa Composition", key=ubiome_state.DB_ANNOTATOR_SCENARIO_NAME_INPUT_KEY)

    # Display available annotation tables for user selection
    st.markdown(f"##### {translate_service.translate('select_annotation_table')}")
    # Use StreamlitResourceSelect to let user choose an annotation table
    resource_select = StreamlitResourceSelect()
    # Filter to show only File resources with tsv extension
    resource_select.filters['resourceTypingNames'] = ['RESOURCE.gws_core.File']
    resource_select.select_resource(
        placeholder=translate_service.translate('select_annotation_table_placeholder'), key=ubiome_state.SELECTED_ANNOTATION_TABLE_KEY, defaut_resource=None)

    # Add both Save and Run buttons
    col1, col2 = st.columns(2)

    with col1:
        save_clicked = st.button(translate_service.translate("save_taxa_composition"), width="stretch", icon=":material/save:", key="button_db_annotator_save")

    with col2:
        run_clicked = st.button(translate_service.translate("run_taxa_composition"), width="stretch", icon=":material/play_arrow:", key="button_db_annotator_run")

    if save_clicked or run_clicked:
        selected_annotation_table_id = ubiome_state.get_selected_annotation_table()["resourceId"]
        if not selected_annotation_table_id:
            st.warning(translate_service.translate("select_annotation_table_required"))
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

            # Only add to queue if Run was clicked
            if run_clicked:
                scenario.add_to_queue()
                ubiome_state.reset_tree_analysis()
                ubiome_state.set_tree_default_item(scenario.get_model_id())
            st.rerun()

def render_db_annotator_step(selected_scenario: Scenario, ubiome_state: State) -> None:
    translate_service = ubiome_state.get_translate_service()

    # Get the selected tree menu item to determine which taxonomy scenario is selected
    tree_menu = ubiome_state.get_tree_menu_object()
    selected_item = tree_menu.get_selected_item()
    if selected_item.key.startswith(ubiome_state.TAG_DB_ANNOTATOR):
        taxonomy_scenario_parent_id = ubiome_state.get_parent_taxonomy_scenario_from_step()
        ubiome_state.set_current_taxonomy_scenario_id_parent(taxonomy_scenario_parent_id.id)
        # Retrieve the feature inference scenario ID using the utility function
        feature_inference_id = ubiome_state.get_feature_inference_id_from_taxonomy_scenario(taxonomy_scenario_parent_id)
        ubiome_state.set_current_feature_scenario_id_parent(feature_inference_id)

    if not selected_scenario:
        if not ubiome_state.get_is_standalone():
            # On click, open a dialog to allow the user to select params of Taxa Composition
            st.button(translate_service.translate("configure_new_taxa_composition_scenario"), icon=":material/edit:", width="content",
                            on_click=lambda state=ubiome_state: dialog_db_annotator_params(state))

        # Display table of existing Taxa Composition scenarios
        st.markdown(f"### {translate_service.translate('list_scenarios')}")

        list_scenario_db_annotator = ubiome_state.get_scenario_step_db_annotator()
        render_scenario_table(list_scenario_db_annotator, 'db_annotator_process', 'db_annotator_grid', ubiome_state)

    else:
        # Display details about scenario DB annotator
        st.markdown(f"##### {translate_service.translate('taxa_composition_scenario_results')}")
        display_scenario_parameters(selected_scenario, 'db_annotator_process', ubiome_state)

        if selected_scenario.status == ScenarioStatus.DRAFT and not ubiome_state.get_is_standalone():
            display_saved_scenario_actions(selected_scenario, ubiome_state)

        if selected_scenario.status != ScenarioStatus.SUCCESS:
            return

        # Display results if scenario is successful
        scenario_proxy = ScenarioProxy.from_existing_scenario(selected_scenario.id)
        protocol_proxy = scenario_proxy.get_protocol()

        tab_relative, tab_absolute = st.tabs([translate_service.translate("relative_abundance"), translate_service.translate("absolute_count")])

        with tab_relative:
            # Display relative abundance table and plot
            st.markdown(f"##### {translate_service.translate('relative_abundance_table')}")
            relative_table_output = protocol_proxy.get_process('db_annotator_process').get_output('relative_abundance_table')
            if relative_table_output:
                st.dataframe(relative_table_output.get_data())

            st.markdown(f"##### {translate_service.translate('relative_abundance_plot')}")
            relative_plot_output = protocol_proxy.get_process('db_annotator_process').get_output('relative_abundance_plotly_resource')
            if relative_plot_output:
                st.plotly_chart(relative_plot_output.get_figure())

        with tab_absolute:
            # Display absolute count table and plot
            st.markdown(f"##### {translate_service.translate('absolute_count_table')}")
            absolute_table_output = protocol_proxy.get_process('db_annotator_process').get_output('absolute_abundance_table')
            if absolute_table_output:
                st.dataframe(absolute_table_output.get_data())
