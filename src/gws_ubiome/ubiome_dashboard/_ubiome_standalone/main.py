import streamlit as st
from gws_ubiome.ubiome_dashboard._ubiome_dashboard.pages import first_page, new_analysis_page, analysis_page
from gws_ubiome.ubiome_dashboard._ubiome_dashboard.state import State
from gws_core.streamlit import StreamlitRouter

if 'standalone' not in st.session_state:
    st.subheader("Welcome to the Ubiome Standalone Dashboard!")
    st.write("This application is intended exclusively for **visualization**, you can't run new analysis in this demo mode. Contact Gencovery team if you want the full app on your lab!")
    st.write("Click on the button to launch the app: ")

    if st.button("Launch the app"):
        # Set the attribute to indicate that this is a standalone dashboard
        st.session_state['standalone'] = True
        st.rerun()

else :
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

