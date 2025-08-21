import streamlit as st
from typing import List
from state import State
from gws_core.streamlit import StreamlitContainers, StreamlitResourceSelect, StreamlitRouter, StreamlitTreeMenu, StreamlitTreeMenuItem
from gws_ubiome.ubiome_dashboard._ubiome_dashboard.ubiome_config import UbiomeConfig
from gws_ubiome.ubiome_dashboard._ubiome_dashboard.functions_home import navigate_to_first_page
import pandas as pd
from gws_core import Tag, InputTask, ProcessProxy, ScenarioSearchBuilder, TagValueModel, Scenario, ScenarioStatus, ScenarioProxy, ProtocolProxy, ScenarioCreationType


# Check if steps are completed (have successful scenarios)
def has_successful_scenario(step_name, scenarios_by_step):
    if step_name not in scenarios_by_step:
        return False
    return any(s.status == ScenarioStatus.SUCCESS for s in scenarios_by_step[step_name])


def build_analysis_tree_menu(ubiome_state: State, analysis_name: str):
    """Build the tree menu for analysis workflow steps"""
    button_menu = StreamlitTreeMenu(key="analysis_tree_menu")

    analysis_name_parsed = Tag.parse_tag(analysis_name)

    # Get all scenarios for this analysis
    search_scenario_builder = ScenarioSearchBuilder() \
        .add_tag_filter(Tag(key=ubiome_state.TAG_ANALYSIS_NAME, value=analysis_name_parsed, auto_parse=True)) \
        .add_is_archived_filter(False)

    all_scenarios: List[Scenario] = search_scenario_builder.search_all()


    # Group scenarios by step type
    scenarios_by_step = {}
    for scenario in all_scenarios:
        step_name = scenario.get_short_name().split(" - ")[-1] if " - " in scenario.get_short_name() else "Unknown" # TODO récupérer la valeur du tag ubiome
        if step_name not in scenarios_by_step:
            scenarios_by_step[step_name] = []
        scenarios_by_step[step_name].append(scenario)



    # 1) Metadata table
    if "Metadata" in scenarios_by_step or True:  # Always show first step

        if "Metadata" in scenarios_by_step:
            # If a scenario exists
            key=scenario.id
        else:
            key = "metadata"
        metadata_item = StreamlitTreeMenuItem(
            label="1) Metadata table",
            key=key,
            material_icon='table_chart'
        )


        button_menu.add_item(metadata_item)

    # 2) QC - only if metadata is successful
    if has_successful_scenario("Metadata", scenarios_by_step) or "QC" in scenarios_by_step:

        if "QC" in scenarios_by_step:
            key = scenario.id
        else:
            key = "qc"
        qc_item = StreamlitTreeMenuItem(
            label="2) QC",
            key=key,
            material_icon='check_circle'
        )

        button_menu.add_item(qc_item)

    # 3) Feature inference - only if QC is successful
    if has_successful_scenario("QC", scenarios_by_step) or "Feature inference" in scenarios_by_step:
        feature_item = StreamlitTreeMenuItem(
            label="3) Feature inference",
            key="feature_inference",
            material_icon='analytics'
        )

        if "Feature inference" in scenarios_by_step:
            for scenario in scenarios_by_step["Feature inference"]:
                scenario_item = StreamlitTreeMenuItem(
                    label=scenario.get_short_name(),
                    key=scenario.id,
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

    return button_menu

def render_analysis_page():
    ubiome_config = UbiomeConfig.get_instance()
    router = StreamlitRouter.load_from_session()
    ubiome_state = State()

    selected_analysis = ubiome_state.get_selected_analysis()
    if not selected_analysis:
        return st.error("No analysis selected. Please select an analysis from the first page.")

    # Get analysis name from scenario
    analysis_name = selected_analysis.get_short_name().split(" - ")[0]

    # Create two columns
    left_col, right_col = st.columns([1, 4])

    # Left column - Analysis workflow tree
    with left_col:
        # Button to go home using config
        if ubiome_config.build_home_button():
            router.navigate("first-page")

        st.write(f"**Analysis:** {analysis_name}")

        # Build and render the analysis tree menu
        tree_menu = build_analysis_tree_menu(ubiome_state, analysis_name)

        # Render the tree menu
        selected_item = tree_menu.render()

        if selected_item is not None:
            # Handle tree item selection
            item_key = selected_item.key


            # If it's a scenario ID, update the selected scenario
            selected_scenario_new = Scenario.get_by_id(item_key)

            if selected_scenario_new:
                ubiome_state.set_selected_scenario(selected_scenario_new)
                ubiome_state.set_step_pipeline(selected_scenario_new.get_short_name().split(" - ")[-1]) # TODO get the tag

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
            st.write("Analysis Details")
            st.write("**Selected Step:**", ubiome_state.get_step_pipeline())


            if ubiome_state.get_selected_scenario():
                selected_scenario = ubiome_state.get_selected_scenario()

                # Write the status of the scenario at the top right
                col_empty, col_status = StreamlitContainers.columns_with_fit_content(
                        key="button_new",
                        cols=[1, 'fit-content'], vertical_align_items='center')

                with col_status:
                    st.write(f"**Status:** {selected_scenario.status}")

                st.write(ubiome_state.get_selected_scenario().get_short_name())





