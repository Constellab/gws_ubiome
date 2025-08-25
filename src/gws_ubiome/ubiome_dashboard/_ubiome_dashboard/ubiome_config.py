import streamlit as st
from gws_core import StringHelper
from gws_core.streamlit import StreamlitRouter


class UbiomeConfig():

    UBIOME_CONFIG_KEY = "ubiome_config"

    @classmethod
    def get_instance(cls) -> "UbiomeConfig":
        if UbiomeConfig.UBIOME_CONFIG_KEY not in st.session_state:
            st.session_state[UbiomeConfig.UBIOME_CONFIG_KEY] = cls()
        return st.session_state[UbiomeConfig.UBIOME_CONFIG_KEY]

    @classmethod
    def store_instance(cls, instance: "UbiomeConfig") -> None:
        st.session_state[UbiomeConfig.UBIOME_CONFIG_KEY] = instance

