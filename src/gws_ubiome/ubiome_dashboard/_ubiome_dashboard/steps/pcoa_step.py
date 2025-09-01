import streamlit as st
import plotly.express as px
from state import State
from gws_core.streamlit import StreamlitAuthenticateUser, StreamlitTaskRunner
from gws_core import Scenario, ScenarioProxy, Tag, InputTask, Scenario, ScenarioStatus, ScenarioProxy
from gws_gaia import PCoATrainer
from gws_ubiome.ubiome_dashboard._ubiome_dashboard.functions_steps import create_base_scenario_with_tags, render_scenario_table, display_scenario_parameters

@st.dialog("PCOA parameters")
def dialog_pcoa_params(ubiome_state: State):
    st.text_input("PCOA scenario name:", placeholder="Enter PCOA scenario name", value=f"{ubiome_state.get_current_analysis_name()} - PCOA", key=ubiome_state.PCOA_SCENARIO_NAME_INPUT_KEY)
    taxonomy_scenario_id = ubiome_state.get_current_taxonomy_scenario_id_parent()

    # Get available diversity tables from taxonomy results
    scenario_proxy_tax = ScenarioProxy.from_existing_scenario(taxonomy_scenario_id)
    protocol_proxy_tax = scenario_proxy_tax.get_protocol()
    diversity_resource_set = protocol_proxy_tax.get_process('taxonomy_process').get_output('diversity_tables')

    resource_set_result_dict = diversity_resource_set.get_resources()
    # Keep only tables "beta diversity" not alpha
    beta_diversity_tables = {k: v for k, v in resource_set_result_dict.items() if "beta" in k.lower()}

    # Let user select which diversity table to use
    st.selectbox(
        "Select a diversity table for PCOA analysis:",
        options=list(beta_diversity_tables.keys()),
        key=ubiome_state.PCOA_DIVERSITY_TABLE_SELECT_KEY,
    )

    # Standard PCOA configuration
    form_config = StreamlitTaskRunner(PCoATrainer)
    form_config.generate_config_form_without_run(
        session_state_key=ubiome_state.PCOA_CONFIG_KEY,
        default_config_values=PCoATrainer.config_specs.get_default_values(),
        is_default_config_valid=PCoATrainer.config_specs.mandatory_values_are_set(
            PCoATrainer.config_specs.get_default_values())
    )

    if st.button("Run PCOA", use_container_width=True, icon=":material/play_arrow:", key="button_pcoa"):
        if not ubiome_state.get_pcoa_config()["is_valid"]:
            st.warning("Please fill all the mandatory fields.")
            return

        selected_table = ubiome_state.get_pcoa_diversity_table_select()
        if not selected_table:
            st.warning("Please select a diversity table.")
            return

        with StreamlitAuthenticateUser():
            scenario = create_base_scenario_with_tags(ubiome_state, ubiome_state.TAG_PCOA_DIVERSITY, ubiome_state.get_scenario_user_name(ubiome_state.PCOA_SCENARIO_NAME_INPUT_KEY))
            feature_scenario_id = ubiome_state.get_current_feature_scenario_id_parent()
            scenario.add_tag(Tag(ubiome_state.TAG_FEATURE_INFERENCE_ID, feature_scenario_id, is_propagable=False, auto_parse=True))
            scenario.add_tag(Tag(ubiome_state.TAG_TAXONOMY_ID, taxonomy_scenario_id, is_propagable=False, auto_parse=True))
            protocol = scenario.get_protocol()

            # Add PCOA process
            pcoa_process = protocol.add_process(PCoATrainer, 'pcoa_process',
                                              config_params=ubiome_state.get_pcoa_config()["config"])

            # Get the selected diversity table as input
            diversity_table = resource_set_result_dict[selected_table]

            # Create an input task for the selected diversity table
            diversity_table_resource = protocol.add_process(InputTask, 'diversity_table_resource',
                                                          {InputTask.config_name: diversity_table.get_model_id()})

            # Connect to PCOA process
            protocol.add_connector(out_port=diversity_table_resource >> 'resource',
                                 in_port=pcoa_process << 'distance_table')

            # Add outputs
            protocol.add_output('pcoa_result_output', pcoa_process >> 'result', flag_resource=False)

            scenario.add_to_queue()
            ubiome_state.reset_tree_analysis()
            ubiome_state.set_tree_default_item(scenario.get_model_id())
            st.rerun()


def render_pcoa_step(selected_scenario: Scenario, ubiome_state: State) -> None:
    # Get the selected tree menu item to determine which taxonomy scenario is selected
    tree_menu = ubiome_state.get_tree_menu_object()
    selected_item = tree_menu.get_selected_item()
    if selected_item.key.startswith(ubiome_state.TAG_PCOA_DIVERSITY):
        taxonomy_scenario_parent_id = ubiome_state.get_parent_taxonomy_scenario_from_step()
        ubiome_state.set_current_taxonomy_scenario_id_parent(taxonomy_scenario_parent_id)
        # Retrieve the feature inference scenario ID using the utility function
        feature_inference_id = ubiome_state.get_feature_inference_id_from_taxonomy_scenario(taxonomy_scenario_parent_id)
        ubiome_state.set_current_feature_scenario_id_parent(feature_inference_id)

    if not selected_scenario:
        if not ubiome_state.get_is_standalone():
            # On click, open a dialog to allow the user to select params of PCOA
            st.button("Run new PCOA", icon=":material/play_arrow:", use_container_width=False,
                        on_click=lambda state=ubiome_state: dialog_pcoa_params(state))

        # Display table of existing PCOA scenarios
        st.markdown("### Previous PCOA Analyses")

        list_scenario_pcoa = ubiome_state.get_scenario_step_pcoa()
        render_scenario_table(list_scenario_pcoa, 'pcoa_process', 'pcoa_grid', ubiome_state)
    else:
        # Display details about scenario PCOA
        st.markdown("##### PCOA Scenario Results")
        display_scenario_parameters(selected_scenario, 'pcoa_process')
        scenario_proxy = ScenarioProxy.from_existing_scenario(selected_scenario.id)
        protocol_proxy = scenario_proxy.get_protocol()
        process = protocol_proxy.get_process('pcoa_process')
        st.write(f"Diversity Table: {process.get_input('distance_table').name}")

        # Display results if scenario is successful
        if selected_scenario.status != ScenarioStatus.SUCCESS:
            return

        scenario_proxy = ScenarioProxy.from_existing_scenario(selected_scenario.id)
        protocol_proxy = scenario_proxy.get_protocol()

        # Get PCOA results
        pcoa_result = protocol_proxy.get_process('pcoa_process').get_output('result')

        if pcoa_result:
            tab_plot, tab_table = st.tabs(["2D Score Plot", "Tables"])
            transformed_table = pcoa_result.get_transformed_table()
            variance_table = pcoa_result.get_variance_table()

            with tab_plot:
                # Manual plot creation
                if transformed_table and variance_table:

                    data = transformed_table.get_data()
                    variance_data = variance_table.get_data()

                    # Create scatter plot of PC1 vs PC2
                    fig = px.scatter(
                        data,
                        x='PC1',
                        y='PC2',
                        title='PCOA - 2D Score Plot'
                    )

                    # Update axis labels with variance explained
                    pc1_var = variance_data.loc['PC1', 'ExplainedVariance'] * 100
                    pc2_var = variance_data.loc['PC2', 'ExplainedVariance'] * 100

                    fig.update_xaxes(title=f'PC1 ({pc1_var:.2f}%)')
                    fig.update_yaxes(title=f'PC2 ({pc2_var:.2f}%)')

                    fig.update_layout(
                        xaxis={
                            "showline": True,
                            "linecolor": 'black',
                            "linewidth": 1,
                            "zeroline": False
                        },
                        yaxis={
                            "showline": True,
                            "linecolor": 'black',
                            "linewidth": 1
                        })

                    st.plotly_chart(fig)
            with tab_table:
                # Display the transformed data table
                if transformed_table:
                    st.dataframe(transformed_table.get_data())

                # Also show variance table
                st.markdown("##### Variance Explained")
                if variance_table:
                    st.dataframe(variance_table.get_data())