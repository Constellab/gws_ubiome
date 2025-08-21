
import streamlit as st

from gws_core import Scenario

class State:
    """Class to manage the state of the app.
    """

    TAG_BRICK = "brick"
    TAG_UBIOME = "ubiome"
    TAG_METADATA = "metadata"
    TAG_FASTQ = "fastq_name"
    TAG_ANALYSIS_NAME = "analysis_name"
    SELECTED_SCENARIO_KEY = "selected_scenario"
    SELECTED_ANALYSIS_KEY = "selected_analysis"
    STEP_PIPELINE_KEY = "step_pipeline"

    @classmethod
    def set_selected_scenario(cls, scenario: Scenario):
        st.session_state[cls.SELECTED_SCENARIO_KEY] = scenario

    @classmethod
    def get_selected_scenario(cls) -> Scenario:
        return st.session_state.get(cls.SELECTED_SCENARIO_KEY)

    @classmethod
    def set_selected_analysis(cls, scenario: Scenario):
        st.session_state[cls.SELECTED_ANALYSIS_KEY] = scenario

    @classmethod
    def get_selected_analysis(cls) -> Scenario:
        return st.session_state.get(cls.SELECTED_ANALYSIS_KEY)

    @classmethod
    def set_step_pipeline(cls, step_name: str):
        st.session_state[cls.STEP_PIPELINE_KEY] = step_name

    @classmethod
    def get_step_pipeline(cls) -> str:
        return st.session_state.get(cls.STEP_PIPELINE_KEY)
