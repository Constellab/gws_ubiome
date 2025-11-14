import os
import streamlit as st
import pandas as pd
from gws_ubiome.ubiome_dashboard._ubiome_dashboard_core.state import State
from gws_core.streamlit import StreamlitAuthenticateUser, StreamlitTaskRunner
from gws_core import FrontService, FsNodeExtractor, Scenario, ScenarioProxy, Tag, InputTask, Scenario, ScenarioStatus, ScenarioProxy
from gws_ubiome import Picrust2FunctionalAnalysis
from gws_ubiome.ubiome_dashboard._ubiome_dashboard_core.functions_steps import create_base_scenario_with_tags, render_scenario_table, display_scenario_parameters

@st.dialog("16S parameters")
def dialog_16s_params(ubiome_state: State):
    translate_service = ubiome_state.get_translate_service()
    st.text_input(translate_service.translate("16s_functional_analysis_scenario_name"), placeholder=translate_service.translate("enter_16s_functional_analysis_name"), value=f"{ubiome_state.get_current_analysis_name()} - 16S Functional Analysis", key=ubiome_state.FUNCTIONAL_ANALYSIS_SCENARIO_NAME_INPUT_KEY)
    form_config = StreamlitTaskRunner(Picrust2FunctionalAnalysis)
    form_config.generate_config_form_without_run(
        session_state_key=ubiome_state.FUNCTIONAL_ANALYSIS_CONFIG_KEY,
        default_config_values=Picrust2FunctionalAnalysis.config_specs.get_default_values(),
        is_default_config_valid=Picrust2FunctionalAnalysis.config_specs.mandatory_values_are_set(
            Picrust2FunctionalAnalysis.config_specs.get_default_values()))

    if st.button(translate_service.translate("run_16s_functional_analysis"), width="stretch", icon=":material/play_arrow:", key="button_16s"):
        if not ubiome_state.get_functional_analysis_config()["is_valid"]:
            st.warning(translate_service.translate("fill_mandatory_fields"))
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
    translate_service = ubiome_state.get_translate_service()

    # Get the selected tree menu item to determine which feature inference scenario is selected
    tree_menu = ubiome_state.get_tree_menu_object()
    selected_item = tree_menu.get_selected_item()
    if selected_item.key.startswith(ubiome_state.TAG_16S):
        feature_scenario_parent_id = ubiome_state.get_parent_feature_inference_scenario_from_step()
        # save in session state
        ubiome_state.set_current_feature_scenario_id_parent(feature_scenario_parent_id.id)

    if not selected_scenario:
        if not ubiome_state.get_is_standalone():
            # On click, open a dialog to allow the user to select params of 16S functional analysis
            st.button(translate_service.translate("configure_new_16s_functional_analysis_scenario"), icon=":material/edit:", width="content",
                    on_click=lambda state=ubiome_state: dialog_16s_params(state))

        # Display table of existing 16S Functional Analysis scenarios
        st.markdown(f"### {translate_service.translate('list_scenarios')}")

        list_scenario_16s = ubiome_state.get_scenario_step_16s()
        render_scenario_table(list_scenario_16s, 'functional_analysis_process', '16s_functional_grid', ubiome_state)
    else:
        # Display details about scenario 16S functional analysis
        st.markdown(f"##### {translate_service.translate('16s_functional_analysis_scenario_results')}")
        display_scenario_parameters(selected_scenario, 'functional_analysis_process', ubiome_state)

        if ubiome_state.get_is_standalone():
            return

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
            st.markdown(f"##### {translate_service.translate('picrust2_functional_analysis_results')}")

            # Display folder contents
            st.markdown(f"##### {translate_service.translate('result_folder_contents')}")
            folder_path = functional_result_folder.path

            if os.path.exists(folder_path):
                # List key output folders
                key_folders = ['EC_metagenome_out', 'KO_metagenome_out', 'pathways_out']

                tabs = st.tabs([translate_service.translate("ec_metagenome"), translate_service.translate("ko_metagenome"), translate_service.translate("pathways")])

                for i, (tab, folder_name) in enumerate(zip(tabs, key_folders)):
                    with tab:
                        folder_full_path = os.path.join(folder_path, folder_name)
                        if os.path.exists(folder_full_path):
                            st.write(f"#### {folder_name.replace('_', ' ').title()}")

                            # List files in the folder
                            try:
                                files_in_folder = os.listdir(folder_full_path)
                                if files_in_folder:
                                    st.write(f"**{translate_service.translate('available_files')}**")
                                    for file_name in files_in_folder:
                                        file_path = os.path.join(folder_full_path, file_name)
                                        if os.path.isfile(file_path):
                                            file_size = os.path.getsize(file_path)
                                            st.write(f"- {file_name} ({file_size} bytes)")

                                            # For TSV files, offer to display them
                                            if file_name.endswith(('.tsv', '.tsv.gz')):
                                                if st.button(translate_service.translate("view_file").format(file_name), key=f"view_{folder_name}_{file_name}"):
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
                                                        st.error(translate_service.translate("error_reading_file").format(str(e)))
                                else:
                                    st.info(translate_service.translate("no_files_found").format(folder_name))
                            except Exception as e:
                                st.error(translate_service.translate("error_accessing_folder").format(folder_name, str(e)))
                        else:
                            st.warning(translate_service.translate("folder_not_found").format(folder_name))
            else:
                st.error(translate_service.translate("result_folder_not_found"))