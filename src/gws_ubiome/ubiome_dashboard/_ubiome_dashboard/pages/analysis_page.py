import streamlit as st
from typing import List
from state import State
from gws_core import Tag, File, Folder, ScenarioSearchBuilder,  Scenario, ScenarioStatus, ScenarioProxy, ProtocolProxy
from gws_ubiome.ubiome_dashboard._ubiome_dashboard.functions_steps import render_metadata_step, render_qc_step, render_feature_inference_step, render_rarefaction_step, render_taxonomy_step, render_pcoa_step, render_ancom_step, render_db_annotator_step, render_16s_step, render_16s_visu_step, search_updated_metadata_table
from gws_core.streamlit import StreamlitContainers, StreamlitRouter, StreamlitTreeMenu, StreamlitTreeMenuItem
from gws_core.tag.tag_entity_type import TagEntityType
from gws_core.tag.entity_tag_list import EntityTagList

# Check if steps are completed (have successful scenarios)
def has_successful_scenario(step_name, scenarios_by_step):
    if step_name not in scenarios_by_step:
        return False
    return any(s.status == ScenarioStatus.SUCCESS for s in scenarios_by_step[step_name])


def build_analysis_tree_menu(ubiome_state: State, ubiome_pipeline_id: str):
    """Build the tree menu for analysis workflow steps"""
    button_menu = StreamlitTreeMenu(key=ubiome_state.TREE_ANALYSIS_KEY)

    ubiome_pipeline_id_parsed = Tag.parse_tag(ubiome_pipeline_id)

    # Get all scenarios for this analysis, we retrieve all the other thanks to the id ubiome pipeline id
    search_scenario_builder = ScenarioSearchBuilder() \
        .add_tag_filter(Tag(key=ubiome_state.TAG_UBIOME_PIPELINE_ID, value=ubiome_pipeline_id_parsed, auto_parse=True)) \
        .add_is_archived_filter(False)

    all_scenarios: List[Scenario] = search_scenario_builder.search_all()


    # Group scenarios by step type
    scenarios_by_step = {}
    for scenario in all_scenarios:
        entity_tag_list = EntityTagList.find_by_entity(TagEntityType.SCENARIO, scenario.id)
        tag_step_name = entity_tag_list.get_tags_by_key(ubiome_state.TAG_UBIOME)[0].to_simple_tag()
        step_name = tag_step_name.value
        if step_name not in scenarios_by_step:
            scenarios_by_step[step_name] = []
        scenarios_by_step[step_name].append(scenario)

    ubiome_state.set_scenarios_by_step_dict(scenarios_by_step)

    # Set in the state if data is single-end or paired-end
    metadata_scenario = ubiome_state.get_scenario_step_metadata()[0]
    scenario_metadata_proxy = ScenarioProxy.from_existing_scenario(metadata_scenario.id)
    config_sequencing_type = scenario_metadata_proxy.get_protocol().get_process('metadata_process').get_param('sequencing_type')
    ubiome_state.set_sequencing_type(config_sequencing_type)

    # 1) Metadata table
    # Always show first step
    if ubiome_state.TAG_METADATA in scenarios_by_step:
        # If a scenario exists, use the first scenario's ID
        key_metadata = ubiome_state.get_scenario_step_metadata()[0].id
    else:
        key_metadata = ubiome_state.TAG_METADATA
    metadata_item = StreamlitTreeMenuItem(
        label="1) Metadata table",
        key=key_metadata,
        material_icon='table_chart'
    )


    button_menu.add_item(metadata_item)

    # 2) QC - only if metadata is successful
    if has_successful_scenario(ubiome_state.TAG_METADATA, scenarios_by_step) or ubiome_state.TAG_QC in scenarios_by_step:

        if ubiome_state.TAG_QC in scenarios_by_step:
            # Use the first QC scenario's ID
            key_qc = ubiome_state.get_scenario_step_qc()[0].id
        else:
            key_qc = ubiome_state.TAG_QC
        qc_item = StreamlitTreeMenuItem(
            label="2) QC",
            key=key_qc,
            material_icon='check_circle'
        )

        button_menu.add_item(qc_item)

    # 3) Feature inference - only if QC is successful
    if has_successful_scenario(ubiome_state.TAG_QC, scenarios_by_step) or ubiome_state.TAG_FEATURE_INFERENCE in scenarios_by_step:
        feature_item = StreamlitTreeMenuItem(
            label="3) Feature inference",
            key=ubiome_state.TAG_FEATURE_INFERENCE,
            material_icon='analytics'
        )

        if ubiome_state.TAG_FEATURE_INFERENCE in scenarios_by_step:
            for scenario in scenarios_by_step[ubiome_state.TAG_FEATURE_INFERENCE]:
                scenario_item = StreamlitTreeMenuItem(
                    label=scenario.get_short_name(),
                    key=scenario.id,
                    material_icon='description'
                )

                # 4) Rarefaction sub-step - use a key that includes the parent scenario ID
                rarefaction_item = StreamlitTreeMenuItem(
                    label="4) Rarefaction",
                    key=f"{ubiome_state.TAG_RAREFACTION}_{scenario.id}",  # Include parent scenario ID
                    material_icon='trending_down'
                )
                if ubiome_state.TAG_RAREFACTION in scenarios_by_step:
                    for rare_scenario in scenarios_by_step[ubiome_state.TAG_RAREFACTION]:
                        # Check if this rarefaction scenario belongs to this feature inference scenario
                        # by checking the feature inference ID tag
                        rare_entity_tag_list = EntityTagList.find_by_entity(TagEntityType.SCENARIO, rare_scenario.id)
                        rare_feature_id_tags = rare_entity_tag_list.get_tags_by_key(ubiome_state.TAG_FEATURE_INFERENCE_ID)
                        scenario_feature_id_tags = EntityTagList.find_by_entity(TagEntityType.SCENARIO, scenario.id).get_tags_by_key(ubiome_state.TAG_FEATURE_INFERENCE_ID)
                        if (rare_feature_id_tags and scenario_feature_id_tags and
                            rare_feature_id_tags[0].to_simple_tag().value == scenario_feature_id_tags[0].to_simple_tag().value):
                            rare_item = StreamlitTreeMenuItem(
                                label=rare_scenario.get_short_name(),
                                key=rare_scenario.id,
                                material_icon='description'
                            )
                            rarefaction_item.add_children([rare_item])

                # 4) Taxonomy sub-step
                taxonomy_item = StreamlitTreeMenuItem(
                    label="4) Taxonomy",
                    key=f"{ubiome_state.TAG_TAXONOMY}_{scenario.id}",  # Include parent scenario ID
                    material_icon='account_tree'
                )
                if ubiome_state.TAG_TAXONOMY in scenarios_by_step:
                    for tax_scenario in scenarios_by_step[ubiome_state.TAG_TAXONOMY]:
                        # Check if this taxonomy scenario belongs to this feature inference scenario
                        tax_entity_tag_list = EntityTagList.find_by_entity(TagEntityType.SCENARIO, tax_scenario.id)
                        tax_feature_id_tags = tax_entity_tag_list.get_tags_by_key(ubiome_state.TAG_FEATURE_INFERENCE_ID)
                        scenario_feature_id_tags = EntityTagList.find_by_entity(TagEntityType.SCENARIO, scenario.id).get_tags_by_key(ubiome_state.TAG_FEATURE_INFERENCE_ID)

                        if (tax_feature_id_tags and scenario_feature_id_tags and
                            tax_feature_id_tags[0].to_simple_tag().value == scenario_feature_id_tags[0].to_simple_tag().value):
                            tax_item = StreamlitTreeMenuItem(
                                label=tax_scenario.get_short_name(),
                                key=tax_scenario.id,
                                material_icon='description'
                            )

                            # Sub-analysis items under taxonomy
                            pcoa_diversity_item = StreamlitTreeMenuItem(
                                label="5) PCOA diversity",
                                key=f"{ubiome_state.TAG_PCOA_DIVERSITY}_{tax_scenario.id}",
                                material_icon='scatter_plot'
                            )
                            if ubiome_state.TAG_PCOA_DIVERSITY in scenarios_by_step:
                                for pcoa_scenario in scenarios_by_step[ubiome_state.TAG_PCOA_DIVERSITY]:
                                    # Check if this pcoa scenario belongs to this taxonomy scenario
                                    pcoa_entity_tag_list = EntityTagList.find_by_entity(TagEntityType.SCENARIO, pcoa_scenario.id)
                                    pcoa_taxonomy_id_tags = pcoa_entity_tag_list.get_tags_by_key(ubiome_state.TAG_TAXONOMY_ID)
                                    scenario_taxonomy_id_tags = EntityTagList.find_by_entity(TagEntityType.SCENARIO, tax_scenario.id).get_tags_by_key(ubiome_state.TAG_TAXONOMY_ID)

                                    if (pcoa_taxonomy_id_tags and scenario_taxonomy_id_tags and
                                        pcoa_taxonomy_id_tags[0].to_simple_tag().value == scenario_taxonomy_id_tags[0].to_simple_tag().value):
                                        pcoa_item = StreamlitTreeMenuItem(
                                            label=pcoa_scenario.get_short_name(),
                                            key=pcoa_scenario.id,
                                            material_icon='description'
                                        )
                                        pcoa_diversity_item.add_children([pcoa_item])

                            ancom_item = StreamlitTreeMenuItem(
                                label="6) ANCOM",
                                key=f"{ubiome_state.TAG_ANCOM}_{tax_scenario.id}",
                                material_icon='biotech'
                            )

                            # Check if ANCOM scenarios exist for this taxonomy
                            if ubiome_state.TAG_ANCOM in scenarios_by_step:
                                for ancom_scenario in scenarios_by_step[ubiome_state.TAG_ANCOM]:
                                    ancom_entity_tag_list = EntityTagList.find_by_entity(TagEntityType.SCENARIO, ancom_scenario.id)
                                    ancom_taxonomy_id_tags = ancom_entity_tag_list.get_tags_by_key(ubiome_state.TAG_TAXONOMY_ID)
                                    scenario_taxonomy_id_tags = EntityTagList.find_by_entity(TagEntityType.SCENARIO, tax_scenario.id).get_tags_by_key(ubiome_state.TAG_TAXONOMY_ID)

                                    if (ancom_taxonomy_id_tags and scenario_taxonomy_id_tags and
                                        ancom_taxonomy_id_tags[0].to_simple_tag().value == scenario_taxonomy_id_tags[0].to_simple_tag().value):
                                        ancom_item_child = StreamlitTreeMenuItem(
                                            label=ancom_scenario.get_short_name(),
                                            key=ancom_scenario.id,
                                            material_icon='description'
                                        )
                                        ancom_item.add_children([ancom_item_child])

                            taxa_comp_item = StreamlitTreeMenuItem(
                                label="7) Taxa Composition",
                                key=f"{ubiome_state.TAG_DB_ANNOTATOR}_{tax_scenario.id}",
                                material_icon='pie_chart'
                            )

                            # Check if DB annotator scenarios exist for this taxonomy
                            if ubiome_state.TAG_DB_ANNOTATOR in scenarios_by_step:
                                for db_scenario in scenarios_by_step[ubiome_state.TAG_DB_ANNOTATOR]:
                                    db_entity_tag_list = EntityTagList.find_by_entity(TagEntityType.SCENARIO, db_scenario.id)
                                    db_taxonomy_id_tags = db_entity_tag_list.get_tags_by_key(ubiome_state.TAG_TAXONOMY_ID)
                                    scenario_taxonomy_id_tags = EntityTagList.find_by_entity(TagEntityType.SCENARIO, tax_scenario.id).get_tags_by_key(ubiome_state.TAG_TAXONOMY_ID)

                                    if (db_taxonomy_id_tags and scenario_taxonomy_id_tags and
                                        db_taxonomy_id_tags[0].to_simple_tag().value == scenario_taxonomy_id_tags[0].to_simple_tag().value):
                                        db_item = StreamlitTreeMenuItem(
                                            label=db_scenario.get_short_name(),
                                            key=db_scenario.id,
                                            material_icon='description'
                                        )
                                        taxa_comp_item.add_children([db_item])

                            tax_item.add_children([pcoa_diversity_item, ancom_item, taxa_comp_item])
                            taxonomy_item.add_children([tax_item])

                # 8) 16S sub-step
                s16_item = StreamlitTreeMenuItem(
                    label="8) 16S",
                    key=f"{ubiome_state.TAG_16S}_{scenario.id}",
                    material_icon='dna'
                )
                if ubiome_state.TAG_16S in scenarios_by_step:
                    for functional_16s_scenario in scenarios_by_step[ubiome_state.TAG_16S]:
                        # Check if this 16S scenario belongs to this feature inference scenario
                        s16_entity_tag_list = EntityTagList.find_by_entity(TagEntityType.SCENARIO, functional_16s_scenario.id)
                        s16_feature_id_tags = s16_entity_tag_list.get_tags_by_key(ubiome_state.TAG_FEATURE_INFERENCE_ID)
                        scenario_feature_id_tags = EntityTagList.find_by_entity(TagEntityType.SCENARIO, scenario.id).get_tags_by_key(ubiome_state.TAG_FEATURE_INFERENCE_ID)

                        if (s16_feature_id_tags and scenario_feature_id_tags and
                            s16_feature_id_tags[0].to_simple_tag().value == scenario_feature_id_tags[0].to_simple_tag().value):
                            s16_item_child = StreamlitTreeMenuItem(
                                label=functional_16s_scenario.get_short_name(),
                                key=functional_16s_scenario.id,
                                material_icon='description'
                            )

                            # Sub-analysis items under 16S
                            ggpicrust_item = StreamlitTreeMenuItem(
                                label="9) 16s ggpicrust",
                                key=f"{ubiome_state.TAG_16S_VISU}_{functional_16s_scenario.id}",
                                material_icon='insights'
                            )
                            if ubiome_state.TAG_16S_VISU in scenarios_by_step:
                                for ggpicrust_scenario in scenarios_by_step[ubiome_state.TAG_16S_VISU]:
                                    # Check if this visu scenario belongs to this 16s scenario
                                    ggpicrust_entity_tag_list = EntityTagList.find_by_entity(TagEntityType.SCENARIO, ggpicrust_scenario.id)
                                    ggpicrust_feature_id_tags = ggpicrust_entity_tag_list.get_tags_by_key(ubiome_state.TAG_FEATURE_INFERENCE_ID)
                                    functional_16s_feature_id_tags = EntityTagList.find_by_entity(TagEntityType.SCENARIO, functional_16s_scenario.id).get_tags_by_key(ubiome_state.TAG_FEATURE_INFERENCE_ID)

                                    if (ggpicrust_feature_id_tags and functional_16s_feature_id_tags and
                                        ggpicrust_feature_id_tags[0].to_simple_tag().value == functional_16s_feature_id_tags[0].to_simple_tag().value):
                                        ggpicrust_child_item = StreamlitTreeMenuItem(
                                            label=ggpicrust_scenario.get_short_name(),
                                            key=ggpicrust_scenario.id,
                                            material_icon='description'
                                        )
                                        ggpicrust_item.add_children([ggpicrust_child_item])

                            s16_item.add_children([s16_item_child])

                scenario_item.add_children([rarefaction_item, taxonomy_item, s16_item])
                feature_item.add_children([scenario_item])

        button_menu.add_item(feature_item)

    return button_menu, key_metadata

def get_status_emoji(status: ScenarioStatus) -> str:
    """Return appropriate emoji for scenario status"""
    emoji_map = {
        ScenarioStatus.DRAFT: "📝",
        ScenarioStatus.IN_QUEUE: "⏳",
        ScenarioStatus.WAITING_FOR_CLI_PROCESS: "⏸️",
        ScenarioStatus.RUNNING: "🔄",
        ScenarioStatus.SUCCESS: "✅",
        ScenarioStatus.ERROR: "❌",
        ScenarioStatus.PARTIALLY_RUN: "⚠️"
    }
    return emoji_map.get(status, "")

def render_analysis_page():
    router = StreamlitRouter.load_from_session()
    ubiome_state = State()
    # Create two columns
    left_col, right_col = st.columns([1, 4])

    with left_col:
        # Button to go home
        if st.button("Home", use_container_width=True, icon=":material/home:", type="primary"):
            router = StreamlitRouter.load_from_session()
            router.navigate("first-page")


    selected_analysis = ubiome_state.get_selected_analysis()
    if not selected_analysis:
        return st.error("No analysis selected. Please select an analysis from the first page.")

    # Get analysis name from scenario tag
    entity_tag_list = EntityTagList.find_by_entity(TagEntityType.SCENARIO, selected_analysis.id)
    tag_analysis_name = entity_tag_list.get_tags_by_key(ubiome_state.TAG_ANALYSIS_NAME)[0].to_simple_tag()
    analysis_name = tag_analysis_name.value

    # Get ubiome pipeline id from scenario tag
    tag_ubiome_pipeline_id = entity_tag_list.get_tags_by_key(ubiome_state.TAG_UBIOME_PIPELINE_ID)[0].to_simple_tag()
    ubiome_pipeline_id = tag_ubiome_pipeline_id.value

    if selected_analysis.status != ScenarioStatus.SUCCESS:
        with right_col:
            st.info("The first step for this analysis is not completed successfully. Please check back later.")
        return

    # Get fastq and metadata table
    scenario_proxy = ScenarioProxy.from_existing_scenario(selected_analysis.id)
    # Retrieve the protocol
    protocol_proxy: ProtocolProxy = scenario_proxy.get_protocol()

    # Retrieve outputs
    # Fastq
    file_fastq : Folder = protocol_proxy.get_process('metadata_process').get_input('fastq_folder')
    ubiome_state.set_resource_id_fastq(file_fastq.get_model_id())

    ##### Metadata table
    metadata_updated = search_updated_metadata_table(ubiome_state)

    if metadata_updated:
        ubiome_state.set_resource_id_metadata_table(metadata_updated.get_model_id())
    else : # Get the table from initial scenario
        metadata_output : File = protocol_proxy.get_process('metadata_process').get_output('metadata_table')
        ubiome_state.set_resource_id_metadata_table(metadata_output.get_model_id())

    # Left column - Analysis workflow tree
    with left_col:

        st.write(f"**Analysis:** {analysis_name}")

        # Build and render the analysis tree menu, and keep the key of the first element
        tree_menu, key_metadata = build_analysis_tree_menu(ubiome_state, ubiome_pipeline_id)

        # Set default selected item to metadata table
        tree_menu.set_default_selected_item(key_metadata)

        # Save in session_state the tree_menu
        ubiome_state.set_tree_menu_object(tree_menu)

        # Render the tree menu
        selected_item = tree_menu.render()

        if selected_item is not None:
            # Handle tree item selection
            item_key = selected_item.key


            # If it's a scenario ID, update the selected scenario
            selected_scenario_new = Scenario.get_by_id(item_key)

            if selected_scenario_new:
                ubiome_state.set_selected_scenario(selected_scenario_new)

                entity_tag_list = EntityTagList.find_by_entity(TagEntityType.SCENARIO, selected_scenario_new.id)
                tag_step_name = entity_tag_list.get_tags_by_key(ubiome_state.TAG_UBIOME)[0].to_simple_tag()
                ubiome_state.set_step_pipeline(tag_step_name.value)

            else:
                ubiome_state.set_selected_scenario(None)
                ubiome_state.set_step_pipeline(item_key)

    # Right column - Analysis details
    with right_col:
        # Add vertical line to separate the two columns
        style = """
        [CLASS_NAME] {
            border-left: 2px solid #ccc;
            min-height: 100vh;
            padding-left: 20px !important;
        }
        """
        with StreamlitContainers.container_with_style('analysis-container', style):

            is_scenario = True if ubiome_state.get_selected_scenario() else False

            if is_scenario:
                selected_scenario : Scenario = ubiome_state.get_selected_scenario()

                # Write the status of the scenario at the top right
                col_empty, col_status = StreamlitContainers.columns_with_fit_content(
                        key="container_status",
                        cols=[1, 'fit-content'], vertical_align_items='center')

                with col_status:
                    status_emoji = get_status_emoji(selected_scenario.status)
                    st.write(f"**Status:** {status_emoji} {selected_scenario.status.value}")
            else :
                selected_scenario = None

            if ubiome_state.get_step_pipeline() == ubiome_state.TAG_METADATA:
                # Render metadata table
                render_metadata_step(selected_scenario, ubiome_state)
            elif ubiome_state.get_step_pipeline() == ubiome_state.TAG_QC:
                render_qc_step(selected_scenario, ubiome_state)
            elif ubiome_state.get_step_pipeline() == ubiome_state.TAG_FEATURE_INFERENCE:
                render_feature_inference_step(selected_scenario, ubiome_state)
            elif ubiome_state.get_step_pipeline().startswith(ubiome_state.TAG_RAREFACTION):
                render_rarefaction_step(selected_scenario, ubiome_state)
            elif ubiome_state.get_step_pipeline().startswith(ubiome_state.TAG_TAXONOMY):
                render_taxonomy_step(selected_scenario, ubiome_state)
            elif ubiome_state.get_step_pipeline().startswith(ubiome_state.TAG_PCOA_DIVERSITY):
                render_pcoa_step(selected_scenario, ubiome_state)
            elif ubiome_state.get_step_pipeline().startswith(ubiome_state.TAG_ANCOM):
                render_ancom_step(selected_scenario, ubiome_state)
            elif ubiome_state.get_step_pipeline().startswith(ubiome_state.TAG_DB_ANNOTATOR):
                render_db_annotator_step(selected_scenario, ubiome_state)
            elif ubiome_state.get_step_pipeline().startswith(ubiome_state.TAG_16S_VISU):
                render_16s_visu_step(selected_scenario, ubiome_state)
            elif ubiome_state.get_step_pipeline().startswith(ubiome_state.TAG_16S):
                render_16s_step(selected_scenario, ubiome_state)
