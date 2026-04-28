import json
import os
import tempfile

import pandas as pd
import streamlit as st
from gws_core import ResourceModel, Scenario
from gws_core.tag.entity_tag_list import EntityTagList
from gws_core.tag.tag_entity_type import TagEntityType
from gws_streamlit_main import StreamlitTranslateLang, StreamlitTranslateService

from gws_ubiome.ubiome_dashboard._ubiome_dashboard_core.ubiome_scenario_service import (
    UbiomeScenarioService,
)


class State:
    """Class to manage the state of the app."""

    def __init__(cls, file_lang: str, lang_specific_folder_path: str | None = None):
        if lang_specific_folder_path:
            temp_dir = tempfile.mkdtemp(prefix="translations_")
            for lang in ["en", "fr"]:
                cls.merge_translation_files(file_lang, lang_specific_folder_path, temp_dir, lang)
            file_lang = temp_dir

        translate_service = StreamlitTranslateService(file_lang)
        st.session_state[UbiomeScenarioService.TRANSLATE_SERVICE] = translate_service

    @classmethod
    def merge_translation_files(cls, base_path, specific_path, output_path, lang):
        """Merge base and specific translation files for a given language."""
        base_file = os.path.join(base_path, f"{lang}.json")
        specific_file = os.path.join(specific_path, f"{lang}_specific.json")
        output_file = os.path.join(output_path, f"{lang}.json")

        merged_data = {}

        if os.path.exists(base_file):
            with open(base_file, encoding="utf-8") as f:
                merged_data.update(json.load(f))

        if os.path.exists(specific_file):
            with open(specific_file, encoding="utf-8") as f:
                merged_data.update(json.load(f))

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(merged_data, f, ensure_ascii=False, indent=4)

    @classmethod
    def get_lang(cls) -> StreamlitTranslateLang:
        # Get language from translate service instead of session state
        translate_service = cls.get_translate_service()
        if translate_service:
            return translate_service.get_lang()
        return StreamlitTranslateLang.EN  # Default to English

    @classmethod
    def set_lang(cls, value: StreamlitTranslateLang) -> None:
        # Update the translate service language instead of storing separately
        translate_service = cls.get_translate_service()
        if translate_service:
            translate_service.change_lang(value)
            cls.set_translate_service(translate_service)

    @classmethod
    def get_translate_service(cls):
        return st.session_state.get(UbiomeScenarioService.TRANSLATE_SERVICE, None)

    @classmethod
    def set_translate_service(cls, value: StreamlitTranslateService) -> None:
        st.session_state[UbiomeScenarioService.TRANSLATE_SERVICE] = value

    @classmethod
    def get_has_ratio_step(cls) -> bool:
        return st.session_state.get(UbiomeScenarioService.HAS_RATIO_STEP_KEY, False)

    @classmethod
    def set_has_ratio_step(cls, value: bool) -> None:
        st.session_state[UbiomeScenarioService.HAS_RATIO_STEP_KEY] = value

    @classmethod
    def get_is_standalone(cls) -> bool:
        return st.session_state.get(UbiomeScenarioService.STANDALONE_KEY, False)

    @classmethod
    def set_is_standalone(cls, value: bool) -> None:
        st.session_state[UbiomeScenarioService.STANDALONE_KEY] = value

    @classmethod
    def get_tree_default_item(cls) -> str:
        return st.session_state.get(UbiomeScenarioService.TREE_DEFAULT_ITEM_KEY, None)

    @classmethod
    def set_tree_default_item(cls, value: str) -> None:
        st.session_state[UbiomeScenarioService.TREE_DEFAULT_ITEM_KEY] = value

    @classmethod
    def set_associate_scenario_with_folder(cls, value: bool) -> None:
        st.session_state[UbiomeScenarioService.ASSOCIATE_FOLDER_KEY] = value

    @classmethod
    def get_associate_scenario_with_folder(cls) -> bool:
        return st.session_state.get(UbiomeScenarioService.ASSOCIATE_FOLDER_KEY, False)

    @classmethod
    def set_credentials_lab_large(cls, value: str | None) -> None:
        st.session_state[UbiomeScenarioService.CREDENTIALS_LAB_LARGE_KEY] = value

    @classmethod
    def get_credentials_lab_large(cls) -> str | None:
        return st.session_state.get(UbiomeScenarioService.CREDENTIALS_LAB_LARGE_KEY, None)

    @classmethod
    def reset_tree_analysis(cls) -> None:
        """Reset the analysis tree state in session."""
        if UbiomeScenarioService.TREE_ANALYSIS_KEY in st.session_state:
            del st.session_state[UbiomeScenarioService.TREE_ANALYSIS_KEY]

    @classmethod
    def check_if_required_is_filled(cls, valeur: str) -> bool:
        if not valeur:
            return False
        return True

    @classmethod
    def get_edited_df_metadata(cls) -> str:
        return st.session_state.get(UbiomeScenarioService.EDITED_DF_METADATA, None)

    @classmethod
    def set_edited_df_metadata(cls, df_metadata: pd.DataFrame) -> None:
        st.session_state[UbiomeScenarioService.EDITED_DF_METADATA] = df_metadata

    @classmethod
    def get_new_column_name(cls) -> str:
        return st.session_state.get(UbiomeScenarioService.NEW_COLUMN_INPUT_KEY, None)

    @classmethod
    def get_resource_selector_fastq(cls) -> ResourceModel:
        return st.session_state.get(UbiomeScenarioService.RESOURCE_SELECTOR_FASTQ_KEY, None)

    @classmethod
    def get_analysis_name_user(cls) -> str:
        return st.session_state.get(UbiomeScenarioService.ANALYSIS_NAME_USER, None)

    @classmethod
    def set_selected_scenario(cls, scenario: Scenario):
        st.session_state[UbiomeScenarioService.SELECTED_SCENARIO_KEY] = scenario

    @classmethod
    def get_selected_scenario(cls) -> Scenario:
        return st.session_state.get(UbiomeScenarioService.SELECTED_SCENARIO_KEY)

    @classmethod
    # It's the metadata scenario
    def set_selected_analysis(cls, scenario: Scenario):
        st.session_state[UbiomeScenarioService.SELECTED_ANALYSIS_KEY] = scenario

    @classmethod
    def get_selected_analysis(cls) -> Scenario:
        return st.session_state.get(UbiomeScenarioService.SELECTED_ANALYSIS_KEY)

    @classmethod
    def get_pcoa_diversity_table_select(cls) -> str:
        return st.session_state.get(UbiomeScenarioService.PCOA_DIVERSITY_TABLE_SELECT_KEY)

    @classmethod
    def get_selected_annotation_table(cls) -> ResourceModel:
        return st.session_state.get(UbiomeScenarioService.SELECTED_ANNOTATION_TABLE_KEY)

    @classmethod
    def get_selected_ratios_definition(cls) -> ResourceModel:
        return st.session_state.get(UbiomeScenarioService.SELECTED_RATIOS_DEFINITION_KEY)

    # Infos of the metadata scenario

    @classmethod
    def get_current_tag_value_by_key(cls, key: str) -> str:
        metadata_scenario: Scenario = cls.get_selected_analysis()
        entity_tag_list = EntityTagList.find_by_entity(TagEntityType.SCENARIO, metadata_scenario.id)
        tag = entity_tag_list.get_tags_by_key(key)[0].to_simple_tag()
        return tag.value

    @classmethod
    def get_current_ubiome_pipeline_id(cls) -> str:
        return cls.get_current_tag_value_by_key(UbiomeScenarioService.TAG_UBIOME_PIPELINE_ID)

    @classmethod
    def get_current_analysis_name(cls) -> str:
        return cls.get_current_tag_value_by_key(UbiomeScenarioService.TAG_ANALYSIS_NAME)

    @classmethod
    def get_current_fastq_name(cls) -> str:
        return cls.get_current_tag_value_by_key(UbiomeScenarioService.TAG_FASTQ)

    @classmethod
    def set_current_feature_scenario_id_parent(cls, scenario_id: str) -> None:
        st.session_state[UbiomeScenarioService.TAG_FEATURE_INFERENCE_ID] = scenario_id

    @classmethod
    def get_current_feature_scenario_id_parent(cls) -> str:
        return st.session_state.get(UbiomeScenarioService.TAG_FEATURE_INFERENCE_ID)

    @classmethod
    def set_current_taxonomy_scenario_id_parent(cls, scenario_id: str):
        st.session_state[UbiomeScenarioService.TAG_TAXONOMY_ID] = scenario_id

    @classmethod
    def get_current_taxonomy_scenario_id_parent(cls) -> str:
        return st.session_state.get(UbiomeScenarioService.TAG_TAXONOMY_ID)

    @classmethod
    def set_current_taxa_composition_scenario_id_parent(cls, scenario_id: str):
        st.session_state[UbiomeScenarioService.TAG_DB_ANNOTATOR_ID] = scenario_id

    @classmethod
    def get_current_taxa_composition_scenario_id_parent(cls) -> str:
        return st.session_state.get(UbiomeScenarioService.TAG_DB_ANNOTATOR_ID)

    @classmethod
    def get_current_16s_scenario_id_parent(cls) -> str:
        return st.session_state.get(UbiomeScenarioService.TAG_16S_ID)

    @classmethod
    def set_current_16s_scenario_id_parent(cls, scenario_id: str):
        st.session_state[UbiomeScenarioService.TAG_16S_ID] = scenario_id

    @classmethod
    def get_resource_id_fastq(cls) -> str:
        return st.session_state.get(UbiomeScenarioService.RESOURCE_ID_FASTQ_KEY)

    @classmethod
    def set_resource_id_fastq(cls, resource_id: str):
        st.session_state[UbiomeScenarioService.RESOURCE_ID_FASTQ_KEY] = resource_id

    @classmethod
    def get_resource_id_metadata_table(cls) -> str:
        return st.session_state.get(UbiomeScenarioService.RESOURCE_ID_METADATA_TABLE_KEY)

    @classmethod
    def set_resource_id_metadata_table(cls, resource_id: str):
        st.session_state[UbiomeScenarioService.RESOURCE_ID_METADATA_TABLE_KEY] = resource_id

    @classmethod
    def set_step_pipeline(cls, step_name: str):
        st.session_state[UbiomeScenarioService.STEP_PIPELINE_KEY] = step_name

    @classmethod
    def get_step_pipeline(cls) -> str:
        return st.session_state.get(UbiomeScenarioService.STEP_PIPELINE_KEY)

    @classmethod
    def set_selected_folder_id(cls, folder_id: str):
        st.session_state[UbiomeScenarioService.SELECTED_FOLDER_ID_KEY] = folder_id

    @classmethod
    def get_selected_folder_id(cls) -> str:
        return st.session_state.get(UbiomeScenarioService.SELECTED_FOLDER_ID_KEY)

    @classmethod
    def get_scenario_user_name(cls, key: str) -> str:
        return st.session_state.get(key, "")

    # Functions get config

    @classmethod
    def get_qiime2_metadata_config(cls) -> dict:
        return st.session_state.get(UbiomeScenarioService.QIIME2_METADATA_CONFIG_KEY, {})

    @classmethod
    def get_feature_inference_config(cls) -> dict:
        return st.session_state.get(UbiomeScenarioService.FEATURE_INFERENCE_CONFIG_KEY, {})

    @classmethod
    def get_rarefaction_config(cls) -> dict:
        return st.session_state.get(UbiomeScenarioService.RAREFACTION_CONFIG_KEY, {})

    @classmethod
    def get_taxonomy_config(cls) -> dict:
        return st.session_state.get(UbiomeScenarioService.TAXONOMY_CONFIG_KEY, {})

    @classmethod
    def get_pcoa_config(cls) -> dict:
        return st.session_state.get(UbiomeScenarioService.PCOA_CONFIG_KEY, {})

    @classmethod
    def get_ancom_config(cls) -> dict:
        return st.session_state.get(UbiomeScenarioService.ANCOM_CONFIG_KEY, {})

    @classmethod
    def get_functional_analysis_config(cls) -> dict:
        return st.session_state.get(UbiomeScenarioService.FUNCTIONAL_ANALYSIS_CONFIG_KEY, {})

    @classmethod
    def get_functional_analysis_visu_config(cls) -> dict:
        return st.session_state.get(UbiomeScenarioService.FUNCTIONAL_ANALYSIS_VISU_CONFIG_KEY, {})

    @classmethod
    def get_sequencing_type(cls) -> str:
        return st.session_state.get(UbiomeScenarioService.TAG_SEQUENCING_TYPE)

    @classmethod
    def set_sequencing_type(cls, sequencing_type: str) -> None:
        st.session_state[UbiomeScenarioService.TAG_SEQUENCING_TYPE] = sequencing_type

    # Get scenarios ids of each step
    @classmethod
    def get_scenarios_by_step_dict(cls) -> dict:
        return st.session_state.get(UbiomeScenarioService.SCENARIOS_BY_STEP_KEY, {})

    @classmethod
    def set_scenarios_by_step_dict(cls, scenarios_by_step: dict) -> None:
        st.session_state[UbiomeScenarioService.SCENARIOS_BY_STEP_KEY] = scenarios_by_step

    @classmethod
    def get_scenario_step_metadata(cls) -> list[Scenario]:
        return cls.get_scenarios_by_step_dict().get(UbiomeScenarioService.TAG_METADATA)

    @classmethod
    def get_scenario_step_qc(cls) -> list[Scenario]:
        return cls.get_scenarios_by_step_dict().get(UbiomeScenarioService.TAG_QC)

    @classmethod
    def get_scenario_step_multiqc(cls) -> list[Scenario]:
        return cls.get_scenarios_by_step_dict().get(UbiomeScenarioService.TAG_MULTIQC)

    @classmethod
    def get_scenario_step_feature_inference(cls) -> list[Scenario]:
        return cls.get_scenarios_by_step_dict().get(UbiomeScenarioService.TAG_FEATURE_INFERENCE)

    @classmethod
    def get_scenario_step_rarefaction(cls) -> list[Scenario]:
        scenarios_dict = cls.get_scenarios_by_step_dict().get(
            UbiomeScenarioService.TAG_RAREFACTION, {}
        )
        current_feature_id = cls.get_current_feature_scenario_id_parent()
        return scenarios_dict.get((current_feature_id), [])

    @classmethod
    def get_scenario_step_taxonomy(cls) -> list[Scenario]:
        scenarios_dict = cls.get_scenarios_by_step_dict().get(
            UbiomeScenarioService.TAG_TAXONOMY, {}
        )
        current_feature_id = cls.get_current_feature_scenario_id_parent()
        return scenarios_dict.get(current_feature_id, [])

    @classmethod
    def get_scenario_step_pcoa(cls) -> list[Scenario]:
        scenarios_dict = cls.get_scenarios_by_step_dict().get(
            UbiomeScenarioService.TAG_PCOA_DIVERSITY, {}
        )
        current_taxonomy_id = cls.get_current_taxonomy_scenario_id_parent()
        return scenarios_dict.get(current_taxonomy_id, [])

    @classmethod
    def get_scenario_step_ancom(cls) -> list[Scenario]:
        scenarios_dict = cls.get_scenarios_by_step_dict().get(UbiomeScenarioService.TAG_ANCOM, {})
        current_taxonomy_id = cls.get_current_taxonomy_scenario_id_parent()
        return scenarios_dict.get(current_taxonomy_id, [])

    @classmethod
    def get_scenario_step_db_annotator(cls) -> list[Scenario]:
        scenarios_dict = cls.get_scenarios_by_step_dict().get(
            UbiomeScenarioService.TAG_DB_ANNOTATOR, {}
        )
        current_taxonomy_id = cls.get_current_taxonomy_scenario_id_parent()
        return scenarios_dict.get(current_taxonomy_id, [])

    @classmethod
    def get_scenario_step_ratio(cls) -> list[Scenario]:
        scenarios_dict = cls.get_scenarios_by_step_dict().get(UbiomeScenarioService.TAG_RATIO, {})
        current_taxa_composition_id = cls.get_current_taxa_composition_scenario_id_parent()
        return scenarios_dict.get(current_taxa_composition_id, [])

    @classmethod
    def get_scenario_step_16s(cls) -> list[Scenario]:
        scenarios_dict = cls.get_scenarios_by_step_dict().get(UbiomeScenarioService.TAG_16S, {})
        current_feature_id = cls.get_current_feature_scenario_id_parent()
        return scenarios_dict.get(current_feature_id, [])

    @classmethod
    def get_scenario_step_16s_visu(cls) -> list[Scenario]:
        scenarios_dict = cls.get_scenarios_by_step_dict().get(
            UbiomeScenarioService.TAG_16S_VISU, {}
        )
        current_16s_id = cls.get_current_16s_scenario_id_parent()
        return scenarios_dict.get(current_16s_id, [])

    @classmethod
    def get_tree_menu_object(cls):
        """Get the tree menu instance from session state."""
        return st.session_state.get(UbiomeScenarioService.TREE_ANALYSIS_OBJECT)

    @classmethod
    def set_tree_menu_object(cls, tree_menu_object) -> None:
        st.session_state[UbiomeScenarioService.TREE_ANALYSIS_OBJECT] = tree_menu_object

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
        if step and step.startswith(UbiomeScenarioService.TAG_RAREFACTION + "_"):
            # Extract the scenario ID from the step name like "rarefaction_scenario_id"
            return step.replace(UbiomeScenarioService.TAG_RAREFACTION + "_", "")
        if step and step.startswith(UbiomeScenarioService.TAG_TAXONOMY + "_"):
            return step.replace(UbiomeScenarioService.TAG_TAXONOMY + "_", "")
        if step and step.startswith(UbiomeScenarioService.TAG_16S + "_"):
            return step.replace(UbiomeScenarioService.TAG_16S + "_", "")
        return None

    @classmethod
    def get_parent_feature_inference_scenario_from_step(cls) -> "Scenario":
        """Get the parent feature inference scenario from the current step pipeline."""
        scenario_id = cls.get_parent_feature_inference_scenario_id_from_step()
        if scenario_id:
            return Scenario.get_by_id(scenario_id)
        return None

    # Retrieve taxa composition
    @classmethod
    def get_parent_taxa_composition_scenario_id_from_step(cls) -> str:
        """Extract the parent taxa composition scenario ID from the current step pipeline."""
        step = cls.get_step_pipeline()
        if step and step.startswith(UbiomeScenarioService.TAG_RATIO + "_"):
            return step.replace(UbiomeScenarioService.TAG_RATIO + "_", "")
        return None

    @classmethod
    def get_parent_taxa_composition_scenario_from_step(cls) -> "Scenario":
        """Get the parent taxa composition scenario from the current step pipeline."""
        scenario_id = cls.get_parent_taxa_composition_scenario_id_from_step()
        if scenario_id:
            return Scenario.get_by_id(scenario_id)
        return None

    # Retrieve taxonomy
    @classmethod
    def get_parent_taxonomy_scenario_id_from_step(cls) -> str:
        """Extract the parent taxonomy scenario ID from the current step pipeline."""
        step = cls.get_step_pipeline()
        if step and step.startswith(UbiomeScenarioService.TAG_PCOA_DIVERSITY + "_"):
            return step.replace(UbiomeScenarioService.TAG_PCOA_DIVERSITY + "_", "")
        if step and step.startswith(UbiomeScenarioService.TAG_ANCOM + "_"):
            return step.replace(UbiomeScenarioService.TAG_ANCOM + "_", "")
        if step and step.startswith(UbiomeScenarioService.TAG_DB_ANNOTATOR + "_"):
            return step.replace(UbiomeScenarioService.TAG_DB_ANNOTATOR + "_", "")
        return None

    @classmethod
    def get_parent_taxonomy_scenario_from_step(cls) -> "Scenario":
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
        feature_inference_id_tag = entity_tag_list.get_tags_by_key(
            UbiomeScenarioService.TAG_FEATURE_INFERENCE_ID
        )[0].to_simple_tag()
        return feature_inference_id_tag.value

    @classmethod
    def get_taxonomy_scenario_id_from_db_annotator_scenario(
        cls, db_annotator_scenario_id: str
    ) -> str:
        """Get the taxonomy scenario ID from a ratio scenario ID."""
        db_annotator_scenario = Scenario.get_by_id(db_annotator_scenario_id)
        entity_tag_list = EntityTagList.find_by_entity(
            TagEntityType.SCENARIO, db_annotator_scenario.id
        )
        taxonomy_scenario_id_tag = entity_tag_list.get_tags_by_key(
            UbiomeScenarioService.TAG_TAXONOMY_ID
        )[0].to_simple_tag()
        return taxonomy_scenario_id_tag.value

    @classmethod
    def get_feature_inference_id_from_16s_scenario(
        cls, functional_16s_scenario_id: str
    ) -> str | None:
        """Get the feature inference ID from a 16S scenario ID."""
        if not functional_16s_scenario_id:
            return None
        functional_16s_scenario = Scenario.get_by_id(functional_16s_scenario_id)
        if functional_16s_scenario is None:
            return None
        entity_tag_list = EntityTagList.find_by_entity(
            TagEntityType.SCENARIO, functional_16s_scenario.id
        )
        feature_inference_id_tag = entity_tag_list.get_tags_by_key(
            UbiomeScenarioService.TAG_FEATURE_INFERENCE_ID
        )[0].to_simple_tag()
        return feature_inference_id_tag.value

    @classmethod
    def get_parent_16s_scenario_id_from_step(cls) -> str:
        """Extract the parent 16S scenario ID from the current step pipeline."""
        step = cls.get_step_pipeline()
        if step and step.startswith(UbiomeScenarioService.TAG_16S_VISU + "_"):
            return step.replace(UbiomeScenarioService.TAG_16S_VISU + "_", "")
        return None

    @classmethod
    def get_parent_16s_scenario_from_step(cls) -> "Scenario":
        """Get the parent 16S scenario from the current step pipeline."""
        scenario_id = cls.get_parent_16s_scenario_id_from_step()
        if scenario_id:
            return Scenario.get_by_id(scenario_id)
        return None
