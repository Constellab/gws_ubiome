"""Ubiome scenario service.

Wraps a single Ubiome scenario with its resolved tag metadata and provides
methods for accessing scenario information, tags, and protocol outputs.
Pipeline-level helpers (scenario search, creation, export) are exposed as
static methods.

"""

import os

import pandas as pd
from gws_core import (
    File,
    FsNodeExtractor,
    InputTask,
    ProtocolProxy,
    ProtocolService,
    ResourceModel,
    ResourceOrigin,
    Scenario,
    ScenarioCreationType,
    ScenarioProxy,
    ScenarioSearchBuilder,
    ScenarioStatus,
    ScenarioTransfertService,
    SendScenarioToLab,
    Settings,
    SpaceFolder,
    StringHelper,
    Tag,
)
from gws_core.tag.entity_tag_list import EntityTagList
from gws_core.tag.tag import TagOrigin
from gws_core.tag.tag_entity_type import TagEntityType
from gws_gaia import PCoATrainer
from gws_omix.rna_seq.multiqc.multiqc import MultiQc
from gws_omix.rna_seq.quality_check.fastq_init import FastqcInit

from gws_ubiome import (
    Ggpicrust2FunctionalAnalysis,
    Picrust2FunctionalAnalysis,
    Qiime2DifferentialAnalysis,
    Qiime2FeatureTableExtractorPE,
    Qiime2FeatureTableExtractorSE,
    Qiime2MetadataTableMaker,
    Qiime2QualityCheck,
    Qiime2RarefactionAnalysis,
    Qiime2TableDbAnnotator,
    Qiime2TaxonomyDiversity,
)


class UbiomeScenarioService:
    """Service for a single Ubiome analysis scenario.

    Loads a scenario, reads its tags, and provides convenient access to
    scenario metadata, tag values, and protocol outputs.  Pipeline-level
    operations (building the step dict, creating scenarios, exporting) are
    available as static methods so they can be called without an instance.

    No Streamlit imports — safe to use outside the Streamlit context.

    Usage:

        service = UbiomeScenarioService(scenario_id)
        pipeline_id = service.pipeline_id
        step = service.step

        # Pipeline-level helpers
        scenarios = UbiomeScenarioService.build_scenarios_by_step_dict(pipeline_id)
        new_scenario = UbiomeScenarioService.create_base_scenario_with_tags(
            folder_id, step_tag, title, fastq_name, analysis_name, pipeline_id
        )
        UbiomeScenarioService.export_scenario_to_lab_large(scenario_id, credentials)
    """

    TAG_BRICK = "brick"
    TAG_UBIOME = "ubiome"
    TAG_SEQUENCING_TYPE = "sequencing_type"
    TAG_FASTQ = "fastq_name"
    TAG_ANALYSIS_NAME = "analysis_name"

    # step tags
    TAG_METADATA = "metadata"
    TAG_QC = "quality_control"
    TAG_MULTIQC = "multiqc"
    TAG_FEATURE_INFERENCE = "feature_inference"
    TAG_RAREFACTION = "rarefaction"
    TAG_TAXONOMY = "taxonomy"
    TAG_PCOA_DIVERSITY = "pcoa_diversity"
    TAG_ANCOM = "ancom"
    TAG_DB_ANNOTATOR = "db_annotator"
    TAG_16S = "16s"
    TAG_16S_VISU = "16s_visualization"
    TAG_RATIO = "ratio"

    # Tags unique ids
    TAG_UBIOME_PIPELINE_ID = "ubiome_pipeline_id"
    TAG_FEATURE_INFERENCE_ID = "feature_inference_id"
    TAG_RAREFACTION_ID = "rarefaction_id"
    TAG_TAXONOMY_ID = "taxonomy_id"
    TAG_DB_ANNOTATOR_ID = "db_annotator_id"
    TAG_PCOA_ID = "pcoa_id"
    TAG_16S_ID = "16s_id"

    # Scenario names
    FEATURE_SCENARIO_NAME_INPUT_KEY = "feature_scenario_name_input"
    RAREFACTION_SCENARIO_NAME_INPUT_KEY = "rarefaction_scenario_name_input"
    TAXONOMY_SCENARIO_NAME_INPUT_KEY = "taxonomy_scenario_name_input"
    PCOA_SCENARIO_NAME_INPUT_KEY = "pcoa_scenario_name_input"
    ANCOM_SCENARIO_NAME_INPUT_KEY = "ancom_scenario_name_input"
    DB_ANNOTATOR_SCENARIO_NAME_INPUT_KEY = "db_annotator_scenario_name_input"
    RATIO_SCENARIO_NAME_INPUT_KEY = "ratio_scenario_name_input"
    FUNCTIONAL_ANALYSIS_SCENARIO_NAME_INPUT_KEY = "functional_analysis_scenario_name_input"
    FUNCTIONAL_ANALYSIS_VISU_SCENARIO_NAME_INPUT_KEY = (
        "functional_analysis_visu_scenario_name_input"
    )

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
    NEW_COLUMN_INPUT_KEY = "new_column_input"
    SELECTED_RATIOS_DEFINITION_KEY = "selected_ratios_definition"

    TREE_DEFAULT_ITEM_KEY = "tree_default_item"

    EDITED_DF_METADATA = "edited_df_metadata"
    STANDALONE_KEY = "standalone"

    ASSOCIATE_FOLDER_KEY = "associate_folder"

    CREDENTIALS_LAB_LARGE_KEY = "credentials_lab_large"

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
    FUNCTIONAL_ANALYSIS_CONFIG_KEY = "functional_analysis_config"
    FUNCTIONAL_ANALYSIS_VISU_CONFIG_KEY = "functional_analysis_visu_config"

    LANG_KEY = "lang_select"
    TRANSLATE_SERVICE = "translate_service"

    HAS_RATIO_STEP_KEY = "has_ratio_step"

    # Maps step tags to their protocol process names
    STEP_PROCESS_MAPPING: dict[str, str] = {
        "feature_inference": "feature_process",
        "rarefaction": "rarefaction_process",
        "taxonomy": "taxonomy_process",
        "pcoa_diversity": "pcoa_process",
        "ancom": "ancom_process",
        "db_annotator": "db_annotator_process",
        "16s": "functional_analysis_process",
        "16s_visualization": "functional_visu_process",
    }

    _scenario_proxy: ScenarioProxy
    _entity_tag_list: EntityTagList

    def __init__(self, scenario_id: str) -> None:
        """Initialize by loading the scenario and its tag list.

        :param scenario_id: ID of the scenario to wrap
        """
        self._scenario_proxy = ScenarioProxy.from_existing_scenario(scenario_id)
        self._entity_tag_list = EntityTagList.find_by_entity(
            TagEntityType.SCENARIO, self._scenario_proxy.get_model_id()
        )

    # ── Properties ─────────────────────────────────────────────────

    @property
    def scenario(self) -> Scenario:
        """The underlying Scenario model."""
        return self._scenario_proxy.get_model()

    @property
    def scenario_id(self) -> str:
        """The scenario ID."""
        return self._scenario_proxy.get_model_id()

    @property
    def protocol_proxy(self) -> ProtocolProxy:
        """ProtocolProxy for the scenario."""
        return self._scenario_proxy.get_protocol()

    # ── Instance export ─────────────────────────────────────────────

    def export_to_lab_large(self, credentials: str) -> None:
        """Export this scenario to Lab Large.

        :param credentials: Lab Large credentials string
        :raises Exception: If the export fails
        """
        UbiomeScenarioService.export_scenario_to_lab_large(self.scenario_id, credentials)

    # ── Static helpers ──────────────────────────────────────────────

    @staticmethod
    def create_scenario_table_data(
        scenarios: list[Scenario], process_name: str
    ) -> tuple[list[dict], set]:
        """Build table rows and the set of parameter column keys from a list of scenarios.

        :param scenarios: List of Scenario models to process
        :param process_name: Name of the protocol process to read config from
        :return: Tuple of (table_data rows, all_param_keys set)
        """
        table_data = []
        all_param_keys: set = set()
        scenarios_params = []

        # First pass: collect all parameter data and unique keys
        for scenario in scenarios:
            scenario_proxy = ScenarioProxy.from_existing_scenario(scenario.id)
            protocol_proxy = scenario_proxy.get_protocol()
            process = protocol_proxy.get_process(process_name)
            config_params = process._process_model.config.to_simple_dto().values

            # For PCOA scenarios, add diversity table name from input resource
            if process_name == "pcoa_process":
                config_params["Diversity Table"] = process.get_input("distance_table").name.split(
                    " - "
                )[1]

            scenarios_params.append((scenario, config_params))
            all_param_keys.update(config_params.keys())

        # Second pass: create table data with all parameters
        for scenario, config_params in scenarios_params:
            row_data: dict = {
                "id": scenario.id,
                "Scenario Name": scenario.title,
                "Creation Date": scenario.created_at.strftime("%Y-%m-%d %H:%M")
                if scenario.created_at
                else "",
                "Status": f"{UbiomeScenarioService.get_status_emoji(scenario.status)} {UbiomeScenarioService.get_status_prettify(scenario.status)}"
                if scenario.status
                else "",
            }
            for param_key in all_param_keys:
                row_data[param_key] = config_params.get(param_key, "")
            table_data.append(row_data)

        return table_data, all_param_keys

    @staticmethod
    def get_status_emoji(status: ScenarioStatus) -> str:
        """Return an emoji representing the given scenario status."""
        emoji_map = {
            ScenarioStatus.DRAFT: "📝",
            ScenarioStatus.IN_QUEUE: "⏳",
            ScenarioStatus.WAITING_FOR_CLI_PROCESS: "⏸️",
            ScenarioStatus.RUNNING: "🔄",
            ScenarioStatus.SUCCESS: "✅",
            ScenarioStatus.ERROR: "❌",
            ScenarioStatus.PARTIALLY_RUN: "✔️",
        }
        return emoji_map.get(status, "")

    @staticmethod
    def get_status_prettify(status: ScenarioStatus) -> str:
        """Return a human-readable label for the given scenario status."""
        prettify_map = {
            ScenarioStatus.DRAFT: "Draft",
            ScenarioStatus.IN_QUEUE: "In Queue",
            ScenarioStatus.WAITING_FOR_CLI_PROCESS: "Waiting",
            ScenarioStatus.RUNNING: "Running",
            ScenarioStatus.SUCCESS: "Success",
            ScenarioStatus.ERROR: "Error",
            ScenarioStatus.PARTIALLY_RUN: "Partially Run",
        }
        return prettify_map.get(status, "")

    @staticmethod
    def export_scenario_to_lab_large(scenario_id: str, credentials: str) -> None:
        """Export a scenario to Lab Large.

        :param scenario_id: ID of the scenario to export
        :param credentials: Lab Large credentials string
        :raises Exception: If the export fails
        """
        ScenarioTransfertService.export_scenario_to_lab(
            scenario_id=scenario_id,
            values=SendScenarioToLab.build_config(
                credentials,
                "All",
                "Force new scenario",
                True,
            ),
        )

    @staticmethod
    def search_updated_metadata_table(metadata_scenario_id: str) -> File | None:
        """Search for an updated metadata File resource in the given metadata scenario.

        :param metadata_scenario_id: ID of the metadata scenario to inspect
        :return: Updated metadata File resource, or None if not found
        """
        protocol_proxy: ProtocolProxy = ScenarioProxy.from_existing_scenario(
            metadata_scenario_id
        ).get_protocol()
        try:
            return protocol_proxy.get_process("updated_metadata").get_output("resource")
        except Exception:
            return None

    @staticmethod
    def add_tags_on_metadata_resource(metadata_model_id: str, pipeline_id: str) -> None:
        """Add the standard ubiome metadata tags to a resource.

        :param metadata_model_id: Model ID of the metadata File resource
        :param pipeline_id: Ubiome pipeline ID tag value
        """
        user_origin = TagOrigin.current_user_origin()
        entity_tags = EntityTagList.find_by_entity(TagEntityType.RESOURCE, metadata_model_id)
        entity_tags._default_origin = user_origin  # TODO will be fixed in future releases of core

        entity_tags.add_tag(
            Tag(
                UbiomeScenarioService.TAG_UBIOME,
                UbiomeScenarioService.TAG_METADATA_UPDATED,
                is_propagable=False,
            )
        )
        entity_tags.add_tag(
            Tag(
                UbiomeScenarioService.TAG_UBIOME_PIPELINE_ID,
                pipeline_id,
                is_propagable=False,
            )
        )

    @staticmethod
    def save_metadata_table_to_resource(
        edited_df: pd.DataFrame,
        header_lines: list[str],
        analysis_name: str,
        pipeline_id: str,
        protocol: ProtocolProxy,
        existing_resource: File | None = None,
    ) -> str:
        """Save the edited metadata DataFrame to a File resource and attach it to the protocol.

        Deletes any previously saved updated metadata resource before saving the new one.

        :param edited_df: Edited metadata DataFrame to save
        :param header_lines: Comment/header lines to prepend to the file
        :param analysis_name: Analysis name used to build the output file name
        :param pipeline_id: Ubiome pipeline ID used for tagging the resource
        :param protocol: ProtocolProxy of the metadata scenario
        :param existing_resource: Previous updated metadata File resource to replace, or None
        :return: Model ID of the newly created metadata File resource
        """
        if existing_resource is not None:
            ProtocolService.reset_process_of_protocol(protocol._process_model, "updated_metadata")
            protocol.refresh().delete_process("updated_metadata")
            ResourceModel.get_by_id(existing_resource.get_model_id()).delete_instance()

        path_temp = os.path.join(
            os.path.abspath(os.path.dirname(__file__)), Settings.make_temp_dir()
        )
        full_path = os.path.join(path_temp, f"{analysis_name}_Metadata_updated.tsv")

        content_to_save = ""
        if header_lines:
            content_to_save = "\n".join(header_lines) + "\n"
        content_to_save += edited_df.to_csv(index=False, sep="\t")

        with open(full_path, "w") as f:
            f.write(content_to_save)

        metadata_file = File(full_path)
        resource_model = ResourceModel.save_from_resource(
            metadata_file, origin=ResourceOrigin.UPLOADED, flagged=True
        )
        metadata_model_id = metadata_file.get_model_id()

        UbiomeScenarioService.add_tags_on_metadata_resource(metadata_model_id, pipeline_id)

        protocol.add_process(
            InputTask,
            "updated_metadata",
            {InputTask.config_name: resource_model.get_resource().get_model_id()},
        )

        return metadata_model_id

    @staticmethod
    def create_base_scenario_with_tags(
        folder_id: str,
        step_tag: str,
        title: str,
        fastq_name: str,
        analysis_name: str,
        pipeline_id: str,
    ) -> ScenarioProxy:
        """Create a new scenario with the standard ubiome base tags.

        :param folder_id: ID of the SpaceFolder to place the scenario in
        :param step_tag: Step tag value (e.g. TAG_FEATURE_INFERENCE)
        :param title: Scenario title
        :param fastq_name: Fastq name tag value
        :param analysis_name: Analysis name tag value
        :param pipeline_id: Ubiome pipeline ID tag value
        :return: The newly created ScenarioProxy
        """
        folder: SpaceFolder = SpaceFolder.get_by_id(folder_id)
        scenario = ScenarioProxy(
            None,
            folder=folder,
            title=title,
            creation_type=ScenarioCreationType.MANUAL,
        )

        scenario.add_tag(
            Tag(UbiomeScenarioService.TAG_FASTQ, fastq_name, is_propagable=False, auto_parse=True)
        )
        scenario.add_tag(
            Tag(
                UbiomeScenarioService.TAG_BRICK,
                UbiomeScenarioService.TAG_UBIOME,
                is_propagable=False,
                auto_parse=True,
            )
        )
        scenario.add_tag(Tag(UbiomeScenarioService.TAG_UBIOME, step_tag, is_propagable=False))
        scenario.add_tag(
            Tag(
                UbiomeScenarioService.TAG_ANALYSIS_NAME,
                analysis_name,
                is_propagable=False,
                auto_parse=True,
            )
        )
        scenario.add_tag(
            Tag(
                UbiomeScenarioService.TAG_UBIOME_PIPELINE_ID,
                pipeline_id,
                is_propagable=False,
                auto_parse=True,
            )
        )

        return scenario

    @staticmethod
    def build_scenarios_by_step_dict(
        ubiome_pipeline_id: str,
        has_ratio_step: bool = False,
    ) -> dict[str, list | dict]:
        """Build a mapping of step names to scenarios for a given pipeline ID.

        Steps without parent dependencies map to a ``list[Scenario]``.
        Steps that depend on a parent scenario map to a
        ``dict[parent_scenario_id, list[Scenario]]``.

        :param ubiome_pipeline_id: The pipeline ID to search for
        :param has_ratio_step: Whether the ratio step should be included
        :return: Dict mapping step names to scenarios or nested dicts
        """
        ubiome_pipeline_id_parsed = Tag.parse_tag(ubiome_pipeline_id)

        all_scenarios: list[Scenario] = (
            ScenarioSearchBuilder()
            .add_tag_filter(
                Tag(
                    key=UbiomeScenarioService.TAG_UBIOME_PIPELINE_ID,
                    value=ubiome_pipeline_id_parsed,
                    auto_parse=True,
                )
            )
            .add_is_archived_filter(False)
            .search_all()
        )

        standalone_steps = {
            UbiomeScenarioService.TAG_METADATA,
            UbiomeScenarioService.TAG_QC,
            UbiomeScenarioService.TAG_MULTIQC,
            UbiomeScenarioService.TAG_FEATURE_INFERENCE,
        }
        feature_dependent_steps = {
            UbiomeScenarioService.TAG_RAREFACTION,
            UbiomeScenarioService.TAG_TAXONOMY,
            UbiomeScenarioService.TAG_16S,
        }
        taxonomy_dependent_steps = {
            UbiomeScenarioService.TAG_PCOA_DIVERSITY,
            UbiomeScenarioService.TAG_ANCOM,
            UbiomeScenarioService.TAG_DB_ANNOTATOR,
        }

        scenarios_by_step: dict = {}

        for scenario in all_scenarios:
            entity_tag_list = EntityTagList.find_by_entity(TagEntityType.SCENARIO, scenario.id)
            step_tags = entity_tag_list.get_tags_by_key(UbiomeScenarioService.TAG_UBIOME)
            if not step_tags:
                continue
            step_name = step_tags[0].to_simple_tag().value

            if step_name in standalone_steps:
                scenarios_by_step.setdefault(step_name, []).append(scenario)

            elif step_name in feature_dependent_steps:
                feature_id_tags = entity_tag_list.get_tags_by_key(
                    UbiomeScenarioService.TAG_FEATURE_INFERENCE_ID
                )
                if feature_id_tags:
                    parent_id = feature_id_tags[0].to_simple_tag().value
                    scenarios_by_step.setdefault(step_name, {}).setdefault(parent_id, []).append(
                        scenario
                    )

            elif step_name == UbiomeScenarioService.TAG_16S_VISU:
                s16_id_tags = entity_tag_list.get_tags_by_key(UbiomeScenarioService.TAG_16S_ID)
                if s16_id_tags:
                    parent_id = s16_id_tags[0].to_simple_tag().value
                    scenarios_by_step.setdefault(step_name, {}).setdefault(parent_id, []).append(
                        scenario
                    )

            elif step_name in taxonomy_dependent_steps:
                taxonomy_id_tags = entity_tag_list.get_tags_by_key(
                    UbiomeScenarioService.TAG_TAXONOMY_ID
                )
                if taxonomy_id_tags:
                    parent_id = taxonomy_id_tags[0].to_simple_tag().value
                    scenarios_by_step.setdefault(step_name, {}).setdefault(parent_id, []).append(
                        scenario
                    )

            elif has_ratio_step and step_name == UbiomeScenarioService.TAG_RATIO:
                db_annotator_tags = entity_tag_list.get_tags_by_key(
                    UbiomeScenarioService.TAG_DB_ANNOTATOR_ID
                )
                if db_annotator_tags:
                    parent_id = db_annotator_tags[0].to_simple_tag().value
                    scenarios_by_step.setdefault(step_name, {}).setdefault(parent_id, []).append(
                        scenario
                    )

        return scenarios_by_step

    @staticmethod
    def get_scenario_step_tag(scenario_id: str) -> str:
        """Return the ubiome step tag value for a scenario.

        :param scenario_id: ID of the scenario to inspect
        :return: Step tag value (e.g. TAG_FEATURE_INFERENCE)
        """
        entity_tag_list = EntityTagList.find_by_entity(TagEntityType.SCENARIO, scenario_id)
        return str(
            entity_tag_list.get_tags_by_key(UbiomeScenarioService.TAG_UBIOME)[0]
            .to_simple_tag()
            .value
        )

    @staticmethod
    def get_scenario_process_info(scenario_id: str, process_name: str) -> tuple[str, dict]:
        """Return the task name and config parameters for a process in a scenario.

        :param scenario_id: ID of the scenario to inspect
        :param process_name: Name of the protocol process
        :return: Tuple of (task_name, config_params)
        """
        protocol_proxy = ScenarioProxy.from_existing_scenario(scenario_id).get_protocol()
        process = protocol_proxy.get_process(process_name)
        config_params = process._process_model.config.to_simple_dto().values
        task_name = str(process._process_model.name)
        return task_name, config_params

    @staticmethod
    def get_scenario_edit_data(scenario_id: str) -> tuple[str, type, dict]:
        """Return all data needed to populate the scenario edit form.

        :param scenario_id: ID of the scenario to edit
        :return: Tuple of (step_tag, task_class, current_config)
        :raises ValueError: If the step tag is not in STEP_PROCESS_MAPPING
        """
        step_tag = UbiomeScenarioService.get_scenario_step_tag(scenario_id)
        if step_tag not in UbiomeScenarioService.STEP_PROCESS_MAPPING:
            raise ValueError(f"Unknown step type: {step_tag}")
        process_name = UbiomeScenarioService.STEP_PROCESS_MAPPING[step_tag]
        protocol_proxy = ScenarioProxy.from_existing_scenario(scenario_id).get_protocol()
        process = protocol_proxy.get_process(process_name)
        return (
            step_tag,
            process.get_process_type(),
            process._process_model.config.to_simple_dto().values,
        )

    @staticmethod
    def update_scenario_process_config(scenario_id: str, updated_config: dict) -> None:
        """Update the process configuration for a scenario.

        :param scenario_id: ID of the scenario to update
        :param updated_config: New config values to apply
        """
        step_tag = UbiomeScenarioService.get_scenario_step_tag(scenario_id)
        process_name = UbiomeScenarioService.STEP_PROCESS_MAPPING[step_tag]
        protocol_proxy = ScenarioProxy.from_existing_scenario(scenario_id).get_protocol()
        protocol_proxy.get_process(process_name).set_config_params(updated_config)

    @staticmethod
    def run_scenario(scenario_id: str) -> None:
        """Add a scenario to the execution queue.

        :param scenario_id: ID of the scenario to run
        """
        ScenarioProxy.from_existing_scenario(scenario_id).add_to_queue()

    # ── Scenario creation helpers ───────────────────────────────────

    @staticmethod
    def has_successful_scenario(step_name: str, scenarios_by_step: dict) -> bool:
        """Return True if the step has at least one scenario with SUCCESS status.

        :param step_name: Step tag name to check
        :param scenarios_by_step: Dict from build_scenarios_by_step_dict
        """
        if step_name not in scenarios_by_step:
            return False
        return any(s.status == ScenarioStatus.SUCCESS for s in scenarios_by_step[step_name])

    @staticmethod
    def get_scenario_sequencing_type(scenario_id: str) -> str:
        """Return the sequencing_type config value from the metadata process of a scenario.

        :param scenario_id: ID of the metadata scenario
        :return: sequencing_type string (e.g. 'paired-end')
        """
        return (
            ScenarioProxy.from_existing_scenario(scenario_id)
            .get_protocol()
            .get_process("metadata_process")
            .get_param("sequencing_type")
        )

    @staticmethod
    def get_beta_diversity_tables(taxonomy_scenario_id: str) -> dict:
        """Return beta diversity tables from a taxonomy scenario output.

        :param taxonomy_scenario_id: ID of the taxonomy scenario
        :return: Dict of resource name -> resource, filtered to beta diversity tables
        """
        protocol_proxy = ScenarioProxy.from_existing_scenario(taxonomy_scenario_id).get_protocol()
        diversity_resource_set = protocol_proxy.get_process("taxonomy_process").get_output(
            "diversity_tables"
        )
        all_tables = diversity_resource_set.get_resources()
        return {k: v for k, v in all_tables.items() if "beta" in k.lower()}

    @staticmethod
    def create_metadata_scenario(
        folder_id: str,
        fastq_resource_model_id: str,
        analysis_name: str,
        qiime2_config: dict,
    ) -> ScenarioProxy:
        """Create a new metadata scenario (step 1 of the pipeline).

        Generates a new pipeline ID internally.
        Returns an unqueued ScenarioProxy — the caller must call add_to_queue().

        :param folder_id: SpaceFolder ID to place the scenario in
        :param fastq_resource_model_id: ResourceModel ID of the FastqFolder resource
        :param analysis_name: User-provided analysis name
        :param qiime2_config: Qiime2MetadataTableMaker config values dict
        :return: Fully wired ScenarioProxy (not yet queued)
        """
        fastq_resource_model = ResourceModel.get_by_id(fastq_resource_model_id)
        fastq_model_inner_id = fastq_resource_model.get_resource().get_model_id()
        fastq_name = Tag.parse_tag(fastq_resource_model.get_resource().get_name())
        analysis_name_parsed = Tag.parse_tag(analysis_name)
        pipeline_id = StringHelper.generate_uuid()

        folder: SpaceFolder = SpaceFolder.get_by_id(folder_id)
        scenario = ScenarioProxy(
            None,
            folder=folder,
            title=f"{analysis_name} - Metadata",
            creation_type=ScenarioCreationType.MANUAL,
        )
        scenario.add_tag(
            Tag(UbiomeScenarioService.TAG_FASTQ, fastq_name, is_propagable=False, auto_parse=True)
        )
        scenario.add_tag(
            Tag(
                UbiomeScenarioService.TAG_BRICK,
                UbiomeScenarioService.TAG_UBIOME,
                is_propagable=False,
                auto_parse=True,
            )
        )
        scenario.add_tag(
            Tag(
                UbiomeScenarioService.TAG_UBIOME,
                UbiomeScenarioService.TAG_METADATA,
                is_propagable=False,
            )
        )
        scenario.add_tag(
            Tag(
                UbiomeScenarioService.TAG_ANALYSIS_NAME,
                analysis_name_parsed,
                is_propagable=False,
                auto_parse=True,
            )
        )
        scenario.add_tag(
            Tag(
                UbiomeScenarioService.TAG_UBIOME_PIPELINE_ID,
                pipeline_id,
                is_propagable=False,
                auto_parse=True,
            )
        )

        protocol = scenario.get_protocol()
        fastq_input = protocol.add_process(
            InputTask, "selected_fastq", {InputTask.config_name: fastq_model_inner_id}
        )
        metadata_process = protocol.add_process(
            Qiime2MetadataTableMaker, "metadata_process", config_params=qiime2_config
        )
        protocol.add_connector(
            out_port=fastq_input >> "resource", in_port=metadata_process << "fastq_folder"
        )
        protocol.add_output(
            "metadata_process_output", metadata_process >> "metadata_table", flag_resource=False
        )
        return scenario

    @staticmethod
    def create_qc_scenario(
        folder_id: str,
        fastq_name: str,
        analysis_name: str,
        pipeline_id: str,
        metadata_resource_id: str,
        fastq_resource_id: str,
        sequencing_type: str,
    ) -> ScenarioProxy:
        """Create and wire a Quality Control scenario.

        :param folder_id: SpaceFolder ID
        :param fastq_name: Fastq name tag value
        :param analysis_name: Analysis name tag value
        :param pipeline_id: Pipeline ID tag value
        :param metadata_resource_id: Resource model ID of the metadata file
        :param fastq_resource_id: Resource model ID of the FastqFolder
        :param sequencing_type: Sequencing type string
        :return: Fully wired ScenarioProxy (not yet queued)
        """
        scenario = UbiomeScenarioService.create_base_scenario_with_tags(
            folder_id=folder_id,
            step_tag=UbiomeScenarioService.TAG_QC,
            title=f"{analysis_name} - Quality check",
            fastq_name=fastq_name,
            analysis_name=analysis_name,
            pipeline_id=pipeline_id,
        )
        protocol = scenario.get_protocol()

        metadata_input = protocol.add_process(
            InputTask, "metadata_resource", {InputTask.config_name: metadata_resource_id}
        )
        fastq_input = protocol.add_process(
            InputTask, "fastq_resource", {InputTask.config_name: fastq_resource_id}
        )
        qc_process = protocol.add_process(
            Qiime2QualityCheck, "qc_process", config_params={"sequencing_type": sequencing_type}
        )
        protocol.add_connector(
            out_port=fastq_input >> "resource", in_port=qc_process << "fastq_folder"
        )
        protocol.add_connector(
            out_port=metadata_input >> "resource", in_port=qc_process << "metadata_table"
        )
        protocol.add_output(
            "qc_process_output_folder", qc_process >> "result_folder", flag_resource=False
        )
        protocol.add_output(
            "qc_process_output_quality_table", qc_process >> "quality_table", flag_resource=False
        )
        return scenario

    @staticmethod
    def create_multiqc_scenario(
        folder_id: str,
        fastq_name: str,
        analysis_name: str,
        pipeline_id: str,
        fastq_resource_id: str,
        metadata_resource_id: str,
    ) -> ScenarioProxy:
        """Create and wire a MultiQC scenario.

        :param folder_id: SpaceFolder ID
        :param fastq_name: Fastq name tag value
        :param analysis_name: Analysis name tag value
        :param pipeline_id: Pipeline ID tag value
        :param fastq_resource_id: Resource model ID of the FastqFolder
        :param metadata_resource_id: Resource model ID of the metadata file
        :return: Fully wired ScenarioProxy (not yet queued)
        """
        scenario = UbiomeScenarioService.create_base_scenario_with_tags(
            folder_id=folder_id,
            step_tag=UbiomeScenarioService.TAG_MULTIQC,
            title=f"{analysis_name} - MultiQC",
            fastq_name=fastq_name,
            analysis_name=analysis_name,
            pipeline_id=pipeline_id,
        )
        protocol = scenario.get_protocol()

        fastq_input = protocol.add_process(
            InputTask, "fastq_resource", {InputTask.config_name: fastq_resource_id}
        )
        metadata_input = protocol.add_process(
            InputTask, "metadata_resource", {InputTask.config_name: metadata_resource_id}
        )
        fastqc_process = protocol.add_process(FastqcInit, "fastqc_process")
        protocol.add_connector(
            out_port=fastq_input >> "resource", in_port=fastqc_process << "fastq_folder"
        )
        protocol.add_connector(
            out_port=metadata_input >> "resource", in_port=fastqc_process << "metadata"
        )
        multiqc_process = protocol.add_process(MultiQc, "multiqc_process")
        protocol.add_connector(
            out_port=fastqc_process >> "output", in_port=multiqc_process << "fastqc_reports_folder"
        )
        html_extractor = protocol.add_process(
            FsNodeExtractor,
            "fs_node_extractor_html",
            {"fs_node_path": "multiqc_combined.html"},
        )
        protocol.add_connector(
            out_port=multiqc_process >> "output", in_port=html_extractor << "source"
        )
        protocol.add_output(
            "multiqc_process_output_html", html_extractor >> "target", flag_resource=False
        )
        return scenario

    @staticmethod
    def create_feature_inference_scenario(
        folder_id: str,
        fastq_name: str,
        analysis_name: str,
        pipeline_id: str,
        title: str,
        task_class: type,
        config: dict,
        qc_scenario_id: str,
    ) -> ScenarioProxy:
        """Create and wire a Feature Inference scenario.

        :param folder_id: SpaceFolder ID
        :param fastq_name: Fastq name tag value
        :param analysis_name: Analysis name tag value
        :param pipeline_id: Pipeline ID tag value
        :param title: Scenario title
        :param task_class: Either Qiime2FeatureTableExtractorPE or Qiime2FeatureTableExtractorSE
        :param config: Task config values dict
        :param qc_scenario_id: ID of the QC scenario to read output from
        :return: Fully wired ScenarioProxy (not yet queued)
        """
        scenario = UbiomeScenarioService.create_base_scenario_with_tags(
            folder_id=folder_id,
            step_tag=UbiomeScenarioService.TAG_FEATURE_INFERENCE,
            title=title,
            fastq_name=fastq_name,
            analysis_name=analysis_name,
            pipeline_id=pipeline_id,
        )
        scenario.add_tag(
            Tag(
                UbiomeScenarioService.TAG_FEATURE_INFERENCE_ID,
                scenario.get_model_id(),
                is_propagable=False,
                auto_parse=True,
            )
        )
        protocol = scenario.get_protocol()

        feature_process = protocol.add_process(task_class, "feature_process", config_params=config)
        qc_output = (
            ScenarioProxy.from_existing_scenario(qc_scenario_id)
            .get_protocol()
            .get_process("qc_process")
            .get_output("result_folder")
        )
        qc_resource = protocol.add_process(
            InputTask, "qc_resource", {InputTask.config_name: qc_output.get_model_id()}
        )
        protocol.add_connector(
            out_port=qc_resource >> "resource",
            in_port=feature_process << "quality_check_folder",
        )
        protocol.add_output(
            "qiime2_feature_process_boxplot_output",
            feature_process >> "boxplot",
            flag_resource=False,
        )
        protocol.add_output(
            "qiime2_feature_process_stats_output",
            feature_process >> "stats",
            flag_resource=False,
        )
        protocol.add_output(
            "qiime2_feature_process_folder_output",
            feature_process >> "result_folder",
            flag_resource=False,
        )
        return scenario

    @staticmethod
    def create_rarefaction_scenario(
        folder_id: str,
        fastq_name: str,
        analysis_name: str,
        pipeline_id: str,
        title: str,
        config: dict,
        feature_scenario_id: str,
    ) -> ScenarioProxy:
        """Create and wire a Rarefaction scenario.

        :param folder_id: SpaceFolder ID
        :param fastq_name: Fastq name tag value
        :param analysis_name: Analysis name tag value
        :param pipeline_id: Pipeline ID tag value
        :param title: Scenario title
        :param config: Qiime2RarefactionAnalysis config values dict
        :param feature_scenario_id: ID of the feature inference scenario to read output from
        :return: Fully wired ScenarioProxy (not yet queued)
        """
        scenario = UbiomeScenarioService.create_base_scenario_with_tags(
            folder_id=folder_id,
            step_tag=UbiomeScenarioService.TAG_RAREFACTION,
            title=title,
            fastq_name=fastq_name,
            analysis_name=analysis_name,
            pipeline_id=pipeline_id,
        )
        scenario.add_tag(
            Tag(
                UbiomeScenarioService.TAG_FEATURE_INFERENCE_ID,
                feature_scenario_id,
                is_propagable=False,
                auto_parse=True,
            )
        )
        protocol = scenario.get_protocol()

        rarefaction_process = protocol.add_process(
            Qiime2RarefactionAnalysis, "rarefaction_process", config_params=config
        )
        feature_output = (
            ScenarioProxy.from_existing_scenario(feature_scenario_id)
            .get_protocol()
            .get_process("feature_process")
            .get_output("result_folder")
        )
        feature_resource = protocol.add_process(
            InputTask, "feature_resource", {InputTask.config_name: feature_output.get_model_id()}
        )
        protocol.add_connector(
            out_port=feature_resource >> "resource",
            in_port=rarefaction_process << "feature_frequency_folder",
        )
        protocol.add_output(
            "rarefaction_table_output",
            rarefaction_process >> "rarefaction_table",
            flag_resource=False,
        )
        protocol.add_output(
            "rarefaction_folder_output",
            rarefaction_process >> "result_folder",
            flag_resource=False,
        )
        return scenario

    @staticmethod
    def create_taxonomy_scenario(
        folder_id: str,
        fastq_name: str,
        analysis_name: str,
        pipeline_id: str,
        title: str,
        config: dict,
        feature_scenario_id: str,
    ) -> ScenarioProxy:
        """Create and wire a Taxonomy scenario.

        :param folder_id: SpaceFolder ID
        :param fastq_name: Fastq name tag value
        :param analysis_name: Analysis name tag value
        :param pipeline_id: Pipeline ID tag value
        :param title: Scenario title
        :param config: Qiime2TaxonomyDiversity config values dict
        :param feature_scenario_id: ID of the feature inference scenario to read output from
        :return: Fully wired ScenarioProxy (not yet queued)
        """
        scenario = UbiomeScenarioService.create_base_scenario_with_tags(
            folder_id=folder_id,
            step_tag=UbiomeScenarioService.TAG_TAXONOMY,
            title=title,
            fastq_name=fastq_name,
            analysis_name=analysis_name,
            pipeline_id=pipeline_id,
        )
        scenario.add_tag(
            Tag(
                UbiomeScenarioService.TAG_FEATURE_INFERENCE_ID,
                feature_scenario_id,
                is_propagable=False,
                auto_parse=True,
            )
        )
        scenario.add_tag(
            Tag(
                UbiomeScenarioService.TAG_TAXONOMY_ID,
                scenario.get_model_id(),
                is_propagable=False,
                auto_parse=True,
            )
        )
        protocol = scenario.get_protocol()

        taxonomy_process = protocol.add_process(
            Qiime2TaxonomyDiversity, "taxonomy_process", config_params=config
        )
        feature_output = (
            ScenarioProxy.from_existing_scenario(feature_scenario_id)
            .get_protocol()
            .get_process("feature_process")
            .get_output("result_folder")
        )
        feature_resource = protocol.add_process(
            InputTask, "feature_resource", {InputTask.config_name: feature_output.get_model_id()}
        )
        protocol.add_connector(
            out_port=feature_resource >> "resource",
            in_port=taxonomy_process << "rarefaction_analysis_result_folder",
        )
        protocol.add_output(
            "taxonomy_diversity_tables_output",
            taxonomy_process >> "diversity_tables",
            flag_resource=False,
        )
        protocol.add_output(
            "taxonomy_taxonomy_tables_output",
            taxonomy_process >> "taxonomy_tables",
            flag_resource=False,
        )
        protocol.add_output(
            "taxonomy_folder_output", taxonomy_process >> "result_folder", flag_resource=False
        )
        return scenario

    @staticmethod
    def create_pcoa_scenario(
        folder_id: str,
        fastq_name: str,
        analysis_name: str,
        pipeline_id: str,
        title: str,
        config: dict,
        feature_scenario_id: str,
        taxonomy_scenario_id: str,
        diversity_table_model_id: str,
    ) -> ScenarioProxy:
        """Create and wire a PCOA diversity scenario.

        :param folder_id: SpaceFolder ID
        :param fastq_name: Fastq name tag value
        :param analysis_name: Analysis name tag value
        :param pipeline_id: Pipeline ID tag value
        :param title: Scenario title
        :param config: PCoATrainer config values dict
        :param feature_scenario_id: Parent feature inference scenario ID
        :param taxonomy_scenario_id: Parent taxonomy scenario ID
        :param diversity_table_model_id: Resource model ID of the selected beta diversity table
        :return: Fully wired ScenarioProxy (not yet queued)
        """
        scenario = UbiomeScenarioService.create_base_scenario_with_tags(
            folder_id=folder_id,
            step_tag=UbiomeScenarioService.TAG_PCOA_DIVERSITY,
            title=title,
            fastq_name=fastq_name,
            analysis_name=analysis_name,
            pipeline_id=pipeline_id,
        )
        scenario.add_tag(
            Tag(
                UbiomeScenarioService.TAG_FEATURE_INFERENCE_ID,
                feature_scenario_id,
                is_propagable=False,
                auto_parse=True,
            )
        )
        scenario.add_tag(
            Tag(
                UbiomeScenarioService.TAG_TAXONOMY_ID,
                taxonomy_scenario_id,
                is_propagable=False,
                auto_parse=True,
            )
        )
        protocol = scenario.get_protocol()

        pcoa_process = protocol.add_process(PCoATrainer, "pcoa_process", config_params=config)
        diversity_input = protocol.add_process(
            InputTask,
            "diversity_table_resource",
            {InputTask.config_name: diversity_table_model_id},
        )
        protocol.add_connector(
            out_port=diversity_input >> "resource", in_port=pcoa_process << "distance_table"
        )
        protocol.add_output("pcoa_result_output", pcoa_process >> "result", flag_resource=False)
        return scenario

    @staticmethod
    def create_ancom_scenario(
        folder_id: str,
        fastq_name: str,
        analysis_name: str,
        pipeline_id: str,
        title: str,
        config: dict,
        taxonomy_scenario_id: str,
        feature_scenario_id: str,
        metadata_resource_id: str,
    ) -> ScenarioProxy:
        """Create and wire an ANCOM differential analysis scenario.

        :param folder_id: SpaceFolder ID
        :param fastq_name: Fastq name tag value
        :param analysis_name: Analysis name tag value
        :param pipeline_id: Pipeline ID tag value
        :param title: Scenario title
        :param config: Qiime2DifferentialAnalysis config values dict
        :param taxonomy_scenario_id: Parent taxonomy scenario ID
        :param feature_scenario_id: Parent feature inference scenario ID
        :param metadata_resource_id: Resource model ID of the metadata file
        :return: Fully wired ScenarioProxy (not yet queued)
        """
        scenario = UbiomeScenarioService.create_base_scenario_with_tags(
            folder_id=folder_id,
            step_tag=UbiomeScenarioService.TAG_ANCOM,
            title=title,
            fastq_name=fastq_name,
            analysis_name=analysis_name,
            pipeline_id=pipeline_id,
        )
        scenario.add_tag(
            Tag(
                UbiomeScenarioService.TAG_FEATURE_INFERENCE_ID,
                feature_scenario_id,
                is_propagable=False,
                auto_parse=True,
            )
        )
        scenario.add_tag(
            Tag(
                UbiomeScenarioService.TAG_TAXONOMY_ID,
                taxonomy_scenario_id,
                is_propagable=False,
                auto_parse=True,
            )
        )
        protocol = scenario.get_protocol()

        ancom_process = protocol.add_process(
            Qiime2DifferentialAnalysis, "ancom_process", config_params=config
        )
        taxonomy_folder_output = (
            ScenarioProxy.from_existing_scenario(taxonomy_scenario_id)
            .get_protocol()
            .get_process("taxonomy_process")
            .get_output("result_folder")
        )
        taxonomy_folder_input = protocol.add_process(
            InputTask,
            "taxonomy_folder_resource",
            {InputTask.config_name: taxonomy_folder_output.get_model_id()},
        )
        metadata_input = protocol.add_process(
            InputTask, "metadata_file_resource", {InputTask.config_name: metadata_resource_id}
        )
        protocol.add_connector(
            out_port=taxonomy_folder_input >> "resource",
            in_port=ancom_process << "taxonomy_diversity_folder",
        )
        protocol.add_connector(
            out_port=metadata_input >> "resource", in_port=ancom_process << "metadata_file"
        )
        protocol.add_output(
            "ancom_result_tables_output",
            ancom_process >> "result_tables",
            flag_resource=False,
        )
        protocol.add_output(
            "ancom_result_folder_output",
            ancom_process >> "result_folder",
            flag_resource=False,
        )
        return scenario

    @staticmethod
    def create_db_annotator_scenario(
        folder_id: str,
        fastq_name: str,
        analysis_name: str,
        pipeline_id: str,
        title: str,
        taxonomy_scenario_id: str,
        feature_scenario_id: str,
        annotation_table_model_id: str,
    ) -> ScenarioProxy:
        """Create and wire a DB Annotator (taxa composition) scenario.

        :param folder_id: SpaceFolder ID
        :param fastq_name: Fastq name tag value
        :param analysis_name: Analysis name tag value
        :param pipeline_id: Pipeline ID tag value
        :param title: Scenario title
        :param taxonomy_scenario_id: Parent taxonomy scenario ID
        :param feature_scenario_id: Parent feature inference scenario ID
        :param annotation_table_model_id: Resource model ID of the annotation table
        :return: Fully wired ScenarioProxy (not yet queued)
        """
        scenario = UbiomeScenarioService.create_base_scenario_with_tags(
            folder_id=folder_id,
            step_tag=UbiomeScenarioService.TAG_DB_ANNOTATOR,
            title=title,
            fastq_name=fastq_name,
            analysis_name=analysis_name,
            pipeline_id=pipeline_id,
        )
        scenario.add_tag(
            Tag(
                UbiomeScenarioService.TAG_FEATURE_INFERENCE_ID,
                feature_scenario_id,
                is_propagable=False,
                auto_parse=True,
            )
        )
        scenario.add_tag(
            Tag(
                UbiomeScenarioService.TAG_TAXONOMY_ID,
                taxonomy_scenario_id,
                is_propagable=False,
                auto_parse=True,
            )
        )
        protocol = scenario.get_protocol()

        db_annotator_process = protocol.add_process(Qiime2TableDbAnnotator, "db_annotator_process")
        taxonomy_folder_output = (
            ScenarioProxy.from_existing_scenario(taxonomy_scenario_id)
            .get_protocol()
            .get_process("taxonomy_process")
            .get_output("result_folder")
        )
        taxonomy_folder_input = protocol.add_process(
            InputTask,
            "taxonomy_folder_resource",
            {InputTask.config_name: taxonomy_folder_output.get_model_id()},
        )
        annotation_input = protocol.add_process(
            InputTask,
            "annotation_table_resource",
            {InputTask.config_name: annotation_table_model_id},
        )
        protocol.add_connector(
            out_port=taxonomy_folder_input >> "resource",
            in_port=db_annotator_process << "diversity_folder",
        )
        protocol.add_connector(
            out_port=annotation_input >> "resource",
            in_port=db_annotator_process << "annotation_table",
        )
        protocol.add_output(
            "relative_abundance_table_output",
            db_annotator_process >> "relative_abundance_table",
            flag_resource=False,
        )
        protocol.add_output(
            "relative_abundance_plotly_output",
            db_annotator_process >> "relative_abundance_plotly_resource",
            flag_resource=False,
        )
        protocol.add_output(
            "absolute_abundance_table_output",
            db_annotator_process >> "absolute_abundance_table",
            flag_resource=False,
        )
        protocol.add_output(
            "absolute_abundance_plotly_output",
            db_annotator_process >> "absolute_abundance_plotly_resource",
            flag_resource=False,
        )
        return scenario

    @staticmethod
    def create_16s_scenario(
        folder_id: str,
        fastq_name: str,
        analysis_name: str,
        pipeline_id: str,
        title: str,
        config: dict,
        feature_scenario_id: str,
    ) -> ScenarioProxy:
        """Create and wire a 16S Functional Analysis (PICRUSt2) scenario.

        :param folder_id: SpaceFolder ID
        :param fastq_name: Fastq name tag value
        :param analysis_name: Analysis name tag value
        :param pipeline_id: Pipeline ID tag value
        :param title: Scenario title
        :param config: Picrust2FunctionalAnalysis config values dict
        :param feature_scenario_id: Parent feature inference scenario ID
        :return: Fully wired ScenarioProxy (not yet queued)
        """
        scenario = UbiomeScenarioService.create_base_scenario_with_tags(
            folder_id=folder_id,
            step_tag=UbiomeScenarioService.TAG_16S,
            title=title,
            fastq_name=fastq_name,
            analysis_name=analysis_name,
            pipeline_id=pipeline_id,
        )
        scenario.add_tag(
            Tag(
                UbiomeScenarioService.TAG_FEATURE_INFERENCE_ID,
                feature_scenario_id,
                is_propagable=False,
                auto_parse=True,
            )
        )
        scenario.add_tag(
            Tag(
                UbiomeScenarioService.TAG_16S_ID,
                scenario.get_model_id(),
                is_propagable=False,
                auto_parse=True,
            )
        )
        protocol = scenario.get_protocol()

        feature_output = (
            ScenarioProxy.from_existing_scenario(feature_scenario_id)
            .get_protocol()
            .get_process("feature_process")
            .get_output("result_folder")
        )
        feature_input = protocol.add_process(
            InputTask, "feature_resource", {InputTask.config_name: feature_output.get_model_id()}
        )
        table_extractor = protocol.add_process(
            FsNodeExtractor, "fs_node_extractor_table", {"fs_node_path": "table.qza"}
        )
        asv_extractor = protocol.add_process(
            FsNodeExtractor, "fs_node_extractor_asv", {"fs_node_path": "ASV-sequences.fasta"}
        )
        protocol.add_connector(
            out_port=feature_input >> "resource", in_port=table_extractor << "source"
        )
        protocol.add_connector(
            out_port=feature_input >> "resource", in_port=asv_extractor << "source"
        )
        functional_process = protocol.add_process(
            Picrust2FunctionalAnalysis, "functional_analysis_process", config_params=config
        )
        protocol.add_connector(
            out_port=table_extractor >> "target",
            in_port=functional_process << "ASV_count_abundance",
        )
        protocol.add_connector(
            out_port=asv_extractor >> "target", in_port=functional_process << "FASTA_of_asv"
        )
        protocol.add_output(
            "functional_analysis_result_output",
            functional_process >> "Folder_result",
            flag_resource=False,
        )
        return scenario

    @staticmethod
    def create_16s_visu_scenario(
        folder_id: str,
        fastq_name: str,
        analysis_name: str,
        pipeline_id: str,
        title: str,
        config: dict,
        feature_scenario_id: str,
        functional_scenario_id: str,
        metadata_resource_id: str,
    ) -> ScenarioProxy:
        """Create and wire a 16S Visualization (ggpicrust2) scenario.

        :param folder_id: SpaceFolder ID
        :param fastq_name: Fastq name tag value
        :param analysis_name: Analysis name tag value
        :param pipeline_id: Pipeline ID tag value
        :param title: Scenario title
        :param config: Ggpicrust2FunctionalAnalysis config values dict
        :param feature_scenario_id: Parent feature inference scenario ID
        :param functional_scenario_id: Parent 16S scenario ID
        :param metadata_resource_id: Resource model ID of the metadata file
        :return: Fully wired ScenarioProxy (not yet queued)
        """
        scenario = UbiomeScenarioService.create_base_scenario_with_tags(
            folder_id=folder_id,
            step_tag=UbiomeScenarioService.TAG_16S_VISU,
            title=title,
            fastq_name=fastq_name,
            analysis_name=analysis_name,
            pipeline_id=pipeline_id,
        )
        scenario.add_tag(
            Tag(
                UbiomeScenarioService.TAG_FEATURE_INFERENCE_ID,
                feature_scenario_id,
                is_propagable=False,
                auto_parse=True,
            )
        )
        scenario.add_tag(
            Tag(
                UbiomeScenarioService.TAG_16S_ID,
                functional_scenario_id,
                is_propagable=False,
                auto_parse=True,
            )
        )
        protocol = scenario.get_protocol()

        visu_process = protocol.add_process(
            Ggpicrust2FunctionalAnalysis, "functional_visu_process", config_params=config
        )
        functional_result_folder = (
            ScenarioProxy.from_existing_scenario(functional_scenario_id)
            .get_protocol()
            .get_process("functional_analysis_process")
            .get_output("Folder_result")
        )
        functional_input = protocol.add_process(
            InputTask,
            "functional_folder_resource",
            {InputTask.config_name: functional_result_folder.get_model_id()},
        )
        ko_extractor = protocol.add_process(
            FsNodeExtractor,
            "ko_file_extractor",
            {"fs_node_path": "KO_metagenome_out/pred_metagenome_unstrat.tsv.gz"},
        )
        metadata_input = protocol.add_process(
            InputTask, "metadata_file_resource", {InputTask.config_name: metadata_resource_id}
        )
        protocol.add_connector(
            out_port=functional_input >> "resource", in_port=ko_extractor << "source"
        )
        protocol.add_connector(
            out_port=ko_extractor >> "target", in_port=visu_process << "ko_abundance_file"
        )
        protocol.add_connector(
            out_port=metadata_input >> "resource", in_port=visu_process << "metadata_file"
        )
        protocol.add_output(
            "visu_resource_set_output", visu_process >> "resource_set", flag_resource=False
        )
        protocol.add_output(
            "visu_plotly_output", visu_process >> "plotly_result", flag_resource=False
        )
        return scenario

    @staticmethod
    def build_analysis_overview_table_data(
        scenarios: list[Scenario], has_ratio_step: bool
    ) -> list[dict]:
        """Build overview table row data for the first-page analysis list.

        For each metadata scenario, retrieves all related pipeline scenarios and
        annotates each row with the emoji status of every pipeline step.

        :param scenarios: List of metadata Scenario models
        :param has_ratio_step: Whether the ratio step should appear as a column
        :return: List of row dicts ready for slickgrid
        """
        step_types = [
            (UbiomeScenarioService.TAG_QC, "quality_control"),
            (UbiomeScenarioService.TAG_MULTIQC, "multiqc"),
            (UbiomeScenarioService.TAG_FEATURE_INFERENCE, "feature_inference"),
            (UbiomeScenarioService.TAG_RAREFACTION, "rarefaction"),
            (UbiomeScenarioService.TAG_TAXONOMY, "taxonomy"),
            (UbiomeScenarioService.TAG_PCOA_DIVERSITY, "pcoa_diversity"),
            (UbiomeScenarioService.TAG_ANCOM, "ancom"),
            (UbiomeScenarioService.TAG_DB_ANNOTATOR, "db_annotator"),
        ]
        if has_ratio_step:
            step_types.append((UbiomeScenarioService.TAG_RATIO, "ratio"))
        step_types.extend(
            [
                (UbiomeScenarioService.TAG_16S, "16s"),
                (UbiomeScenarioService.TAG_16S_VISU, "16s_visualization"),
            ]
        )
        step_fields = [field for _, field in step_types]

        table_data = []
        for scenario in scenarios:
            entity_tag_list = EntityTagList.find_by_entity(TagEntityType.SCENARIO, scenario.id)
            tag_analysis_name = entity_tag_list.get_tags_by_key(
                UbiomeScenarioService.TAG_ANALYSIS_NAME
            )[0].to_simple_tag()

            row_data: dict = {
                "id": scenario.id,
                "Name given": tag_analysis_name.value,
                "Folder": scenario.folder.name if scenario.folder else "",
                "metadata": UbiomeScenarioService.get_status_emoji(scenario.status),
            }

            pipeline_id_tags = entity_tag_list.get_tags_by_key(
                UbiomeScenarioService.TAG_UBIOME_PIPELINE_ID
            )
            if pipeline_id_tags:
                pipeline_id = pipeline_id_tags[0].to_simple_tag().value
                pipeline_scenarios = (
                    ScenarioSearchBuilder()
                    .add_tag_filter(
                        Tag(key=UbiomeScenarioService.TAG_UBIOME_PIPELINE_ID, value=pipeline_id)
                    )
                    .add_is_archived_filter(False)
                    .search_all()
                )
                for tag_value, field_name in step_types:
                    step_scenarios = [
                        s
                        for s in pipeline_scenarios
                        if any(
                            t.tag_key == UbiomeScenarioService.TAG_UBIOME
                            and t.tag_value == tag_value
                            for t in EntityTagList.find_by_entity(
                                TagEntityType.SCENARIO, s.id
                            ).get_tags()
                        )
                    ]
                    if step_scenarios:
                        latest = max(step_scenarios, key=lambda x: x.created_at)
                        row_data[field_name] = UbiomeScenarioService.get_status_emoji(latest.status)
                    else:
                        row_data[field_name] = ""
            else:
                for field in step_fields:
                    row_data[field] = ""

            table_data.append(row_data)
        return table_data
