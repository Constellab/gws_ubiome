import streamlit as st
import plotly.express as px
from gws_ubiome.ubiome_dashboard._ubiome_dashboard_core.state import State
from gws_core.streamlit import StreamlitAuthenticateUser, StreamlitTaskRunner
from gws_core import ResourceModel, Scenario, ScenarioProxy, TableImporter, Tag, InputTask, Scenario, ScenarioStatus, ScenarioProxy
from gws_ubiome import Qiime2DifferentialAnalysis
from gws_ubiome.ubiome_dashboard._ubiome_dashboard_core.functions_steps import create_base_scenario_with_tags, render_scenario_table, display_scenario_parameters

@st.dialog("ANCOM parameters")
def dialog_ancom_params(ubiome_state: State):
    st.text_input("ANCOM scenario name:", placeholder="Enter ANCOM scenario name", value=f"{ubiome_state.get_current_analysis_name()} - ANCOM", key=ubiome_state.ANCOM_SCENARIO_NAME_INPUT_KEY)

    # Show header of metadata file
    metadata_table = ResourceModel.get_by_id(ubiome_state.get_resource_id_metadata_table())
    metadata_file = metadata_table.get_resource()

    table_metadata = TableImporter.call(metadata_file)
    df_metadata = table_metadata.get_data()

    st.markdown("##### Reminder metadata columns:")
    if metadata_table:
        # Display only column names
        st.write(', '.join(df_metadata.columns.tolist()))

    form_config = StreamlitTaskRunner(Qiime2DifferentialAnalysis)
    form_config.generate_config_form_without_run(
        session_state_key=ubiome_state.ANCOM_CONFIG_KEY,
        default_config_values=Qiime2DifferentialAnalysis.config_specs.get_default_values(),
        is_default_config_valid=Qiime2DifferentialAnalysis.config_specs.mandatory_values_are_set(
            Qiime2DifferentialAnalysis.config_specs.get_default_values())
    )

    if st.button("Run ANCOM", use_container_width=True, icon=":material/play_arrow:", key="button_ancom"):
        if not ubiome_state.get_ancom_config()["is_valid"]:
            st.warning("Please fill all the mandatory fields.")
            return

        with StreamlitAuthenticateUser():
            scenario = create_base_scenario_with_tags(ubiome_state, ubiome_state.TAG_ANCOM, ubiome_state.get_scenario_user_name(ubiome_state.ANCOM_SCENARIO_NAME_INPUT_KEY))
            taxonomy_scenario_id = ubiome_state.get_current_taxonomy_scenario_id_parent()
            feature_scenario_id = ubiome_state.get_current_feature_scenario_id_parent()
            scenario.add_tag(Tag(ubiome_state.TAG_FEATURE_INFERENCE_ID, feature_scenario_id, is_propagable=False, auto_parse=True))
            scenario.add_tag(Tag(ubiome_state.TAG_TAXONOMY_ID, taxonomy_scenario_id, is_propagable=False, auto_parse=True))
            protocol = scenario.get_protocol()


            # Add ANCOM process
            ancom_process = protocol.add_process(Qiime2DifferentialAnalysis, 'ancom_process',
                                               config_params=ubiome_state.get_ancom_config()["config"])

            # Get the taxonomy diversity folder
            scenario_proxy_tax = ScenarioProxy.from_existing_scenario(taxonomy_scenario_id)
            protocol_proxy_tax = scenario_proxy_tax.get_protocol()
            taxonomy_folder_output = protocol_proxy_tax.get_process('taxonomy_process').get_output('result_folder')

            # Add input resources
            taxonomy_folder_resource = protocol.add_process(InputTask, 'taxonomy_folder_resource',
                                                          {InputTask.config_name: taxonomy_folder_output.get_model_id()})

            metadata_file_resource = protocol.add_process(InputTask, 'metadata_file_resource',
                                                        {InputTask.config_name: ubiome_state.get_resource_id_metadata_table()})

            # Connect inputs to ANCOM process
            protocol.add_connector(out_port=taxonomy_folder_resource >> 'resource',
                                 in_port=ancom_process << 'taxonomy_diversity_folder')
            protocol.add_connector(out_port=metadata_file_resource >> 'resource',
                                 in_port=ancom_process << 'metadata_file')

            # Add outputs
            protocol.add_output('ancom_result_tables_output', ancom_process >> 'result_tables', flag_resource=False)
            protocol.add_output('ancom_result_folder_output', ancom_process >> 'result_folder', flag_resource=False)

            scenario.add_to_queue()
            ubiome_state.reset_tree_analysis()
            ubiome_state.set_tree_default_item(scenario.get_model_id())
            st.rerun()

def render_ancom_step(selected_scenario: Scenario, ubiome_state: State) -> None:
    # Get the selected tree menu item to determine which taxonomy scenario is selected
    tree_menu = ubiome_state.get_tree_menu_object()
    selected_item = tree_menu.get_selected_item()
    if selected_item.key.startswith(ubiome_state.TAG_ANCOM):
        taxonomy_scenario_parent_id = ubiome_state.get_parent_taxonomy_scenario_from_step()
        ubiome_state.set_current_taxonomy_scenario_id_parent(taxonomy_scenario_parent_id.id)
        # Retrieve the feature inference scenario ID using the utility function
        feature_inference_id = ubiome_state.get_feature_inference_id_from_taxonomy_scenario(taxonomy_scenario_parent_id)
        ubiome_state.set_current_feature_scenario_id_parent(feature_inference_id)

    if not selected_scenario:
        if not ubiome_state.get_is_standalone():
            # On click, open a dialog to allow the user to select params of ANCOM
            st.button("Run new ANCOM", icon=":material/play_arrow:", use_container_width=False,
                            on_click=lambda state=ubiome_state: dialog_ancom_params(state))

        # Display table of existing ANCOM scenarios
        st.markdown("### Previous ANCOM Analyses")

        list_scenario_ancom = ubiome_state.get_scenario_step_ancom()
        render_scenario_table(list_scenario_ancom, 'ancom_process', 'ancom_grid', ubiome_state)

    else:
        # Display details about scenario ANCOM
        st.markdown("##### ANCOM Scenario Results")
        display_scenario_parameters(selected_scenario, 'ancom_process')
        if selected_scenario.status != ScenarioStatus.SUCCESS:
            return

        # Display results if scenario is successful
        scenario_proxy = ScenarioProxy.from_existing_scenario(selected_scenario.id)
        protocol_proxy = scenario_proxy.get_protocol()

        # Get ANCOM results
        ancom_result_tables = protocol_proxy.get_process('ancom_process').get_output('result_tables')

        if ancom_result_tables:
            resource_set_result_dict = ancom_result_tables.get_resources()

            # Separate different types of results
            ancom_stats = {}
            volcano_plots = {}
            percentile_abundances = {}

            for key, resource in resource_set_result_dict.items():
                if "ANCOM Stat" in key:
                    ancom_stats[key] = resource
                elif "Volcano plot" in key:
                    volcano_plots[key] = resource
                elif "Percentile abundances" in key:
                    percentile_abundances[key] = resource

            tab_stats, tab_volcano, tab_percentile = st.tabs(["ANCOM Statistics", "Volcano Plots", "Percentile Abundances"])

            with tab_stats:
                st.markdown("##### ANCOM Statistical Results")
                if ancom_stats:
                    selected_stat = st.selectbox("Select taxonomic level for ANCOM stats:",
                                                options=list(ancom_stats.keys()),
                                                key="ancom_stats_select")
                    if selected_stat:
                        ancom_data = ancom_stats[selected_stat].get_data()
                        # Convert boolean columns to string to avoid checkbox display
                        for col in ancom_data.columns:
                            if ancom_data[col].dtype == 'bool':
                                ancom_data[col] = ancom_data[col].astype(str)
                        st.dataframe(ancom_data)
                else:
                    st.info("No ANCOM statistics available.")

            with tab_volcano:
                st.markdown("##### Volcano Plot Data")
                if volcano_plots:
                    selected_volcano = st.selectbox("Select taxonomic level for volcano plot:",
                                                    options=list(volcano_plots.keys()),
                                                    key="volcano_plot_select")
                    if selected_volcano:
                        volcano_data = volcano_plots[selected_volcano].get_data()
                        # Convert boolean columns to string to avoid checkbox display
                        for col in volcano_data.columns:
                            if volcano_data[col].dtype == 'bool':
                                volcano_data[col] = volcano_data[col].astype(str)
                        st.dataframe(volcano_data)

                        # Create a simple volcano plot if data has the right columns
                        if 'W' in volcano_data.columns and 'clr_F-score' in volcano_data.columns:
                            fig = px.scatter(volcano_data, x='W', y='clr_F-score',
                                            title=f"Volcano Plot - {selected_volcano}",
                                            hover_data=volcano_data.columns.tolist())
                            fig.update_layout(
                                xaxis_title="W statistic",
                                yaxis_title="F-score"
                            )
                            st.plotly_chart(fig)
                else:
                    st.info("No volcano plot data available.")

            with tab_percentile:
                st.markdown("##### Percentile Abundances")
                if percentile_abundances:
                    selected_percentile = st.selectbox("Select taxonomic level for percentile abundances:",
                                                        options=list(percentile_abundances.keys()),
                                                        key="percentile_select")
                    if selected_percentile:
                        percentile_data = percentile_abundances[selected_percentile].get_data()
                        # Convert boolean columns to string to avoid checkbox display
                        for col in percentile_data.columns:
                            if percentile_data[col].dtype == 'bool':
                                percentile_data[col] = percentile_data[col].astype(str)
                        st.dataframe(percentile_data)
                else:
                    st.info("No percentile abundance data available.")