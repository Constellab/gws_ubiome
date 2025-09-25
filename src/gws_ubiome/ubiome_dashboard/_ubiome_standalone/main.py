import streamlit as st
from gws_ubiome.ubiome_dashboard._ubiome_dashboard_core.pages import first_page, new_analysis_page, analysis_page
from gws_ubiome.ubiome_dashboard._ubiome_dashboard_core.state import State
from gws_core.streamlit import StreamlitRouter

ubiome_state = State()
ubiome_state.set_associate_scenario_with_folder(False)
ubiome_state.set_is_standalone(True)

# Hide sidebar completely
st.markdown("""
<style>
.stSidebar, [data-testid="stSidebarCollapsedControl"]{
    display: none;
}
</style>
""", unsafe_allow_html=True)

def display_first_page(ubiome_state : State):
    first_page.render_first_page(ubiome_state)

def add_first_page(router: StreamlitRouter, ubiome_state: State):
    router.add_page(
        lambda: display_first_page(ubiome_state),
        title='First page',
        url_path='first-page',
        icon='📦',
        hide_from_sidebar=True
    )

def display_new_analysis_page(ubiome_state : State):
    new_analysis_page.render_new_analysis_page(ubiome_state)

def add_new_analysis_page(router: StreamlitRouter, ubiome_state: State):
    router.add_page(
        lambda: display_new_analysis_page(ubiome_state),
        title='New Analysis',
        url_path='new-analysis',
        icon=":material/edit_note:",
        hide_from_sidebar=True
    )

def display_analysis_page(ubiome_state : State):
    analysis_page.render_analysis_page(ubiome_state)

def add_analysis_page(router: StreamlitRouter, ubiome_state: State):
    router.add_page(
        lambda: display_analysis_page(ubiome_state),
        title='Analysis',
        url_path='analysis',
        icon=":material/analytics:",
        hide_from_sidebar=True
    )

router = StreamlitRouter.load_from_session()
# Add pages
add_first_page(router, ubiome_state)
add_new_analysis_page(router, ubiome_state)
add_analysis_page(router, ubiome_state)


router.run()

