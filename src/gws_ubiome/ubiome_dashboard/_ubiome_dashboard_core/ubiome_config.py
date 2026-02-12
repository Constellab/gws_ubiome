import streamlit as st
from gws_core import Scenario
from .state import State


class UbiomeConfig:

    UBIOME_CONFIG_KEY = "ubiome_config"

    @classmethod
    def get_instance(cls) -> "UbiomeConfig":
        if UbiomeConfig.UBIOME_CONFIG_KEY not in st.session_state:
            st.session_state[UbiomeConfig.UBIOME_CONFIG_KEY] = cls()
        return st.session_state[UbiomeConfig.UBIOME_CONFIG_KEY]

    @classmethod
    def store_instance(cls, instance: "UbiomeConfig") -> None:
        st.session_state[UbiomeConfig.UBIOME_CONFIG_KEY] = instance


    def render_ratio_step(self, selected_scenario: Scenario, ubiome_state: State) -> None:
        pass
