import streamlit as st
from gws_core import StringHelper
from gws_ubiome.ubiome_dashboard._ubiome_dashboard.functions_home import navigate_to_new_analysis, navigate_to_first_page
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

    def build_home_button(self) -> bool:
        """Build the home button"""
        home_button = st.button(
            "Home",
            key=StringHelper.generate_uuid(),
            use_container_width=True,
            icon=":material/home:",
            type="primary",
            on_click=lambda: navigate_to_first_page()
        )
        return home_button

    def build_new_analysis_button(self) -> bool:
        """Build the new analysis button"""
        # On click, navigate to a hidden page 'run new analysis'
        new_analysis_button = st.button(
            "Create new analysis",
            key=StringHelper.generate_uuid(),
            use_container_width=True,
            icon=":material/add:",
            type="secondary",
            on_click=lambda: StreamlitRouter.load_from_session().navigate("new-analysis")
        )
        return new_analysis_button

    def build_return_home_button(self) -> bool:
        """Build the return home button"""
        return_home_button = st.button(
            "Return Home",
            key=StringHelper.generate_uuid(),
            use_container_width=True,
            icon=":material/arrow_back:",
            type="secondary"
        )
        return return_home_button
