import os

import streamlit as st
from gws_core import (
    ResourceModel,
    Scenario,
    ScenarioProxy,
    ScenarioStatus,
    TableImporter,
)
from gws_streamlit_main import StreamlitTaskRunner
from gws_ubiome import Ggpicrust2FunctionalAnalysis

from ..functions_steps import (
    display_saved_scenario_actions,
    display_scenario_parameters,
    render_scenario_table,
)
from ..state import State
from ..ubiome_scenario_service import UbiomeScenarioService


@st.dialog("16S Visualization parameters")
def dialog_16s_visu_params(ubiome_state: State):
    translate_service = ubiome_state.get_translate_service()
    st.text_input(
        translate_service.translate("16s_visualization_scenario_name"),
        placeholder=translate_service.translate("enter_16s_visualization_name"),
        value=f"{ubiome_state.get_current_analysis_name()} - 16S Visualization",
        key=UbiomeScenarioService.FUNCTIONAL_ANALYSIS_VISU_SCENARIO_NAME_INPUT_KEY,
    )
    # Show metadata file preview
    metadata_table = ResourceModel.get_by_id(ubiome_state.get_resource_id_metadata_table())
    metadata_file = metadata_table.get_resource()

    table_metadata = TableImporter.call(metadata_file)
    df_metadata = table_metadata.get_data()

    st.markdown(f"##### {translate_service.translate('reminder_metadata_columns')}")
    if metadata_table:
        # Display only column names
        st.write(", ".join(df_metadata.columns.tolist()))

    form_config = StreamlitTaskRunner(Ggpicrust2FunctionalAnalysis)
    default_config = Ggpicrust2FunctionalAnalysis.config_specs.get_default_values()
    default_config["Round_digit"] = True
    form_config.generate_config_form_without_run(
        session_state_key=UbiomeScenarioService.FUNCTIONAL_ANALYSIS_VISU_CONFIG_KEY,
        default_config_values=default_config,
        is_default_config_valid=Ggpicrust2FunctionalAnalysis.config_specs.mandatory_values_are_set(
            default_config
        ),
    )

    col1, col2 = st.columns(2)

    with col1:
        save_clicked = st.button(
            translate_service.translate("save_16s_visualization"),
            width="stretch",
            icon=":material/save:",
            key="button_16s_visu_save",
        )

    with col2:
        run_clicked = st.button(
            translate_service.translate("run_16s_visualization"),
            width="stretch",
            icon=":material/play_arrow:",
            key="button_16s_visu_run",
        )

    if save_clicked or run_clicked:
        if not ubiome_state.get_functional_analysis_visu_config()["is_valid"]:
            st.warning(translate_service.translate("fill_mandatory_fields"))
            return

        scenario = UbiomeScenarioService.create_16s_visu_scenario(
            folder_id=ubiome_state.get_selected_folder_id(),
            fastq_name=ubiome_state.get_current_fastq_name(),
            analysis_name=ubiome_state.get_current_analysis_name(),
            pipeline_id=ubiome_state.get_current_ubiome_pipeline_id(),
            title=ubiome_state.get_scenario_user_name(
                UbiomeScenarioService.FUNCTIONAL_ANALYSIS_VISU_SCENARIO_NAME_INPUT_KEY
            ),
            config=ubiome_state.get_functional_analysis_visu_config()["config"],
            feature_scenario_id=ubiome_state.get_current_feature_scenario_id_parent(),
            functional_scenario_id=ubiome_state.get_current_16s_scenario_id_parent(),
            metadata_resource_id=ubiome_state.get_resource_id_metadata_table(),
        )
        if run_clicked:
            scenario.add_to_queue()
            ubiome_state.reset_tree_analysis()
            ubiome_state.set_tree_default_item(scenario.get_model_id())

        st.rerun()


def render_16s_visu_step(selected_scenario: Scenario, ubiome_state: State) -> None:
    translate_service = ubiome_state.get_translate_service()

    # Get the selected tree menu item to determine which 16s scenario is selected
    tree_menu = ubiome_state.get_tree_menu_object()
    selected_item = tree_menu.get_selected_item()
    if selected_item.key.startswith(UbiomeScenarioService.TAG_16S_VISU):
        functional_scenario_parent_id = ubiome_state.get_parent_16s_scenario_id_from_step()
        ubiome_state.set_current_16s_scenario_id_parent(functional_scenario_parent_id)
        # Retrieve the feature inference scenario ID
        if functional_scenario_parent_id:
            feature_inference_id = ubiome_state.get_feature_inference_id_from_16s_scenario(
                functional_scenario_parent_id
            )
            ubiome_state.set_current_feature_scenario_id_parent(feature_inference_id)

    if not selected_scenario:
        # Check if we have a valid 16S functional analysis scenario to run visualization
        functional_scenario_id = ubiome_state.get_current_16s_scenario_id_parent()

        # Validate that the required KO metagenome file exists
        ko_file_available = False
        if functional_scenario_id:
            try:
                scenario_proxy_16s = ScenarioProxy.from_existing_scenario(functional_scenario_id)
                protocol_proxy_16s = scenario_proxy_16s.get_protocol()
                functional_result_folder = protocol_proxy_16s.get_process(
                    "functional_analysis_process"
                ).get_output("Folder_result")

                if functional_result_folder and os.path.exists(functional_result_folder.path):
                    ko_file_path = os.path.join(
                        functional_result_folder.path,
                        "KO_metagenome_out",
                        "pred_metagenome_unstrat.tsv.gz",
                    )
                    ko_file_available = os.path.exists(ko_file_path)
            except Exception:
                ko_file_available = False

        if not ko_file_available:
            st.warning(f"⚠️ **{translate_service.translate('cannot_run_16s_visualization')}**")
        elif not ubiome_state.get_is_standalone():
            # On click, open a dialog to allow the user to select params of 16S visualization
            st.button(
                translate_service.translate("configure_new_16s_visualization_scenario"),
                icon=":material/edit:",
                width="content",
                on_click=lambda state=ubiome_state: dialog_16s_visu_params(state),
            )

        # Display table of existing 16S Visualization scenarios
        st.markdown(f"### {translate_service.translate('list_scenarios')}")

        list_scenario_16s_visu = ubiome_state.get_scenario_step_16s_visu()
        render_scenario_table(
            list_scenario_16s_visu, "functional_visu_process", "16s_visu_grid", ubiome_state
        )
    else:
        # Display details about scenario 16S visualization
        st.markdown(f"##### {translate_service.translate('16s_visualization_scenario_results')}")
        display_scenario_parameters(selected_scenario, "functional_visu_process", ubiome_state)

        if (
            selected_scenario.status == ScenarioStatus.DRAFT
            and not ubiome_state.get_is_standalone()
        ):
            display_saved_scenario_actions(selected_scenario, ubiome_state)

        if selected_scenario.status != ScenarioStatus.SUCCESS:
            return

        # Display results if scenario is successful
        scenario_proxy = ScenarioProxy.from_existing_scenario(selected_scenario.id)
        protocol_proxy = scenario_proxy.get_protocol()

        resource_set_output = protocol_proxy.get_process("functional_visu_process").get_output(
            "resource_set"
        )

        if resource_set_output:
            resource_dict = resource_set_output.get_resources()

            metadata_summary = [
                res
                for k, res in resource_dict.items()
                if "diagnostic_per_contrast_counts" in k and k.endswith(".csv")
            ]

            # Build dicts keyed by pairwise comparison (e.g. "HC_vs_PD")
            analysis_tables_dict = {}
            for k, r in resource_dict.items():
                if "daa_annotated_results" in k and k.endswith(".csv"):
                    pairwise = k.replace("daa_annotated_results_", "", 1).removesuffix(".csv")
                    analysis_tables_dict[pairwise] = r

            error_bar_plots_dict = {}
            for k, r in resource_dict.items():
                if "pathway_errorbar" in k and k.endswith(".png"):
                    # Strip the prefix; the remainder may be "<pairwise>_<suffix>.png"
                    # The pairwise key is identified by matching against known analysis_tables keys.
                    remainder = k.replace("pathway_errorbar_", "", 1).removesuffix(".png")
                    matched_pairwise = next(
                        (
                            p
                            for p in analysis_tables_dict
                            if remainder == p or remainder.startswith(p + "_")
                        ),
                        remainder,
                    )
                    error_bar_plots_dict.setdefault(matched_pairwise, []).append(r)

            heatmap_plots_dict = {}
            for k, r in resource_dict.items():
                if "pathway_heatmap" in k and k.endswith(".png"):
                    remainder = k.replace("pathway_heatmap_", "", 1).removesuffix(".png")
                    matched_pairwise = next(
                        (
                            p
                            for p in analysis_tables_dict
                            if remainder == p or remainder.startswith(p + "_")
                        ),
                        remainder,
                    )
                    heatmap_plots_dict.setdefault(matched_pairwise, []).append(r)

        else:
            return

        pairwise_keys = list(analysis_tables_dict.keys())
        pairwise_display = [p.replace("_vs_", " vs ") for p in pairwise_keys]

        selected_display = st.selectbox(
            translate_service.translate("select_pairwise_comparison"),
            options=pairwise_display,
        )

        # Map the display label back to the raw key used in the dicts
        selected_pairwise = None
        if selected_display and pairwise_keys:
            idx = pairwise_display.index(selected_display)
            selected_pairwise = pairwise_keys[idx]

        tab_metadata, tab_pca, tab_tables, tab_error_bar, tab_heatmap = st.tabs(
            [
                translate_service.translate("metadata_summary"),
                translate_service.translate("pca_plot"),
                translate_service.translate("analysis_table"),
                translate_service.translate("error_bar_plots"),
                translate_service.translate("heatmap_plots"),
            ]
        )

        with tab_pca:
            # Display PCA plot
            st.markdown(f"##### {translate_service.translate('principal_component_analysis')}")
            plotly_result = protocol_proxy.get_process("functional_visu_process").get_output(
                "plotly_result"
            )
            if plotly_result:
                st.plotly_chart(plotly_result.get_figure())

        with tab_metadata:
            # Display metadata summary
            st.markdown(f"##### {translate_service.translate('metadata_summary')}")
            if metadata_summary:
                st.dataframe(metadata_summary[0].get_data())
            else:
                st.info(translate_service.translate("no_results_available"))

        with tab_tables:
            st.markdown(
                f"##### {translate_service.translate('differential_abundance_analysis_table')}"
            )
            if selected_pairwise and selected_pairwise in analysis_tables_dict:
                st.dataframe(analysis_tables_dict[selected_pairwise].get_data())
            else:
                st.info(translate_service.translate("no_results_available"))

        with tab_error_bar:
            st.markdown(f"##### {translate_service.translate('pathway_error_bar_plots')}")
            if selected_pairwise and selected_pairwise in error_bar_plots_dict:
                for plot in error_bar_plots_dict[selected_pairwise]:
                    st.image(plot.path)
            else:
                st.info(translate_service.translate("no_results_available"))

        with tab_heatmap:
            st.markdown(f"##### {translate_service.translate('pathway_heatmap_plots')}")
            if selected_pairwise and selected_pairwise in heatmap_plots_dict:
                for plot in heatmap_plots_dict[selected_pairwise]:
                    st.image(plot.path)
            else:
                st.info(translate_service.translate("no_results_available"))
