import streamlit as st

from gws_core.streamlit import StreamlitResourceSelect, StreamlitRouter

def navigate_to_new_analysis():
    router = StreamlitRouter.load_from_session()
    router.navigate("new-analysis")

def navigate_to_first_page():
    router = StreamlitRouter.load_from_session()
    router.navigate("first-page")
