import streamlit as st
from typing import List, Dict
from gws_ubiome.ubiome_dashboard._ubiome_dashboard_core.state import State
from gws_core import Settings, File, Folder,  Scenario, ScenarioStatus, ScenarioProxy, ProtocolProxy
from gws_ubiome.ubiome_dashboard._ubiome_dashboard_core.functions_steps import search_updated_metadata_table, get_status_emoji, get_status_prettify, build_scenarios_by_step_dict
from gws_core.streamlit import StreamlitContainers, StreamlitRouter, StreamlitTreeMenu, StreamlitTreeMenuItem
from gws_core.tag.tag_entity_type import TagEntityType
from gws_core.tag.entity_tag_list import EntityTagList

#Steps functions
from gws_ubiome.ubiome_dashboard._ubiome_dashboard_core.steps.metadata_step import render_metadata_step
from gws_ubiome.ubiome_dashboard._ubiome_dashboard_core.steps.qc_step import render_qc_step
from gws_ubiome.ubiome_dashboard._ubiome_dashboard_core.steps.multiqc_step import render_multiqc_step
from gws_ubiome.ubiome_dashboard._ubiome_dashboard_core.steps.feature_inference_step import render_feature_inference_step
from gws_ubiome.ubiome_dashboard._ubiome_dashboard_core.steps.rarefaction_step import render_rarefaction_step
from gws_ubiome.ubiome_dashboard._ubiome_dashboard_core.steps.taxonomy_step import render_taxonomy_step
from gws_ubiome.ubiome_dashboard._ubiome_dashboard_core.steps.pcoa_step import render_pcoa_step
from gws_ubiome.ubiome_dashboard._ubiome_dashboard_core.steps.ancom_step import render_ancom_step
from gws_ubiome.ubiome_dashboard._ubiome_dashboard_core.steps.db_annotator_step import render_db_annotator_step
from gws_ubiome.ubiome_dashboard._ubiome_dashboard_core.steps.functional_16s_step import render_16s_step
from gws_ubiome.ubiome_dashboard._ubiome_dashboard_core.steps.functional_16s_visu_step import render_16s_visu_step


# Check if steps are completed (have successful scenarios)
def has_successful_scenario(step_name : str, scenarios_by_step: Dict):
    if step_name not in scenarios_by_step:
        return False
    return any(s.status == ScenarioStatus.SUCCESS for s in scenarios_by_step[step_name])

# Helper function to get icon - check_circle if step has been run for specific parent, otherwise original icon
def get_step_icon(step_name: str, scenarios_by_step: Dict, list_scenarios: List[Scenario] = None) -> str:
    """Get icon for step - check_circle if step has scenarios, empty otherwise."""
    if step_name not in scenarios_by_step:
        return ''
    if not list_scenarios:
        return ''
    return 'check_circle'

def build_analysis_tree_menu(ubiome_state: State, ubiome_pipeline_id: str):
    """Build the tree menu for analysis workflow steps"""
    translate_service = ubiome_state.get_translate_service()
    button_menu = StreamlitTreeMenu(key=ubiome_state.TREE_ANALYSIS_KEY)

    # Build scenarios_by_step dictionary using helper function
    scenarios_by_step = build_scenarios_by_step_dict(ubiome_pipeline_id, ubiome_state)
    ubiome_state.set_scenarios_by_step_dict(scenarios_by_step)

    # Set in the state if data is single-end or paired-end
    metadata_scenario = ubiome_state.get_scenario_step_metadata()[0]
    scenario_metadata_proxy = ScenarioProxy.from_existing_scenario(metadata_scenario.id)
    config_sequencing_type = scenario_metadata_proxy.get_protocol().get_process('metadata_process').get_param('sequencing_type')
    ubiome_state.set_sequencing_type(config_sequencing_type)

    # 1) Metadata table
    scenario_metadata = None
    if ubiome_state.TAG_METADATA in scenarios_by_step:
        # If a scenario exists, use the first scenario's ID
        scenario_metadata = ubiome_state.get_scenario_step_metadata()
        key_metadata = scenario_metadata[0].id
    else:
        key_metadata = ubiome_state.TAG_METADATA

    # Show the default selected item if exist either show first step
    if ubiome_state.get_tree_default_item():
        key_default_item = ubiome_state.get_tree_default_item()
    else :
        key_default_item = key_metadata

    metadata_item = StreamlitTreeMenuItem(
        label=translate_service.translate("metadata_table"),
        key=key_metadata,
        material_icon=get_step_icon(ubiome_state.TAG_METADATA, scenarios_by_step, scenario_metadata)
    )

    button_menu.add_item(metadata_item)

    # 2) QC - only if metadata is successful
    if has_successful_scenario(ubiome_state.TAG_METADATA, scenarios_by_step) or ubiome_state.TAG_QC in scenarios_by_step:
        scenario_qc = None
        if ubiome_state.TAG_QC in scenarios_by_step:
            scenario_qc = ubiome_state.get_scenario_step_qc()
            # Use the first QC scenario's ID
            key_qc = scenario_qc[0].id
        else:
            key_qc = ubiome_state.TAG_QC
        qc_item = StreamlitTreeMenuItem(
            label=translate_service.translate("quality_control"),
            key=key_qc,
            material_icon=get_step_icon(ubiome_state.TAG_QC, scenarios_by_step, scenario_qc)
        )

        button_menu.add_item(qc_item)

    # MultiQC - only if QC is successful
    if has_successful_scenario(ubiome_state.TAG_QC, scenarios_by_step) or ubiome_state.TAG_MULTIQC in scenarios_by_step:
        scenario_multiqc = None
        if ubiome_state.TAG_MULTIQC in scenarios_by_step:
            scenario_multiqc = ubiome_state.get_scenario_step_multiqc()
            # Use the first MultiQC scenario's ID
            key_multiqc = scenario_multiqc[0].id
        else:
            key_multiqc = ubiome_state.TAG_MULTIQC
        multiqc_item = StreamlitTreeMenuItem(
            label="MultiQC",
            key=key_multiqc,
            material_icon=get_step_icon(ubiome_state.TAG_MULTIQC, scenarios_by_step, scenario_multiqc)
        )

        button_menu.add_item(multiqc_item)

    # 3) Feature inference - only if QC is successful
    if has_successful_scenario(ubiome_state.TAG_QC, scenarios_by_step) or ubiome_state.TAG_FEATURE_INFERENCE in scenarios_by_step:
        scenario_feature_inference = ubiome_state.get_scenario_step_feature_inference()
        feature_item = StreamlitTreeMenuItem(
            label="Feature inference",
            key=ubiome_state.TAG_FEATURE_INFERENCE,
            material_icon=get_step_icon(ubiome_state.TAG_FEATURE_INFERENCE, scenarios_by_step, scenario_feature_inference)
        )

        if ubiome_state.TAG_FEATURE_INFERENCE in scenarios_by_step:
            for scenario in scenarios_by_step[ubiome_state.TAG_FEATURE_INFERENCE]:
                scenario_item = StreamlitTreeMenuItem(
                    label=scenario.get_short_name(),
                    key=scenario.id,
                    material_icon='description'
                )
                if scenario.status == ScenarioStatus.SUCCESS:
                    # Get parent scenario ID for filtering sub-steps
                    scenario_feature_id_tags = EntityTagList.find_by_entity(TagEntityType.SCENARIO, scenario.id).get_tags_by_key(ubiome_state.TAG_FEATURE_INFERENCE_ID)
                    parent_feature_id = scenario_feature_id_tags[0].to_simple_tag().value if scenario_feature_id_tags else scenario.id

                    # 4) Rarefaction sub-step
                    rarefaction_scenarios = scenarios_by_step.get(ubiome_state.TAG_RAREFACTION, {}).get(parent_feature_id, [])
                    rarefaction_item = StreamlitTreeMenuItem(
                        label="Rarefaction",
                        key=f"{ubiome_state.TAG_RAREFACTION}_{scenario.id}",
                        material_icon=get_step_icon(ubiome_state.TAG_RAREFACTION, scenarios_by_step, rarefaction_scenarios)
                    )
                    for rare_scenario in rarefaction_scenarios:
                        rare_item = StreamlitTreeMenuItem(
                            label=rare_scenario.get_short_name(),
                            key=rare_scenario.id,
                            material_icon='description'
                        )
                        rarefaction_item.add_children([rare_item])

                    # 4) Taxonomy sub-step
                    taxonomy_scenarios = scenarios_by_step.get(ubiome_state.TAG_TAXONOMY, {}).get(parent_feature_id, [])
                    taxonomy_item = StreamlitTreeMenuItem(
                        label="Taxonomy",
                        key=f"{ubiome_state.TAG_TAXONOMY}_{scenario.id}",
                        material_icon=get_step_icon(ubiome_state.TAG_TAXONOMY, scenarios_by_step, taxonomy_scenarios)
                    )
                    for tax_scenario in taxonomy_scenarios:
                        tax_item = StreamlitTreeMenuItem(
                            label=tax_scenario.get_short_name(),
                            key=tax_scenario.id,
                            material_icon='description'
                        )
                        if tax_scenario.status == ScenarioStatus.SUCCESS:

                            # Get taxonomy scenario ID for sub-analysis filtering
                            scenario_taxonomy_id_tags = EntityTagList.find_by_entity(TagEntityType.SCENARIO, tax_scenario.id).get_tags_by_key(ubiome_state.TAG_TAXONOMY_ID)
                            parent_taxonomy_id = scenario_taxonomy_id_tags[0].to_simple_tag().value if scenario_taxonomy_id_tags else tax_scenario.id

                            # Sub-analysis items under taxonomy
                            pcoa_scenarios = scenarios_by_step.get(ubiome_state.TAG_PCOA_DIVERSITY, {}).get(parent_taxonomy_id, [])
                            pcoa_diversity_item = StreamlitTreeMenuItem(
                                label="PCOA diversity",
                                key=f"{ubiome_state.TAG_PCOA_DIVERSITY}_{tax_scenario.id}",
                                material_icon=get_step_icon(ubiome_state.TAG_PCOA_DIVERSITY, scenarios_by_step, pcoa_scenarios)
                            )
                            for pcoa_scenario in pcoa_scenarios:
                                pcoa_item = StreamlitTreeMenuItem(
                                    label=pcoa_scenario.get_short_name(),
                                    key=pcoa_scenario.id,
                                    material_icon='description'
                                )
                                pcoa_diversity_item.add_children([pcoa_item])

                            ancom_scenarios = scenarios_by_step.get(ubiome_state.TAG_ANCOM, {}).get(parent_taxonomy_id, [])
                            ancom_item = StreamlitTreeMenuItem(
                                label="ANCOM",
                                key=f"{ubiome_state.TAG_ANCOM}_{tax_scenario.id}",
                                material_icon=get_step_icon(ubiome_state.TAG_ANCOM, scenarios_by_step, ancom_scenarios)
                            )
                            for ancom_scenario in ancom_scenarios:
                                ancom_item_child = StreamlitTreeMenuItem(
                                    label=ancom_scenario.get_short_name(),
                                    key=ancom_scenario.id,
                                    material_icon='description'
                                )
                                ancom_item.add_children([ancom_item_child])

                            db_scenarios = scenarios_by_step.get(ubiome_state.TAG_DB_ANNOTATOR, {}).get(parent_taxonomy_id, [])
                            taxa_comp_item = StreamlitTreeMenuItem(
                                label="Taxa Composition",
                                key=f"{ubiome_state.TAG_DB_ANNOTATOR}_{tax_scenario.id}",
                                material_icon=get_step_icon(ubiome_state.TAG_DB_ANNOTATOR, scenarios_by_step, db_scenarios)
                            )
                            for db_scenario in db_scenarios:
                                db_item = StreamlitTreeMenuItem(
                                    label=db_scenario.get_short_name(),
                                    key=db_scenario.id,
                                    material_icon='description'
                                )
                                taxa_comp_item.add_children([db_item])

                            tax_item.add_children([pcoa_diversity_item, ancom_item, taxa_comp_item])
                        taxonomy_item.add_children([tax_item])

                    # 8) 16S sub-step
                    s16_scenarios = scenarios_by_step.get(ubiome_state.TAG_16S, {}).get(parent_feature_id, [])
                    s16_item = StreamlitTreeMenuItem(
                        label="16s Functional abundances prediction",
                        key=f"{ubiome_state.TAG_16S}_{scenario.id}",
                        material_icon=get_step_icon(ubiome_state.TAG_16S, scenarios_by_step, s16_scenarios)
                    )
                    for functional_16s_scenario in s16_scenarios:
                        s16_item_child = StreamlitTreeMenuItem(
                            label=functional_16s_scenario.get_short_name(),
                            key=functional_16s_scenario.id,
                            material_icon='description'
                        )
                        if functional_16s_scenario.status == ScenarioStatus.SUCCESS:

                            # Sub-analysis items under 16S
                            s16_visu_scenarios = scenarios_by_step.get(ubiome_state.TAG_16S_VISU, {}).get(parent_feature_id, [])
                            ggpicrust_item = StreamlitTreeMenuItem(
                                label="16s Functional abundances visualisation",
                                key=f"{ubiome_state.TAG_16S_VISU}_{functional_16s_scenario.id}",
                                material_icon=get_step_icon(ubiome_state.TAG_16S_VISU, scenarios_by_step, s16_visu_scenarios)
                            )
                            for ggpicrust_scenario in s16_visu_scenarios:
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

    return button_menu, key_default_item

def render_analysis_page(ubiome_state : State):
    style = """
    [CLASS_NAME] {
        padding: 40px;
    }
    """

    with StreamlitContainers.container_full_min_height('container-center_analysis_page',
                additional_style=style):

        translate_service = ubiome_state.get_translate_service()
        router = StreamlitRouter.load_from_session()
        # Create two columns
        left_col, right_col = st.columns([1, 4])

        with left_col:
            # Button to go home
            if st.button(translate_service.translate("recipes"), width="stretch", icon=":material/home:", type="primary"):
                # Reset the state of selected tree default item
                ubiome_state.set_tree_default_item(None)
                router = StreamlitRouter.load_from_session()
                router.navigate("first-page")


        selected_analysis = ubiome_state.get_selected_analysis()
        if not selected_analysis:
            return st.error(translate_service.translate("no_analysis_selected"))

        # Get analysis name from scenario tag
        entity_tag_list = EntityTagList.find_by_entity(TagEntityType.SCENARIO, selected_analysis.id)
        tag_analysis_name = entity_tag_list.get_tags_by_key(ubiome_state.TAG_ANALYSIS_NAME)[0].to_simple_tag()
        analysis_name = tag_analysis_name.value

        # Get ubiome pipeline id from scenario tag
        tag_ubiome_pipeline_id = entity_tag_list.get_tags_by_key(ubiome_state.TAG_UBIOME_PIPELINE_ID)[0].to_simple_tag()
        ubiome_pipeline_id = tag_ubiome_pipeline_id.value

        # Get folder from scenario folder
        ubiome_state.set_selected_folder_id(selected_analysis.folder.id if selected_analysis.folder else None)

        if selected_analysis.status != ScenarioStatus.SUCCESS:
            if selected_analysis.status in [ScenarioStatus.RUNNING, ScenarioStatus.DRAFT, ScenarioStatus.WAITING_FOR_CLI_PROCESS, ScenarioStatus.IN_QUEUE, ScenarioStatus.PARTIALLY_RUN]:
                message = translate_service.translate("analysis_still_running")
            else:
                message = translate_service.translate("analysis_not_completed")
            with right_col:
                st.info(message)
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

            st.write(f"**{translate_service.translate('recipe')}:** {analysis_name}")

            # Build and render the analysis tree menu, and keep the key of the first element
            tree_menu, key_default_item = build_analysis_tree_menu(ubiome_state, ubiome_pipeline_id)

            tree_menu.set_default_selected_item(key_default_item)

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
                    col_title, col_status, col_refresh= StreamlitContainers.columns_with_fit_content(
                            key="container_status",
                            cols=[1, 'fit-content', 'fit-content'], vertical_align_items='center')
                    with col_title:
                        st.markdown(f"#### {selected_scenario.get_short_name()}")
                    with col_status:
                        status_emoji = get_status_emoji(selected_scenario.status)
                        st.markdown(f"#### **{translate_service.translate('status')}:** {status_emoji} {get_status_prettify(selected_scenario.status)}")
                        # Add a button to redirect to the scenario page
                        virtual_host = Settings.get_instance().get_virtual_host()
                        if Settings.get_instance().is_prod_mode():
                            lab_mode = "lab"
                        else:
                            lab_mode = "dev-lab"
                        if not ubiome_state.get_is_standalone():
                            st.link_button(translate_service.translate("view_scenario"), f"https://{lab_mode}.{virtual_host}/app/scenario/{selected_scenario.id}", icon=":material/open_in_new:")
                    with col_refresh:
                        # If the scenario status is running or in queue, add a refresh button to refresh the page
                        if selected_scenario.status in [ScenarioStatus.RUNNING, ScenarioStatus.WAITING_FOR_CLI_PROCESS, ScenarioStatus.IN_QUEUE]:
                            if st.button(translate_service.translate("refresh"), icon=":material/refresh:", width="stretch"):
                                ubiome_state.set_tree_default_item(selected_scenario.id)
                                st.rerun()
                else :
                    selected_scenario = None

                if ubiome_state.get_step_pipeline() == ubiome_state.TAG_METADATA:
                    # Render metadata table
                    render_metadata_step(selected_scenario, ubiome_state)
                elif ubiome_state.get_step_pipeline() == ubiome_state.TAG_QC:
                    render_qc_step(selected_scenario, ubiome_state)
                elif ubiome_state.get_step_pipeline() == ubiome_state.TAG_MULTIQC:
                    render_multiqc_step(selected_scenario, ubiome_state)
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
