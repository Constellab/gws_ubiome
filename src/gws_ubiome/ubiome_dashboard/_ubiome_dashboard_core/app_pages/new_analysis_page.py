import streamlit as st
from gws_core import SpaceService
from gws_streamlit_main import (
    StreamlitContainers,
    StreamlitResourceSelect,
    StreamlitRouter,
    StreamlitTaskRunner,
)

from gws_ubiome import Qiime2MetadataTableMaker

from ..state import State
from ..ubiome_scenario_service import UbiomeScenarioService


def _flatten_folders_recursive(folders, folder_dict, folder_display_names, prefix="-"):
    """Recursively flatten folder hierarchy for display"""
    for folder in folders:
        display_name = f"{prefix}{folder.name}"
        folder_dict[folder.id] = folder.name
        folder_display_names[display_name] = folder.id

        # Recursively process children with increased indentation
        if hasattr(folder, "children") and folder.children:
            _flatten_folders_recursive(
                folder.children, folder_dict, folder_display_names, prefix + "------"
            )


def render_new_analysis_page(ubiome_state: State):
    style = """
    [CLASS_NAME] {
        padding: 40px;
    }
    """

    with StreamlitContainers.container_full_min_height(
        "container-center_new_analysis_page", additional_style=style
    ):
        translate_service = ubiome_state.get_translate_service()
        # Add a return button
        router = StreamlitRouter.load_from_session()

        if st.button(
            translate_service.translate("return_recipes"),
            icon=":material/arrow_back:",
            width="content",
        ):
            router.navigate("first-page")

        with st.form(clear_on_submit=False, enter_to_submit=True, key="new_analysis_form"):
            st.markdown(f"## {translate_service.translate('new_recipe')}")
            # select fastq data
            resource_select = StreamlitResourceSelect()
            # Filter to show only FastqFolder resources
            resource_select.add_filter("resourceTypingNames", ["RESOURCE.gws_omix.FastqFolder"])
            resource_select.select_resource(
                placeholder=translate_service.translate("search_fastq_resource"),
                key=UbiomeScenarioService.RESOURCE_SELECTOR_FASTQ_KEY,
                default_resource=None,
            )

            form_config = StreamlitTaskRunner(Qiime2MetadataTableMaker)
            form_config.generate_config_form_without_run(
                session_state_key=UbiomeScenarioService.QIIME2_METADATA_CONFIG_KEY,
                default_config_values=Qiime2MetadataTableMaker.config_specs.get_default_values(),
            )

            cols = st.columns(2)
            with cols[0]:
                st.text_input(
                    translate_service.translate("insert_recipe_name"),
                    key=UbiomeScenarioService.ANALYSIS_NAME_USER,
                )

            with cols[1]:
                space_service = SpaceService.get_instance()
                list_folders_in_lab = space_service.get_all_lab_root_folders().folders
                folder_dict = {}
                folder_display_names = {}

                # Flatten the folder hierarchy recursively
                _flatten_folders_recursive(list_folders_in_lab, folder_dict, folder_display_names)

                # Give the user the possibility to choose from all folders (including children)
                folder_to_associate_with = st.selectbox(
                    translate_service.translate("select_folder_associate"),
                    options=list(folder_display_names.keys()),
                    index=None,
                )
                # Save in session state the id of the folder
                ubiome_state.set_selected_folder_id(
                    folder_display_names.get(folder_to_associate_with)
                )

            submit_button = st.form_submit_button(label=translate_service.translate("run"))

            if submit_button:
                list_required_fields_filled = []
                list_required_fields_filled.append(
                    ubiome_state.check_if_required_is_filled(
                        ubiome_state.get_resource_selector_fastq()
                    )
                )
                if ubiome_state.check_if_required_is_filled(
                    ubiome_state.get_resource_selector_fastq()
                ):
                    list_required_fields_filled.append(
                        ubiome_state.get_resource_selector_fastq().get("resourceId") is not None
                    )
                list_required_fields_filled.append(
                    ubiome_state.check_if_required_is_filled(ubiome_state.get_analysis_name_user())
                )
                list_required_fields_filled.append(
                    ubiome_state.get_qiime2_metadata_config()["is_valid"]
                )
                if ubiome_state.get_associate_scenario_with_folder():
                    list_required_fields_filled.append(
                        ubiome_state.check_if_required_is_filled(
                            ubiome_state.get_selected_folder_id()
                        )
                    )
                # Check if mandatory fields have been filled
                if False in list_required_fields_filled:
                    st.warning(translate_service.translate("fill_mandatory_fields"))
                    return

                selected_fastq_id = ubiome_state.get_resource_selector_fastq()["resourceId"]
                analysis_name = ubiome_state.get_analysis_name_user()

                scenario = UbiomeScenarioService.create_metadata_scenario(
                    folder_id=ubiome_state.get_selected_folder_id(),
                    fastq_resource_model_id=selected_fastq_id,
                    analysis_name=analysis_name,
                    qiime2_config=ubiome_state.get_qiime2_metadata_config()["config"],
                )
                scenario.add_to_queue()

                router.navigate("first-page")
                st.rerun()
