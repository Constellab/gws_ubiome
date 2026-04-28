import plotly.express as px
import streamlit as st
from gws_core import Scenario, ScenarioProxy, ScenarioStatus
from gws_gaia import PCoATrainer
from gws_streamlit_main import StreamlitTaskRunner

from ..functions_steps import (
    display_saved_scenario_actions,
    display_scenario_parameters,
    render_scenario_table,
)
from ..state import State
from ..ubiome_scenario_service import UbiomeScenarioService


@st.dialog("PCOA parameters")
def dialog_pcoa_params(ubiome_state: State):
    translate_service = ubiome_state.get_translate_service()
    st.text_input(
        translate_service.translate("pcoa_scenario_name"),
        placeholder=translate_service.translate("enter_pcoa_name"),
        value=f"{ubiome_state.get_current_analysis_name()} - PCOA",
        key=UbiomeScenarioService.PCOA_SCENARIO_NAME_INPUT_KEY,
    )
    taxonomy_scenario_id = ubiome_state.get_current_taxonomy_scenario_id_parent()

    # Get available diversity tables from taxonomy results
    beta_diversity_tables = UbiomeScenarioService.get_beta_diversity_tables(taxonomy_scenario_id)

    # Let user select which diversity table to use
    st.selectbox(
        translate_service.translate("select_diversity_table_pcoa"),
        options=list(beta_diversity_tables.keys()),
        key=UbiomeScenarioService.PCOA_DIVERSITY_TABLE_SELECT_KEY,
    )

    # Standard PCOA configuration
    form_config = StreamlitTaskRunner(PCoATrainer)
    form_config.generate_config_form_without_run(
        session_state_key=UbiomeScenarioService.PCOA_CONFIG_KEY,
        default_config_values=PCoATrainer.config_specs.get_default_values(),
        is_default_config_valid=PCoATrainer.config_specs.mandatory_values_are_set(
            PCoATrainer.config_specs.get_default_values()
        ),
    )

    # Add both Save and Run buttons
    col1, col2 = st.columns(2)

    with col1:
        save_clicked = st.button(
            translate_service.translate("save_pcoa"),
            width="stretch",
            icon=":material/save:",
            key="button_pcoa_save",
        )

    with col2:
        run_clicked = st.button(
            translate_service.translate("run_pcoa"),
            width="stretch",
            icon=":material/play_arrow:",
            key="button_pcoa_run",
        )

    if save_clicked or run_clicked:
        if not ubiome_state.get_pcoa_config()["is_valid"]:
            st.warning(translate_service.translate("fill_mandatory_fields"))
            return

        selected_table_name = ubiome_state.get_pcoa_diversity_table_select()
        if not selected_table_name:
            st.warning(translate_service.translate("select_diversity_table_required"))
            return

        diversity_table_model_id = beta_diversity_tables[selected_table_name].get_model_id()
        scenario = UbiomeScenarioService.create_pcoa_scenario(
            folder_id=ubiome_state.get_selected_folder_id(),
            fastq_name=ubiome_state.get_current_fastq_name(),
            analysis_name=ubiome_state.get_current_analysis_name(),
            pipeline_id=ubiome_state.get_current_ubiome_pipeline_id(),
            title=ubiome_state.get_scenario_user_name(
                UbiomeScenarioService.PCOA_SCENARIO_NAME_INPUT_KEY
            ),
            config=ubiome_state.get_pcoa_config()["config"],
            feature_scenario_id=ubiome_state.get_current_feature_scenario_id_parent(),
            taxonomy_scenario_id=taxonomy_scenario_id,
            diversity_table_model_id=diversity_table_model_id,
        )
        if run_clicked:
            scenario.add_to_queue()
            ubiome_state.reset_tree_analysis()
            ubiome_state.set_tree_default_item(scenario.get_model_id())
        st.rerun()


def render_pcoa_step(selected_scenario: Scenario, ubiome_state: State) -> None:
    translate_service = ubiome_state.get_translate_service()

    # Get the selected tree menu item to determine which taxonomy scenario is selected
    tree_menu = ubiome_state.get_tree_menu_object()
    selected_item = tree_menu.get_selected_item()
    if selected_item.key.startswith(UbiomeScenarioService.TAG_PCOA_DIVERSITY):
        taxonomy_scenario_parent_id = ubiome_state.get_parent_taxonomy_scenario_from_step()
        ubiome_state.set_current_taxonomy_scenario_id_parent(taxonomy_scenario_parent_id.id)
        # Retrieve the feature inference scenario ID using the utility function
        feature_inference_id = ubiome_state.get_feature_inference_id_from_taxonomy_scenario(
            taxonomy_scenario_parent_id
        )
        ubiome_state.set_current_feature_scenario_id_parent(feature_inference_id)

    if not selected_scenario:
        if not ubiome_state.get_is_standalone():
            # On click, open a dialog to allow the user to select params of PCOA
            st.button(
                translate_service.translate("configure_new_pcoa_scenario"),
                icon=":material/edit:",
                width="content",
                on_click=lambda state=ubiome_state: dialog_pcoa_params(state),
            )

        # Display table of existing PCOA scenarios
        st.markdown(f"### {translate_service.translate('list_scenarios')}")

        list_scenario_pcoa = ubiome_state.get_scenario_step_pcoa()
        render_scenario_table(list_scenario_pcoa, "pcoa_process", "pcoa_grid", ubiome_state)
    else:
        # Display details about scenario PCOA
        st.markdown(f"##### {translate_service.translate('pcoa_scenario_results')}")
        display_scenario_parameters(selected_scenario, "pcoa_process", ubiome_state)

        if (
            selected_scenario.status == ScenarioStatus.DRAFT
            and not ubiome_state.get_is_standalone()
        ):
            display_saved_scenario_actions(selected_scenario, ubiome_state)

        scenario_proxy = ScenarioProxy.from_existing_scenario(selected_scenario.id)
        protocol_proxy = scenario_proxy.get_protocol()
        process = protocol_proxy.get_process("pcoa_process")
        st.write(f"Diversity Table: {process.get_input('distance_table').name}")

        # Display results if scenario is successful
        if selected_scenario.status != ScenarioStatus.SUCCESS:
            return

        scenario_proxy = ScenarioProxy.from_existing_scenario(selected_scenario.id)
        protocol_proxy = scenario_proxy.get_protocol()

        # Get PCOA results
        pcoa_result = protocol_proxy.get_process("pcoa_process").get_output("result")

        if pcoa_result:
            tab_plot, tab_table = st.tabs(
                [
                    translate_service.translate("2d_score_plot"),
                    translate_service.translate("tables"),
                ]
            )
            transformed_table = pcoa_result.get_transformed_table()
            variance_table = pcoa_result.get_variance_table()

            with tab_plot:
                # Manual plot creation
                if transformed_table and variance_table:
                    data = transformed_table.get_data()
                    variance_data = variance_table.get_data()

                    # Add sample names from index to the data for plotting
                    data_with_samples = data.copy()
                    data_with_samples["Sample"] = data.index

                    # Create scatter plot of PC1 vs PC2
                    fig = px.scatter(
                        data_with_samples,
                        x="PC1",
                        y="PC2",
                        color="Sample",
                        hover_name="Sample",  # Show sample name on hover
                        title=translate_service.translate("pcoa_2d_score_plot"),
                    )

                    # Update text position to be above the points
                    fig.update_traces(textposition="top center")

                    # Update axis labels with variance explained
                    pc1_var = variance_data.loc["PC1", "ExplainedVariance"] * 100
                    pc2_var = variance_data.loc["PC2", "ExplainedVariance"] * 100

                    fig.update_xaxes(title=f"PC1 ({pc1_var:.2f}%)")
                    fig.update_yaxes(title=f"PC2 ({pc2_var:.2f}%)")

                    fig.update_layout(
                        xaxis={
                            "showline": True,
                            "linecolor": "black",
                            "linewidth": 1,
                            "zeroline": False,
                        },
                        yaxis={"showline": True, "linecolor": "black", "linewidth": 1},
                    )

                    st.plotly_chart(fig)
            with tab_table:
                # Display the transformed data table
                if transformed_table:
                    st.dataframe(transformed_table.get_data())

                # Also show variance table
                st.markdown(f"##### {translate_service.translate('variance_explained')}")
                if variance_table:
                    st.dataframe(variance_table.get_data())
