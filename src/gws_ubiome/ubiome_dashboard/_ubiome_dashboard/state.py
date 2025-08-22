
import streamlit as st

from gws_core.tag.tag_entity_type import TagEntityType
from gws_core.tag.entity_tag_list import EntityTagList

from gws_core import Scenario

class State:
    """Class to manage the state of the app.
    """

    TAG_BRICK = "brick"
    TAG_UBIOME = "ubiome"
    TAG_METADATA = "metadata"
    TAG_QC = "quality_control"
    TAG_FEATURE_INFERENCE = "feature_inference"
    TAG_FASTQ = "fastq_name"
    TAG_ANALYSIS_NAME = "analysis_name"
    TAG_UBIOME_PIPELINE_ID = "ubiome_pipeline_id"
    SELECTED_SCENARIO_KEY = "selected_scenario"
    SELECTED_ANALYSIS_KEY = "selected_analysis"
    STEP_PIPELINE_KEY = "step_pipeline"
    SELECTED_FOLDER_ID_KEY = "selected_folder_id"
    RESOURCE_ID_FASTQ_KEY = "resource_id_fastq"
    RESOURCE_ID_METADATA_TABLE_KEY = "resource_id_metadata_table"
    TAG_METADATA_UPDATED = "metadata_table_updated"
    TREE_ANALYSIS_KEY = "analysis_tree_menu"

    @classmethod
    def reset_tree_analysis(cls) -> None:
        """Reset the analysis tree state in session."""
        if cls.TREE_ANALYSIS_KEY in st.session_state:
            del st.session_state[cls.TREE_ANALYSIS_KEY]


    @classmethod
    def set_selected_scenario(cls, scenario: Scenario):
        st.session_state[cls.SELECTED_SCENARIO_KEY] = scenario

    @classmethod
    def get_selected_scenario(cls) -> Scenario:
        return st.session_state.get(cls.SELECTED_SCENARIO_KEY)

    @classmethod
    # It's the metadata scenario
    def set_selected_analysis(cls, scenario: Scenario):
        st.session_state[cls.SELECTED_ANALYSIS_KEY] = scenario

    @classmethod
    def get_selected_analysis(cls) -> Scenario:
        return st.session_state.get(cls.SELECTED_ANALYSIS_KEY)

    # Infos of the metadata scenario

    @classmethod
    def get_current_tag_value_by_key(cls, key: str) -> str:
        metadata_scenario : Scenario = cls.get_selected_analysis()
        entity_tag_list = EntityTagList.find_by_entity(TagEntityType.SCENARIO, metadata_scenario.id)
        tag = entity_tag_list.get_tags_by_key(key)[0].to_simple_tag()
        return tag.value

    @classmethod
    def get_current_ubiome_pipeline_id(cls) -> str:
        return cls.get_current_tag_value_by_key(cls.TAG_UBIOME_PIPELINE_ID)

    @classmethod
    def get_current_analysis_name(cls) -> str:
        return cls.get_current_tag_value_by_key(cls.TAG_ANALYSIS_NAME)

    @classmethod
    def get_current_fastq_name(cls) -> str:
        return cls.get_current_tag_value_by_key(cls.TAG_FASTQ)

    @classmethod
    def get_resource_id_fastq(cls) -> str:
        return st.session_state.get(cls.RESOURCE_ID_FASTQ_KEY)

    @classmethod
    def set_resource_id_fastq(cls, resource_id: str):
        st.session_state[cls.RESOURCE_ID_FASTQ_KEY] = resource_id

    @classmethod
    def get_resource_id_metadata_table(cls) -> str:
        return st.session_state.get(cls.RESOURCE_ID_METADATA_TABLE_KEY)

    @classmethod
    def set_resource_id_metadata_table(cls, resource_id: str):
        st.session_state[cls.RESOURCE_ID_METADATA_TABLE_KEY] = resource_id

    @classmethod
    def set_step_pipeline(cls, step_name: str):
        st.session_state[cls.STEP_PIPELINE_KEY] = step_name

    @classmethod
    def get_step_pipeline(cls) -> str:
        return st.session_state.get(cls.STEP_PIPELINE_KEY)

    @classmethod
    def set_selected_folder_id(cls, folder_id: str):
        st.session_state[cls.SELECTED_FOLDER_ID_KEY] = folder_id

    @classmethod
    def get_selected_folder_id(cls) -> str:
        return st.session_state.get(cls.SELECTED_FOLDER_ID_KEY)
