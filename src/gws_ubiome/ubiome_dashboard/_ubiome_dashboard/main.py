import os

from gws_streamlit_main import StreamlitMainState, StreamlitRouter

StreamlitMainState.initialize()

from gws_ubiome.ubiome_dashboard._ubiome_dashboard_core import (
    State,
    analysis_page,
    first_page,
    new_analysis_page,
    settings,
)

params = StreamlitMainState.get_params()

associate_scenario_with_folder = params.get("associate_scenario_with_folder")
credentials_data = params.get("credentials_lab_large", None)

# Path of the folder containing the translation files
lang_translation_folder_path = os.path.join(
    os.path.abspath(os.path.dirname(__file__)), "../_ubiome_dashboard_core"
)
ubiome_state = State(lang_translation_folder_path)
ubiome_state.set_associate_scenario_with_folder(associate_scenario_with_folder)


def display_first_page(ubiome_state: State):
    first_page.render_first_page(ubiome_state)


def add_first_page(router: StreamlitRouter, ubiome_state: State):
    translate_service = ubiome_state.get_translate_service()
    router.add_page(
        lambda: display_first_page(ubiome_state),
        title=translate_service.translate("page_recipes"),
        url_path="first-page",
        icon="📦",
        hide_from_sidebar=False,
    )


def display_new_analysis_page(ubiome_state: State):
    new_analysis_page.render_new_analysis_page(ubiome_state)


def add_new_analysis_page(router: StreamlitRouter, ubiome_state: State):
    translate_service = ubiome_state.get_translate_service()
    router.add_page(
        lambda: display_new_analysis_page(ubiome_state),
        title=translate_service.translate("page_new_analysis"),
        url_path="new-analysis",
        icon=":material/edit_note:",
        hide_from_sidebar=True,
    )


def display_analysis_page(ubiome_state: State):
    analysis_page.render_analysis_page(ubiome_state)


def add_analysis_page(router: StreamlitRouter, ubiome_state: State):
    translate_service = ubiome_state.get_translate_service()
    router.add_page(
        lambda: display_analysis_page(ubiome_state),
        title=translate_service.translate("page_analysis"),
        url_path="analysis",
        icon=":material/analytics:",
        hide_from_sidebar=True,
    )


def display_settings_page(ubiome_state: State):
    settings.render_settings_page(ubiome_state)


def add_settings_page(router: StreamlitRouter, ubiome_state: State):
    translate_service = ubiome_state.get_translate_service()
    router.add_page(
        lambda: display_settings_page(ubiome_state),
        title=translate_service.translate("page_settings"),
        url_path="settings",
        icon=":material/settings:",
        hide_from_sidebar=False,
    )


router = StreamlitRouter.load_from_session()
# Add pages
add_first_page(router, ubiome_state)
add_new_analysis_page(router, ubiome_state)
add_analysis_page(router, ubiome_state)
add_settings_page(router, ubiome_state)

router.run()
