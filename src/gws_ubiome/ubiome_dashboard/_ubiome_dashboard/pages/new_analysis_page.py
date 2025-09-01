import streamlit as st
from state import State
from gws_core.streamlit import StreamlitResourceSelect, StreamlitRouter, StreamlitTaskRunner
from gws_core import ResourceModel, SpaceFolder, StringHelper, Tag, InputTask, SpaceService, ProcessProxy, ScenarioProxy, ProtocolProxy, ScenarioCreationType
from gws_ubiome import Qiime2MetadataTableMaker

def render_new_analysis_page(ubiome_state : State):
    # Add a return button
    router = StreamlitRouter.load_from_session()

    if st.button("Return Home", icon=":material/arrow_back:", use_container_width=False):
        router.navigate("first-page")


    with st.form(clear_on_submit=False, enter_to_submit=True, key="new_analysis_form"):
        st.markdown("## New Analysis")
        # select fastq data
        resource_select = StreamlitResourceSelect()
        resource_select.select_resource(
            placeholder='Search for fastq resource', key=ubiome_state.RESOURCE_SELECTOR_FASTQ_KEY, defaut_resource=None)

        form_config = StreamlitTaskRunner(Qiime2MetadataTableMaker)
        form_config.generate_config_form_without_run(
            session_state_key=ubiome_state.QIIME2_METADATA_CONFIG_KEY, default_config_values=Qiime2MetadataTableMaker.config_specs.get_default_values())

        cols = st.columns(2)
        with cols[0]:
            st.text_input("Insert your analysis name", key = ubiome_state.ANALYSIS_NAME_USER)

        with cols[1]:
            space_service = SpaceService.get_instance()
            list_folders_in_lab = space_service.get_all_lab_root_folders().folders
            folder_dict = {}
            for folder in list_folders_in_lab:
                # Create a dict of folder names and id
                folder_dict[folder.id] = folder.name

            # Give the user the possibility to choose in a list of folder names
            folder_to_associate_with = st.selectbox("Select folder to associate with", options=list(folder_dict.values()), index=None)
            # Save in session state the id of the folder
            ubiome_state.set_selected_folder_id(next((id for id, name in folder_dict.items() if name == folder_to_associate_with), None))

        submit_button = st.form_submit_button(
            label="Run"
        )

        if submit_button:
            list_required_fields_filled = []
            list_required_fields_filled.append(ubiome_state.check_if_required_is_filled(ubiome_state.get_resource_selector_fastq()))
            list_required_fields_filled.append(ubiome_state.check_if_required_is_filled(ubiome_state.get_analysis_name_user()))
            list_required_fields_filled.append(ubiome_state.get_qiime2_metadata_config()["is_valid"])
            if ubiome_state.get_associate_scenario_with_folder():
                list_required_fields_filled.append(ubiome_state.check_if_required_is_filled(ubiome_state.get_selected_folder_id()))
            # Check if mandatory fields have been filled
            if False in list_required_fields_filled:
                st.warning("Please fill all the mandatory fields.")
                return

            selected_fastq_id = ubiome_state.get_resource_selector_fastq()["resourceId"]
            selected_fastq = ResourceModel.get_by_id(selected_fastq_id)
            analysis_name = ubiome_state.get_analysis_name_user()
            # Create a new scenario in the lab
            folder : SpaceFolder = SpaceFolder.get_by_id(ubiome_state.get_selected_folder_id())
            scenario: ScenarioProxy = ScenarioProxy(
                None, folder=folder, title=f"{analysis_name} - Metadata",
                creation_type=ScenarioCreationType.MANUAL,
            )
            protocol: ProtocolProxy = scenario.get_protocol()

            fastq_resource = protocol.add_process(
                InputTask, 'selected_fastq',
                {InputTask.config_name: selected_fastq.get_resource().get_model_id()})

            name_fastq = selected_fastq.get_resource().get_name()

            # We parse value to ensure it is a valid tag format because auto parse is not longer availaible
            # for values in lab
            name_fastq_parsed = Tag.parse_tag(name_fastq)
            analysis_name_parsed = Tag.parse_tag(analysis_name)

            # Set sequencing_type as tag
            sequencing_type = ubiome_state.get_qiime2_metadata_config()["config"].get("sequencing_type")

            # Add tags to the scenario
            scenario.add_tag(Tag(ubiome_state.TAG_FASTQ, name_fastq_parsed, is_propagable=False, auto_parse=True))
            scenario.add_tag(Tag(ubiome_state.TAG_BRICK, ubiome_state.TAG_UBIOME, is_propagable=False, auto_parse=True))
            scenario.add_tag(Tag(ubiome_state.TAG_UBIOME, ubiome_state.TAG_METADATA, is_propagable=False))
            scenario.add_tag(Tag(ubiome_state.TAG_ANALYSIS_NAME, analysis_name_parsed, is_propagable=False, auto_parse=True))
            scenario.add_tag(Tag(ubiome_state.TAG_UBIOME_PIPELINE_ID, StringHelper.generate_uuid(), is_propagable=False, auto_parse=True))

            # Step 1 : Metadata task
            metadata_process : ProcessProxy = protocol.add_process(Qiime2MetadataTableMaker, 'metadata_process', config_params=ubiome_state.get_qiime2_metadata_config()["config"])
            protocol.add_connector(out_port=fastq_resource >> 'resource',
                                       in_port=metadata_process << "fastq_folder")
            # Add output
            protocol.add_output('metadata_process_output', metadata_process >> 'metadata_table', flag_resource=False)
            scenario.add_to_queue()


            router.navigate("first-page")
            st.rerun()