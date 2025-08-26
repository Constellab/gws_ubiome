from typing import List, Dict
import streamlit as st

from gws_core.tag.tag_entity_type import TagEntityType
from gws_core.tag.entity_tag_list import EntityTagList

from gws_core import Scenario, ResourceModel

class State:
    """Class to manage the state of the app.
    """

    TAG_BRICK = "brick"
    TAG_UBIOME = "ubiome"
    TAG_SEQUENCING_TYPE = "sequencing_type"
    TAG_FASTQ = "fastq_name"
    TAG_ANALYSIS_NAME = "analysis_name"

    # step tags
    TAG_METADATA = "metadata"
    TAG_QC = "quality_control"
    TAG_FEATURE_INFERENCE = "feature_inference"
    TAG_RAREFACTION = "rarefaction"
    TAG_TAXONOMY = "taxonomy"
    TAG_PCOA_DIVERSITY = "pcoa_diversity"
    TAG_ANCOM = "ancom"
    TAG_DB_ANNOTATOR = "db_annotator"
    TAG_16S = "16S"
    TAG_16S_VISU = "16S_visualization"

    # Tags unique ids
    TAG_UBIOME_PIPELINE_ID = "ubiome_pipeline_id"
    TAG_FEATURE_INFERENCE_ID = "feature_inference_id"
    TAG_RAREFACTION_ID = "rarefaction_id"
    TAG_TAXONOMY_ID = "taxonomy_id"
    TAG_PCOA_ID = "pcoa_id"
    TAG_16S_ID = "16S_id"

    SELECTED_SCENARIO_KEY = "selected_scenario"
    SELECTED_ANALYSIS_KEY = "selected_analysis"
    STEP_PIPELINE_KEY = "step_pipeline"
    SELECTED_FOLDER_ID_KEY = "selected_folder_id"
    RESOURCE_ID_FASTQ_KEY = "resource_id_fastq"
    RESOURCE_ID_METADATA_TABLE_KEY = "resource_id_metadata_table"
    TAG_METADATA_UPDATED = "metadata_table_updated"
    SCENARIOS_BY_STEP_KEY = "scenarios_by_step"
    PCOA_DIVERSITY_TABLE_SELECT_KEY = "pcoa_diversity_table_select"
    SELECTED_ANNOTATION_TABLE_KEY = "selected_annotation_table"

    RESOURCE_SELECTOR_FASTQ_KEY = "resource_selector_fastq"
    ANALYSIS_NAME_USER = "analysis_name_user"

    # Tree
    TREE_ANALYSIS_OBJECT = "analysis_tree_menu_object"
    TREE_ANALYSIS_KEY = "analysis_tree_menu"

    # Config keys
    QIIME2_METADATA_CONFIG_KEY = "qiime2_metadata_config"
    FEATURE_INFERENCE_CONFIG_KEY = "feature_inference_config"
    RAREFACTION_CONFIG_KEY = "rarefaction_config"
    TAXONOMY_CONFIG_KEY = "taxonomy_config"
    PCOA_CONFIG_KEY = "pcoa_config"
    ANCOM_CONFIG_KEY = "ancom_config"

    @classmethod
    def reset_tree_analysis(cls) -> None:
        """Reset the analysis tree state in session."""
        if cls.TREE_ANALYSIS_KEY in st.session_state:
            del st.session_state[cls.TREE_ANALYSIS_KEY]

    @classmethod
    def check_if_required_is_filled(cls, valeur: str) -> bool:
        if not valeur:
            return False
        return True

    @classmethod
    def get_resource_selector_fastq(cls) -> ResourceModel:
        return st.session_state.get(cls.RESOURCE_SELECTOR_FASTQ_KEY, None)

    @classmethod
    def get_analysis_name_user(cls) -> str:
        return st.session_state.get(cls.ANALYSIS_NAME_USER, None)

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

    @classmethod
    def get_pcoa_diversity_table_select(cls) -> str:
        return st.session_state.get(cls.PCOA_DIVERSITY_TABLE_SELECT_KEY)

    @classmethod
    def get_selected_annotation_table(cls) -> ResourceModel:
        return st.session_state.get(cls.SELECTED_ANNOTATION_TABLE_KEY)

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
    def set_current_feature_scenario_id_parent(cls, scenario_id: str):
        st.session_state[cls.TAG_FEATURE_INFERENCE_ID] = scenario_id

    @classmethod
    def get_current_feature_scenario_id_parent(cls) -> str:
        return st.session_state.get(cls.TAG_FEATURE_INFERENCE_ID)

    @classmethod
    def set_current_taxonomy_scenario_id_parent(cls, scenario_id: str):
        st.session_state[cls.TAG_TAXONOMY_ID] = scenario_id

    @classmethod
    def get_current_taxonomy_scenario_id_parent(cls) -> str:
        return st.session_state.get(cls.TAG_TAXONOMY_ID)

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

    # Functions get config

    @classmethod
    def get_qiime2_metadata_config(cls) -> Dict:
        return st.session_state.get(cls.QIIME2_METADATA_CONFIG_KEY, {})

    @classmethod
    def get_feature_inference_config(cls) -> Dict:
        return st.session_state.get(cls.FEATURE_INFERENCE_CONFIG_KEY, {})

    @classmethod
    def get_rarefaction_config(cls) -> Dict:
        return st.session_state.get(cls.RAREFACTION_CONFIG_KEY, {})

    @classmethod
    def get_taxonomy_config(cls) -> Dict:
        return st.session_state.get(cls.TAXONOMY_CONFIG_KEY, {})

    @classmethod
    def get_pcoa_config(cls) -> Dict:
        return st.session_state.get(cls.PCOA_CONFIG_KEY, {})

    @classmethod
    def get_ancom_config(cls) -> Dict:
        return st.session_state.get(cls.ANCOM_CONFIG_KEY, {})

    @classmethod
    def get_sequencing_type(cls) -> str:
        return st.session_state.get(cls.TAG_SEQUENCING_TYPE)

    @classmethod
    def set_sequencing_type(cls, sequencing_type: str) -> None:
        st.session_state[cls.TAG_SEQUENCING_TYPE] = sequencing_type

    # Get scenarios ids of each step
    @classmethod
    def get_scenarios_by_step_dict(cls) -> Dict:
        return st.session_state.get(cls.SCENARIOS_BY_STEP_KEY, {})

    @classmethod
    def set_scenarios_by_step_dict(cls, scenarios_by_step: Dict) -> None:
        st.session_state[cls.SCENARIOS_BY_STEP_KEY] = scenarios_by_step

    @classmethod
    def get_scenario_step_metadata(cls) -> List[Scenario]:
        return cls.get_scenarios_by_step_dict().get(cls.TAG_METADATA)

    @classmethod
    def get_scenario_step_qc(cls) -> List[Scenario]:
        return cls.get_scenarios_by_step_dict().get(cls.TAG_QC)

    @classmethod
    def get_scenario_step_feature_inference(cls) -> List[Scenario]:
        return cls.get_scenarios_by_step_dict().get(cls.TAG_FEATURE_INFERENCE)

    @classmethod
    def get_scenario_step_rarefaction(cls) -> List[Scenario]:
        return cls.get_scenarios_by_step_dict().get(cls.TAG_RAREFACTION)

    @classmethod
    def get_scenario_step_taxonomy(cls) -> List[Scenario]:
        return cls.get_scenarios_by_step_dict().get(cls.TAG_TAXONOMY)

    @classmethod
    def get_scenario_step_pcoa(cls) -> List[Scenario]:
        return cls.get_scenarios_by_step_dict().get(cls.TAG_PCOA_DIVERSITY)

    @classmethod
    def get_scenario_step_ancom(cls) -> List[Scenario]:
        return cls.get_scenarios_by_step_dict().get(cls.TAG_ANCOM)

    @classmethod
    def get_scenario_step_db_annotator(cls) -> List[Scenario]:
        return cls.get_scenarios_by_step_dict().get(cls.TAG_DB_ANNOTATOR)

    @classmethod
    def get_scenario_step_16s(cls) -> List[Scenario]:
        return cls.get_scenarios_by_step_dict().get(cls.TAG_16S)

    @classmethod
    def get_scenario_step_16s_visu(cls) -> List[Scenario]:
        return cls.get_scenarios_by_step_dict().get(cls.TAG_16S_VISU)

    @classmethod
    def get_tree_menu_object(cls):
        """Get the tree menu instance from session state."""
        return st.session_state.get(cls.TREE_ANALYSIS_OBJECT)

    @classmethod
    def set_tree_menu_object(cls, tree_menu_object) -> None:
        st.session_state[cls.TREE_ANALYSIS_OBJECT] = tree_menu_object

    @classmethod
    def update_tree_menu_selection(cls, item_key: str):
        """Update the tree menu selection if tree menu instance exists."""
        tree_menu = cls.get_tree_menu_object()
        if tree_menu:
            tree_menu.set_selected_item(item_key)

    ### Get parent id
    # Retrieve feature inference
    @classmethod
    def get_parent_feature_inference_scenario_id_from_step(cls) -> str:
        """Extract the parent feature inference scenario ID from the current step pipeline."""
        step = cls.get_step_pipeline()
        if step and step.startswith(cls.TAG_RAREFACTION + "_"):
            # Extract the scenario ID from the step name like "rarefaction_scenario_id"
            return step.replace(cls.TAG_RAREFACTION + "_", "")
        if step and step.startswith(cls.TAG_TAXONOMY + "_"):
            return step.replace(cls.TAG_TAXONOMY + "_", "")
        if step and step.startswith(cls.TAG_16S + "_"):
            return step.replace(cls.TAG_16S + "_", "")
        return None

    @classmethod
    def get_parent_feature_inference_scenario_from_step(cls) -> 'Scenario':
        """Get the parent feature inference scenario from the current step pipeline."""
        scenario_id = cls.get_parent_feature_inference_scenario_id_from_step()
        if scenario_id:
            return Scenario.get_by_id(scenario_id)
        return None

    # Retrieve taxonomy
    @classmethod
    def get_parent_taxonomy_scenario_id_from_step(cls) -> str:
        """Extract the parent taxonomy scenario ID from the current step pipeline."""
        step = cls.get_step_pipeline()
        if step and step.startswith(cls.TAG_PCOA_DIVERSITY + "_"):
            return step.replace(cls.TAG_PCOA_DIVERSITY + "_", "")
        if step and step.startswith(cls.TAG_ANCOM + "_"):
            return step.replace(cls.TAG_ANCOM + "_", "")
        if step and step.startswith(cls.TAG_DB_ANNOTATOR + "_"):
            return step.replace(cls.TAG_DB_ANNOTATOR + "_", "")
        return None

    @classmethod
    def get_parent_taxonomy_scenario_from_step(cls) -> 'Scenario':
        """Get the parent taxonomy scenario from the current step pipeline."""
        scenario_id = cls.get_parent_taxonomy_scenario_id_from_step()
        if scenario_id:
            return Scenario.get_by_id(scenario_id)
        return None

    @classmethod
    def get_feature_inference_id_from_taxonomy_scenario(cls, taxonomy_scenario_id: str) -> str:
        """Get the feature inference ID from a taxonomy scenario ID."""
        taxonomy_scenario = Scenario.get_by_id(taxonomy_scenario_id)
        entity_tag_list = EntityTagList.find_by_entity(TagEntityType.SCENARIO, taxonomy_scenario.id)
        feature_inference_id_tag = entity_tag_list.get_tags_by_key(cls.TAG_FEATURE_INFERENCE_ID)[0].to_simple_tag()
        return feature_inference_id_tag.value

