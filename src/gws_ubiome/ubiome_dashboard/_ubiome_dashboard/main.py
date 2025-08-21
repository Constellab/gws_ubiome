import streamlit as st

from _ubiome_dashboard.pages import first_page, new_analysis_page, analysis_page
from gws_core.streamlit import StreamlitRouter

sources: list
params: dict

# Hide sidebar completely
st.markdown("""
<style>
.stSidebar, [data-testid="stSidebarCollapsedControl"]{
    display: none;
}
</style>
""", unsafe_allow_html=True)

def display_first_page():
    first_page.render_first_page()

def add_first_page(router: StreamlitRouter):
    router.add_page(
        lambda: display_first_page(),
        title='First page',
        url_path='first-page',
        icon='📦',
        hide_from_sidebar=True
    )

def display_new_analysis_page():
    new_analysis_page.render_new_analysis_page()

def add_new_analysis_page(router: StreamlitRouter):
    router.add_page(
        lambda: display_new_analysis_page(),
        title='New Analysis',
        url_path='new-analysis',
        icon=":material/edit_note:",
        hide_from_sidebar=True
    )

def display_analysis_page():
    analysis_page.render_analysis_page()

def add_analysis_page(router: StreamlitRouter):
    router.add_page(
        lambda: display_analysis_page(),
        title='Analysis',
        url_path='analysis',
        icon=":material/analytics:",
        hide_from_sidebar=True
    )

router = StreamlitRouter.load_from_session()
# Add pages
add_first_page(router)
add_new_analysis_page(router)
add_analysis_page(router)


router.run()

