import os
import streamlit as st
from state import State
from gws_core.streamlit import StreamlitAuthenticateUser, StreamlitTaskRunner
from gws_core import FsNodeExtractor, ResourceModel, Scenario, ScenarioProxy, TableImporter, Tag, InputTask, Scenario, ScenarioStatus, ScenarioProxy
from gws_ubiome import Ggpicrust2FunctionalAnalysis
from gws_ubiome.ubiome_dashboard._ubiome_dashboard.functions_steps import create_base_scenario_with_tags, render_scenario_table

@st.dialog("16S Visualization parameters")
def dialog_16s_visu_params(ubiome_state: State):
    st.text_input("16S Visualization scenario name:", placeholder="Enter 16S visualization scenario name", value=f"{ubiome_state.get_current_analysis_name()} - 16S Visualization", key=ubiome_state.FUNCTIONAL_ANALYSIS_VISU_SCENARIO_NAME_INPUT_KEY)
    # Show metadata file preview
    metadata_table = ResourceModel.get_by_id(ubiome_state.get_resource_id_metadata_table())
    metadata_file = metadata_table.get_resource()

    table_metadata = TableImporter.call(metadata_file)
    df_metadata = table_metadata.get_data()

    st.markdown("##### Metadata File Preview")
    if metadata_table:
        # Display only column names and first 3 rows
        st.dataframe(df_metadata.head(3))

    form_config = StreamlitTaskRunner(Ggpicrust2FunctionalAnalysis)
    default_config = Ggpicrust2FunctionalAnalysis.config_specs.get_default_values()
    default_config["Round_digit"] = True
    form_config.generate_config_form_without_run(
        session_state_key=ubiome_state.FUNCTIONAL_ANALYSIS_VISU_CONFIG_KEY,
        default_config_values=default_config,
        is_default_config_valid=Ggpicrust2FunctionalAnalysis.config_specs.mandatory_values_are_set(
            default_config)
    )

    if st.button("Run 16S Visualization", use_container_width=True, icon=":material/play_arrow:", key="button_16s_visu"):
        if not ubiome_state.get_functional_analysis_visu_config()["is_valid"]:
            st.warning("Please fill all the mandatory fields.")
            return

        with StreamlitAuthenticateUser():
            scenario = create_base_scenario_with_tags(ubiome_state, ubiome_state.TAG_16S_VISU, ubiome_state.get_scenario_user_name(ubiome_state.FUNCTIONAL_ANALYSIS_VISU_SCENARIO_NAME_INPUT_KEY))
            feature_scenario_id = ubiome_state.get_current_feature_scenario_id_parent()
            functional_scenario_id = ubiome_state.get_current_16s_scenario_id_parent()
            scenario.add_tag(Tag(ubiome_state.TAG_FEATURE_INFERENCE_ID, feature_scenario_id, is_propagable=False, auto_parse=True))
            scenario.add_tag(Tag(ubiome_state.TAG_16S_ID, functional_scenario_id, is_propagable=False, auto_parse=True))
            protocol = scenario.get_protocol()

            # Add 16S visualization process
            visu_process = protocol.add_process(Ggpicrust2FunctionalAnalysis, 'functional_visu_process',
                                              config_params=ubiome_state.get_functional_analysis_visu_config()["config"])

            # Get the 16S functional analysis results folder
            scenario_proxy_16s = ScenarioProxy.from_existing_scenario(functional_scenario_id)
            protocol_proxy_16s = scenario_proxy_16s.get_protocol()
            functional_result_folder = protocol_proxy_16s.get_process('functional_analysis_process').get_output('Folder_result')

            # Extract the KO metagenome file from the results folder
            functional_folder_resource = protocol.add_process(InputTask, 'functional_folder_resource',
                                                             {InputTask.config_name: functional_result_folder.get_model_id()})

            # Extract the pred_metagenome_unstrat.tsv.gz file from KO_metagenome_out folder
            ko_file_extractor = protocol.add_process(FsNodeExtractor, 'ko_file_extractor',
                                                    {"fs_node_path": "KO_metagenome_out/pred_metagenome_unstrat.tsv.gz"})

            # Add metadata file resource
            metadata_file_resource = protocol.add_process(InputTask, 'metadata_file_resource',
                                                        {InputTask.config_name: ubiome_state.get_resource_id_metadata_table()})

            # Connect inputs
            protocol.add_connector(out_port=functional_folder_resource >> 'resource',
                                 in_port=ko_file_extractor << 'source')
            protocol.add_connector(out_port=ko_file_extractor >> 'target',
                                 in_port=visu_process << 'ko_abundance_file')
            protocol.add_connector(out_port=metadata_file_resource >> 'resource',
                                 in_port=visu_process << 'metadata_file')

            # Add outputs
            protocol.add_output('visu_resource_set_output', visu_process >> 'resource_set', flag_resource=False)
            protocol.add_output('visu_plotly_output', visu_process >> 'plotly_result', flag_resource=False)

            scenario.add_to_queue()
            ubiome_state.reset_tree_analysis()
            ubiome_state.set_tree_default_item(scenario.get_model_id())
            st.rerun()

def render_16s_visu_step(selected_scenario: Scenario, ubiome_state: State) -> None:
    # Get the selected tree menu item to determine which 16s scenario is selected
    tree_menu = ubiome_state.get_tree_menu_object()
    selected_item = tree_menu.get_selected_item()
    if selected_item.key.startswith(ubiome_state.TAG_16S_VISU):
        functional_scenario_parent_id = ubiome_state.get_parent_16s_scenario_from_step()
        ubiome_state.set_current_16s_scenario_id_parent(functional_scenario_parent_id)
        # Retrieve the feature inference scenario ID
        feature_inference_id = ubiome_state.get_feature_inference_id_from_16s_scenario(functional_scenario_parent_id)
        ubiome_state.set_current_feature_scenario_id_parent(feature_inference_id)

    if not selected_scenario:
        # Check if we have a valid 16S functional analysis scenario to run visualization
        functional_scenario_id = ubiome_state.get_current_16s_scenario_id_parent()

        # Validate that the required KO metagenome file exists
        ko_file_available = False
        if functional_scenario_id:
            try:
                scenario_proxy_16s = ScenarioProxy.from_existing_scenario(functional_scenario_id)
                protocol_proxy_16s = scenario_proxy_16s.get_protocol()
                functional_result_folder = protocol_proxy_16s.get_process('functional_analysis_process').get_output('Folder_result')

                if functional_result_folder and os.path.exists(functional_result_folder.path):
                    ko_file_path = os.path.join(functional_result_folder.path, "KO_metagenome_out", "pred_metagenome_unstrat.tsv.gz")
                    ko_file_available = os.path.exists(ko_file_path)
            except Exception:
                ko_file_available = False

        if not ko_file_available:
            st.warning("⚠️ **Cannot run 16S Visualization**: The required file `KO_metagenome_out/pred_metagenome_unstrat.tsv.gz` is not available from the 16S Functional Analysis results.")
        else:
            # On click, open a dialog to allow the user to select params of 16S visualization
            st.button("Run new 16S Visualization", icon=":material/play_arrow:", use_container_width=False,
                        on_click=lambda state=ubiome_state: dialog_16s_visu_params(state))

        # Display table of existing 16S Visualization scenarios
        st.markdown("### Previous 16S Visualizations")

        list_scenario_16s_visu = ubiome_state.get_scenario_step_16s_visu()
        render_scenario_table(list_scenario_16s_visu, 'functional_visu_process', '16s_visu_grid', ubiome_state)
    else:
        # Display details about scenario 16S visualization
        st.markdown("##### 16S Visualization Scenario Results")
        display_scenario_parameters(selected_scenario, 'functional_visu_process')

        if selected_scenario.status != ScenarioStatus.SUCCESS:
            return

        # Display results if scenario is successful
        scenario_proxy = ScenarioProxy.from_existing_scenario(selected_scenario.id)
        protocol_proxy = scenario_proxy.get_protocol()

        tab_pca, tab_results = st.tabs(["PCA Plot", "Analysis Results"])

        with tab_pca:
            # Display PCA plot
            st.markdown("##### Principal Component Analysis")
            plotly_result = protocol_proxy.get_process('functional_visu_process').get_output('plotly_result')
            if plotly_result:
                st.plotly_chart(plotly_result.get_figure())

        with tab_results:
            # Display resource set results
            st.markdown("##### Differential Abundance Analysis Results")
            resource_set_output = protocol_proxy.get_process('functional_visu_process').get_output('resource_set')

            if resource_set_output:
                resource_dict = resource_set_output.get_resources()

                # Separate different types of results
                error_bar_plots = {}
                heatmap_plots = {}
                analysis_tables = {}

                for key, resource in resource_dict.items():
                    if "pathway_errorbar" in key and key.endswith(".png"):
                        error_bar_plots[key] = resource
                    elif "pathway_heatmap" in key and key.endswith(".png"):
                        heatmap_plots[key] = resource
                    elif "daa_annotated_results" in key and key.endswith(".csv"):
                        analysis_tables[key] = resource

                # Create sub-tabs for different result types
                if error_bar_plots or heatmap_plots or analysis_tables:
                    sub_tabs = []
                    if analysis_tables:
                        sub_tabs.append("Analysis Tables")
                    if error_bar_plots:
                        sub_tabs.append("Error Bar Plots")
                    if heatmap_plots:
                        sub_tabs.append("Heatmap Plots")

                    if len(sub_tabs) > 1:
                        tab_tables, *other_tabs = st.tabs(sub_tabs)
                    else:
                        tab_tables = st.container()
                        other_tabs = []

                    # Analysis Tables
                    if analysis_tables:
                        with tab_tables if len(sub_tabs) > 1 else st.container():
                            st.markdown("##### Differential Abundance Analysis Tables")
                            selected_table = st.selectbox("Select analysis table:",
                                                            options=list(analysis_tables.keys()),
                                                            key="analysis_table_select")
                            if selected_table:
                                st.dataframe(analysis_tables[selected_table].get_data())

                    # Error Bar Plots
                    if error_bar_plots and other_tabs:
                        with other_tabs[0]:
                            st.markdown("##### Pathway Error Bar Plots")
                            selected_errorbar = st.selectbox("Select error bar plot:",
                                                            options=list(error_bar_plots.keys()),
                                                            key="errorbar_select")
                            if selected_errorbar:
                                try:
                                    st.image(error_bar_plots[selected_errorbar].path)
                                except Exception as e:
                                    st.error(f"Error displaying image: {str(e)}")

                    # Heatmap Plots
                    if heatmap_plots and len(other_tabs) > 1:
                        with other_tabs[1]:
                            st.markdown("##### Pathway Heatmap Plots")
                            selected_heatmap = st.selectbox("Select heatmap plot:",
                                                            options=list(heatmap_plots.keys()),
                                                            key="heatmap_select")
                            if selected_heatmap:
                                try:
                                    st.image(heatmap_plots[selected_heatmap].path)
                                except Exception as e:
                                    st.error(f"Error displaying image: {str(e)}")
                else:
                    st.info("No visualization results available.")
            else:
                st.info("No analysis results available.")