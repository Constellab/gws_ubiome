import streamlit as st
from state import State
from gws_core.streamlit import StreamlitContainers, StreamlitResourceSelect, StreamlitRouter
from gws_ubiome.ubiome_dashboard._ubiome_dashboard.ubiome_config import UbiomeConfig
from gws_ubiome.ubiome_dashboard._ubiome_dashboard.functions_home import navigate_to_first_page
import pandas as pd
from gws_core import Tag, InputTask, ProcessProxy, ScenarioSearchBuilder, TagValueModel, Scenario, ScenarioStatus, ScenarioProxy, ProtocolProxy, ScenarioCreationType
from gws_ubiome import Qiime2MetadataTableMaker

def render_new_analysis_page():
    # Add a return button
    ubiome_config = UbiomeConfig.get_instance()
    router = StreamlitRouter.load_from_session()
    ubiome_state = State()

    if st.button("Return Home", icon=":material/arrow_back:", use_container_width=False):
        router.navigate("first-page")



    with st.form(clear_on_submit=False, enter_to_submit=True, key="new_analysis_form"):
        st.write("New Analysis")
        # select fastq data
        resource_select = StreamlitResourceSelect()
        selected_fastq = resource_select.select_resource(
            placeholder='Search for fastq resource', key="resource-selector", defaut_resource=None)

        # Select if data is paired-end or single-end
        sequencing_type = st.radio("Select if data is paired-end or single-end", ("Paired-end", "Single-end"))

        analysis_name = st.text_input("Insert your analysis name")

        folder_to_associate_with = st.text_input("Insert folder to associate with")# TODO avoir la liste des folders du lab

        submit_button = st.form_submit_button(
            label="Run"
        )

        if submit_button:
            # Create a new scenario in the lab
            scenario: ScenarioProxy = ScenarioProxy(
                None, title=f"{analysis_name} - Metadata",
                creation_type=ScenarioCreationType.MANUAL)
            protocol: ProtocolProxy = scenario.get_protocol()

            fastq_resource = protocol.add_process(
                InputTask, 'selected_fastq',
                {InputTask.config_name: selected_fastq.get_resource().get_model_id()})

            name_fastq = selected_fastq.get_resource().get_name()

            # TODO : remove when maj of gws_core
            # We parse value to ensure it is a valid tag format because auto parse is not longer availaible
            # for values in lab
            name_fastq_parsed = Tag.parse_tag(name_fastq)
            analysis_name_parsed = Tag.parse_tag(analysis_name)

            # Add tags to the scenario
            scenario.add_tag(Tag(ubiome_state.TAG_FASTQ, name_fastq_parsed, is_propagable=True, auto_parse=True))
            scenario.add_tag(Tag(ubiome_state.TAG_BRICK, ubiome_state.TAG_UBIOME, is_propagable=True, auto_parse=True))
            scenario.add_tag(Tag(ubiome_state.TAG_UBIOME, ubiome_state.TAG_METADATA, is_propagable=True))
            scenario.add_tag(Tag(ubiome_state.TAG_ANALYSIS_NAME, analysis_name_parsed, is_propagable=True, auto_parse=True))

            # Step 1 : Metadata task
            metadata_process : ProcessProxy = protocol.add_process(Qiime2MetadataTableMaker, 'metadata_process') # TODO : add config params
            protocol.add_connector(out_port=fastq_resource >> 'resource',
                                       in_port=metadata_process << "fastq_folder")
            # Add output
            protocol.add_output('metadata_process_output', metadata_process >> 'metadata_table', flag_resource=False)
            scenario.add_to_queue()


            router.navigate("first-page")
            st.rerun()