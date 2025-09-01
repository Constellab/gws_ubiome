import os
import streamlit as st
import pandas as pd
from state import State
from gws_core.streamlit import StreamlitAuthenticateUser, StreamlitTaskRunner
from gws_core import FrontService, FsNodeExtractor, Scenario, ScenarioProxy, Tag, InputTask, Scenario, ScenarioStatus, ScenarioProxy
from gws_ubiome import Picrust2FunctionalAnalysis
from gws_ubiome.ubiome_dashboard._ubiome_dashboard.functions_steps import create_base_scenario_with_tags, render_scenario_table, display_scenario_parameters

@st.dialog("16S parameters")
def dialog_16s_params(ubiome_state: State):
    st.text_input("16S Functional Analysis scenario name:", placeholder="Enter 16S functional analysis scenario name", value=f"{ubiome_state.get_current_analysis_name()} - 16S Functional Analysis", key=ubiome_state.FUNCTIONAL_ANALYSIS_SCENARIO_NAME_INPUT_KEY)
    form_config = StreamlitTaskRunner(Picrust2FunctionalAnalysis)
    form_config.generate_config_form_without_run(
        session_state_key=ubiome_state.FUNCTIONAL_ANALYSIS_CONFIG_KEY,
        default_config_values=Picrust2FunctionalAnalysis.config_specs.get_default_values(),
        is_default_config_valid=Picrust2FunctionalAnalysis.config_specs.mandatory_values_are_set(
            Picrust2FunctionalAnalysis.config_specs.get_default_values()))

    if st.button("Run 16S Functional Analysis", use_container_width=True, icon=":material/play_arrow:", key="button_16s"):
        if not ubiome_state.get_functional_analysis_config()["is_valid"]:
            st.warning("Please fill all the mandatory fields.")
            return

        with StreamlitAuthenticateUser():
            scenario = create_base_scenario_with_tags(ubiome_state, ubiome_state.TAG_16S, ubiome_state.get_scenario_user_name(ubiome_state.FUNCTIONAL_ANALYSIS_SCENARIO_NAME_INPUT_KEY))
            feature_scenario_id = ubiome_state.get_current_feature_scenario_id_parent()
            scenario.add_tag(Tag(ubiome_state.TAG_FEATURE_INFERENCE_ID, feature_scenario_id, is_propagable=False, auto_parse=True))
            scenario.add_tag(Tag(ubiome_state.TAG_16S_ID, scenario.get_model_id(), is_propagable=False, auto_parse=True))
            protocol = scenario.get_protocol()

            # Retrieve feature inference outputs and extract table.qza and asv
            scenario_proxy_fi = ScenarioProxy.from_existing_scenario(feature_scenario_id)
            protocol_proxy_fi = scenario_proxy_fi.get_protocol()
            feature_output = protocol_proxy_fi.get_process('feature_process').get_output('result_folder')

            # Get the table.qza and ASV-sequences.fasta from feature inference output
            feature_resource = protocol.add_process(InputTask, 'feature_resource', {InputTask.config_name: feature_output.get_model_id()})
            fs_node_extractor_table = protocol.add_process(FsNodeExtractor, 'fs_node_extractor_table', {"fs_node_path": "table.qza"})
            fs_node_extractor_asv = protocol.add_process(FsNodeExtractor, 'fs_node_extractor_asv', {"fs_node_path": "ASV-sequences.fasta"})
            # Add connectors
            protocol.add_connector(out_port=feature_resource >> 'resource', in_port=fs_node_extractor_table << "source")
            protocol.add_connector(out_port=feature_resource >> 'resource', in_port=fs_node_extractor_asv << "source")
            # Add 16S functional analysis process
            functional_analysis_process = protocol.add_process(Picrust2FunctionalAnalysis, 'functional_analysis_process',
                                                             config_params=ubiome_state.get_functional_analysis_config()["config"])

            # The task expects table.qza for ASV_count_abundance and ASV-sequences.fasta for FASTA_of_asv
            protocol.add_connector(out_port=fs_node_extractor_table >> "target", in_port=functional_analysis_process << 'ASV_count_abundance')
            protocol.add_connector(out_port=fs_node_extractor_asv >> "target", in_port=functional_analysis_process << 'FASTA_of_asv')

            # Add outputs
            protocol.add_output('functional_analysis_result_output', functional_analysis_process >> 'Folder_result', flag_resource=False)

            ubiome_state.reset_tree_analysis()
            ubiome_state.set_tree_default_item(scenario.get_model_id())
            st.rerun()

def render_16s_step(selected_scenario: Scenario, ubiome_state: State) -> None:
    # Get the selected tree menu item to determine which feature inference scenario is selected
    tree_menu = ubiome_state.get_tree_menu_object()
    selected_item = tree_menu.get_selected_item()
    if selected_item.key.startswith(ubiome_state.TAG_16S):
        feature_scenario_parent_id = ubiome_state.get_parent_feature_inference_scenario_from_step()
        # save in session state
        ubiome_state.set_current_feature_scenario_id_parent(feature_scenario_parent_id)

    if not selected_scenario:
        # On click, open a dialog to allow the user to select params of 16S functional analysis
        st.button("Run new 16S Functional Analysis", icon=":material/play_arrow:", use_container_width=False,
                    on_click=lambda state=ubiome_state: dialog_16s_params(state))

        # Display table of existing 16S Functional Analysis scenarios
        st.markdown("### Previous 16S Functional Analysis")

        list_scenario_16s = ubiome_state.get_scenario_step_16s()
        render_scenario_table(list_scenario_16s, 'functional_analysis_process', '16s_functional_grid', ubiome_state)
    else:
        # Display details about scenario 16S functional analysis
        st.markdown("##### 16S Functional Analysis Scenario Results")
        display_scenario_parameters(selected_scenario, 'functional_analysis_process')

        st.success("The scenario has been successfully created. Here is the link:")
        st.write(FrontService.get_scenario_url(selected_scenario.id))

        if selected_scenario.status != ScenarioStatus.SUCCESS:
            return

        # Display results if scenario is successful
        scenario_proxy = ScenarioProxy.from_existing_scenario(selected_scenario.id)
        protocol_proxy = scenario_proxy.get_protocol()

        # Get functional analysis results folder
        functional_result_folder = protocol_proxy.get_process('functional_analysis_process').get_output('Folder_result')

        if functional_result_folder:
            st.markdown("##### PICRUSt2 Functional Analysis Results")

            # Display folder contents
            st.markdown("##### Result Folder Contents")
            folder_path = functional_result_folder.path

            if os.path.exists(folder_path):
                # List key output folders
                key_folders = ['EC_metagenome_out', 'KO_metagenome_out', 'pathways_out']

                tabs = st.tabs(["EC Metagenome", "KO Metagenome", "Pathways"])

                for i, (tab, folder_name) in enumerate(zip(tabs, key_folders)):
                    with tab:
                        folder_full_path = os.path.join(folder_path, folder_name)
                        if os.path.exists(folder_full_path):
                            st.write(f"#### {folder_name.replace('_', ' ').title()}")

                            # List files in the folder
                            try:
                                files_in_folder = os.listdir(folder_full_path)
                                if files_in_folder:
                                    st.write("**Available files:**")
                                    for file_name in files_in_folder:
                                        file_path = os.path.join(folder_full_path, file_name)
                                        if os.path.isfile(file_path):
                                            file_size = os.path.getsize(file_path)
                                            st.write(f"- {file_name} ({file_size} bytes)")

                                            # For TSV files, offer to display them
                                            if file_name.endswith(('.tsv', '.tsv.gz')):
                                                if st.button(f"View {file_name}", key=f"view_{folder_name}_{file_name}"):
                                                    try:
                                                        if file_name.endswith('.gz'):
                                                            import gzip
                                                            with gzip.open(file_path, 'rt') as f:
                                                                content = f.read()
                                                        else:
                                                            with open(file_path, 'r') as f:
                                                                content = f.read()

                                                        # Display as dataframe if it's TSV
                                                        import io
                                                        df = pd.read_csv(io.StringIO(content), sep='\t')
                                                        st.dataframe(df.head(100))  # Show first 100 rows
                                                    except Exception as e:
                                                        st.error(f"Error reading file: {str(e)}")
                                else:
                                    st.info(f"No files found in {folder_name}")
                            except Exception as e:
                                st.error(f"Error accessing folder {folder_name}: {str(e)}")
                        else:
                            st.warning(f"Folder {folder_name} not found in results")
            else:
                st.error("Result folder not found")