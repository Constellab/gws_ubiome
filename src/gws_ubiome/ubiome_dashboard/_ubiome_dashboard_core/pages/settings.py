import streamlit as st
from gws_core.streamlit import StreamlitTranslateLang
from gws_ubiome.ubiome_dashboard._ubiome_dashboard_core.state import State

def render_settings_page(ubiome_state : State):
    translate_service = ubiome_state.get_translate_service()

    # Get current language from translate service, not from session state string
    current_lang = translate_service.get_lang()

    # Map enum to display strings and indices
    lang_options = ["English", "Français"]
    lang_enum_map = {
        "English": StreamlitTranslateLang.EN,
        "Français": StreamlitTranslateLang.FR
    }

    # Convert current enum to index
    if current_lang == StreamlitTranslateLang.EN:
        current_index = 0
    elif current_lang == StreamlitTranslateLang.FR:
        current_index = 1
    else:
        current_index = 0  # Default to English

    selected_lang_str = st.selectbox(
        translate_service.translate("select_language"),
        options=lang_options,
        index=current_index,
        key=ubiome_state.LANG_KEY
    )

    # Convert selected string back to enum
    selected_lang_enum = lang_enum_map[selected_lang_str]

    # Check if language actually changed
    if current_lang != selected_lang_enum:
        # Change the language in the translate service
        translate_service.change_lang(selected_lang_enum)
        # Update the state
        ubiome_state.set_translate_service(translate_service)
        st.rerun()
