import os
import streamlit as st
from typing import List
from state import State
from gws_core.streamlit import StreamlitContainers, StreamlitResourceSelect, StreamlitRouter, StreamlitTreeMenu, StreamlitTreeMenuItem
from gws_ubiome.ubiome_dashboard._ubiome_dashboard.ubiome_config import UbiomeConfig
from gws_ubiome.ubiome_dashboard._ubiome_dashboard.functions_steps import render_metadata_step, render_qc_step, render_feature_inference_step
import pandas as pd
from gws_core import TableImporter, Tag, ResourceModel, ResourceOrigin, Settings, File, Folder, StringHelper, InputTask, ProcessProxy, ScenarioSearchBuilder, TagValueModel, Scenario, ScenarioStatus, ScenarioProxy, ProtocolProxy, ScenarioCreationType
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
    entity_tag_list = EntityTagList.find_by_entity(TagEntityType.SCENARIO, metadata_scenario.id)
    sequencing_type_tag = entity_tag_list.get_tags_by_key(ubiome_state.TAG_SEQUENCING_TYPE)[0].to_simple_tag()
    sequencing_type = sequencing_type_tag.value
    ubiome_state.set_sequencing_type(sequencing_type)

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
                    key=scenario.id, # TODO change the key to have the correct key - same for other steps
                    material_icon='description'
                )

                # 4) Rarefaction sub-step
                rarefaction_item = StreamlitTreeMenuItem(
                    label="4) Rarefaction",
                    key=f"rarefaction_{scenario.id}",
                    material_icon='trending_down'
                )
                if "Rarefaction" in scenarios_by_step:
                    for rare_scenario in scenarios_by_step["Rarefaction"]:
                        rare_item = StreamlitTreeMenuItem(
                            label=rare_scenario.get_short_name(),
                            key=rare_scenario.id,
                            material_icon='description'
                        )
                        rarefaction_item.add_children([rare_item])

                # 4) Taxonomy sub-step
                taxonomy_item = StreamlitTreeMenuItem(
                    label="4) Taxonomy",
                    key=f"taxonomy_{scenario.id}",
                    material_icon='account_tree'
                )
                if "Taxonomy" in scenarios_by_step:
                    for tax_scenario in scenarios_by_step["Taxonomy"]:
                        tax_item = StreamlitTreeMenuItem(
                            label=tax_scenario.get_short_name(),
                            key=tax_scenario.id,
                            material_icon='description'
                        )

                        # Sub-analysis items under taxonomy
                        pcoa_item = StreamlitTreeMenuItem(
                            label="5) PCOA diversity",
                            key=f"pcoa_{tax_scenario.id}",
                            material_icon='scatter_plot'
                        )
                        ancom_item = StreamlitTreeMenuItem(
                            label="6) ANCOM",
                            key=f"ancom_{tax_scenario.id}",
                            material_icon='biotech'
                        )
                        taxa_comp_item = StreamlitTreeMenuItem(
                            label="5) Taxa Composition",
                            key=f"taxa_comp_{tax_scenario.id}",
                            material_icon='pie_chart'
                        )

                        tax_item.add_children([pcoa_item, ancom_item, taxa_comp_item])
                        taxonomy_item.add_children([tax_item])

                # 8) 16S sub-step
                s16_item = StreamlitTreeMenuItem(
                    label="8) 16S",
                    key=f"16s_{scenario.id}",
                    material_icon='dna'
                )
                if "16S" in scenarios_by_step or "ggpicrust" in scenarios_by_step:
                    ggpicrust_item = StreamlitTreeMenuItem(
                        label="16s ggpicrust",
                        key=f"ggpicrust_{scenario.id}",
                        material_icon='insights'
                    )
                    s16_item.add_children([ggpicrust_item])

                scenario_item.add_children([rarefaction_item, taxonomy_item, s16_item])
                feature_item.add_children([scenario_item])

        button_menu.add_item(feature_item)

    # Rapport - final step
    rapport_item = StreamlitTreeMenuItem(
        label="Rapport",
        key="rapport",
        material_icon='description'
    )
    button_menu.add_item(rapport_item)

    return button_menu, key_metadata

def render_analysis_page():
    ubiome_config = UbiomeConfig.get_instance()
    router = StreamlitRouter.load_from_session()
    ubiome_state = State()

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

    #TODO ajouter un warning ou faire en sorte que ça marche même quand le scénario est en cours

    # Get fastq and metadata table
    scenario_proxy = ScenarioProxy.from_existing_scenario(selected_analysis.id)
    # Retrieve the protocol
    protocol_proxy: ProtocolProxy = scenario_proxy.get_protocol()

    # Retrieve outputs
    # Fastq
    file_fastq : Folder = protocol_proxy.get_process('metadata_process').get_input('fastq_folder')
    ubiome_state.set_resource_id_fastq(file_fastq.get_model_id())

    # Metadata table
    metadata_table_resource_search = ResourceModel.select().where(
        (Tag.key == ubiome_state.TAG_UBIOME_PIPELINE_ID) &
        (Tag.value == ubiome_state.get_current_ubiome_pipeline_id()) &
        (Tag.key == ubiome_state.TAG_UBIOME) &
        (Tag.value == ubiome_state.TAG_METADATA_UPDATED) &
        (ResourceModel.resource_typing_name.contains('File'))  # Search for File type resources
    )

    metadata_updated = metadata_table_resource_search.first()
    if metadata_updated:
        ubiome_state.set_resource_id_metadata_table(metadata_updated.id)
    else : # Get the table from initial scenario
        metadata_output : Folder = protocol_proxy.get_process('metadata_process').get_output('metadata_table')
        ubiome_state.set_resource_id_metadata_table(metadata_output.get_model_id())

    # Create two columns
    left_col, right_col = st.columns([1, 4])

    # Left column - Analysis workflow tree
    with left_col:
        # Button to go home
        if st.button("Home", use_container_width=True, icon=":material/home:", type="primary"):
            router = StreamlitRouter.load_from_session()
            router.navigate("first-page")

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
                    st.write(f"**Status:** {selected_scenario.status.value}")

                st.write(ubiome_state.get_selected_scenario().get_short_name())
            else :
                selected_scenario = None

            if ubiome_state.get_step_pipeline() == ubiome_state.TAG_METADATA:
                # Render metadata table
                render_metadata_step(selected_scenario, ubiome_state)
            elif ubiome_state.get_step_pipeline() == ubiome_state.TAG_QC:
                render_qc_step(selected_scenario, ubiome_state)
            elif ubiome_state.get_step_pipeline() == ubiome_state.TAG_FEATURE_INFERENCE:
                render_feature_inference_step(selected_scenario, ubiome_state)





