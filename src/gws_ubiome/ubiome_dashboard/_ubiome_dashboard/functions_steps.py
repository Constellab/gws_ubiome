import streamlit as st
import pandas as pd
from gws_core import Scenario, ScenarioProxy, ProtocolProxy, File, TableImporter
from gws_core.streamlit import StreamlitResourceSelect, StreamlitRouter


def render_metadata_step(selected_scenario: Scenario) -> None:
    scenario_proxy = ScenarioProxy.from_existing_scenario(selected_scenario.id)
    # Retrieve the protocol
    protocol_proxy: ProtocolProxy = scenario_proxy.get_protocol()

    # Retrieve outputs

    # Quality check
    file_metadata : File = protocol_proxy.get_process('metadata_process').get_output('metadata_table')
    # Import the file with Table importer
    table_metadata = TableImporter.call(file_metadata)
    df_metadata = table_metadata.get_data()
    st.dataframe(df_metadata, use_container_width=True)


def render_qc_step(selected_scenario: Scenario) -> None:
    pass

def render_feature_inference_step(selected_scenario: Scenario) -> None:
    pass