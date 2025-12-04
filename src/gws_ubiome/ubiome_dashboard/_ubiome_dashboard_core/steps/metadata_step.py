import streamlit as st
from gws_ubiome.ubiome_dashboard._ubiome_dashboard_core.state import State
from gws_core.streamlit import StreamlitAuthenticateUser
from gws_core import Scenario, ScenarioProxy, ProtocolProxy, File, TableImporter, Scenario, ScenarioProxy, ProtocolProxy
from gws_ubiome.ubiome_dashboard._ubiome_dashboard_core.functions_steps import search_updated_metadata_table, save_metadata_table, add_new_column_dialog

def render_metadata_step(selected_scenario: Scenario, ubiome_state: State) -> None:
    translate_service = ubiome_state.get_translate_service()

    scenario_proxy = ScenarioProxy.from_existing_scenario(selected_scenario.id)
    protocol_proxy: ProtocolProxy = scenario_proxy.get_protocol()

    # Check if there's an updated metadata table first
    file_metadata = search_updated_metadata_table(ubiome_state)

    # If no updated table found, use the original scenario output
    if file_metadata is None:
        file_metadata: File = protocol_proxy.get_process('metadata_process').get_output('metadata_table')

    # Read the raw file content to capture header lines
    raw_content = file_metadata.read()
    lines = raw_content.split('\n')

    # Find where the actual table data starts (usually after comment lines starting with #)
    header_lines = []
    for i, line in enumerate(lines):
        if line.strip().startswith('#') or (line.strip() and not '\t' in line and not ',' in line):
            header_lines.append(line)
        else:
            break

    # Import the file with Table importer
    table_metadata = TableImporter.call(file_metadata)
    df_metadata = table_metadata.get_data()
    # Define that all columns types must be string
    df_metadata = df_metadata.astype(str)

    st.markdown(f"##### {translate_service.translate('metadata_table_editor')}")

    if not ubiome_state.get_scenario_step_qc():
        if not ubiome_state.get_is_standalone():
            st.info(f"💡 **{translate_service.translate('instructions')}:** {translate_service.translate('instructions_metadata')}")

            if st.button(translate_service.translate("add_column"), width="stretch"):
                add_new_column_dialog(ubiome_state, header_lines, protocol_proxy)

            # Create column configuration for all columns
            column_config = {}

            # Configure all data columns
            for column in df_metadata.columns:
                column_config[column] = st.column_config.TextColumn(
                    label=column,
                    max_chars=200
                )

            # Use data editor for editing capabilities
            st.session_state[ubiome_state.EDITED_DF_METADATA] = st.data_editor(
                df_metadata,
                hide_index=True,
                width="stretch",
                num_rows="dynamic",
                column_config=column_config,
                key="data_editor"
            )
        else:
            st.dataframe(df_metadata, width="stretch", hide_index=True)
    else:
        st.dataframe(df_metadata, width="stretch", hide_index=True)

    # Save button only appear if QC task have not been created
    if not ubiome_state.get_scenario_step_qc():
        if not ubiome_state.get_is_standalone():
            # Validation
            validation_errors = []

            # Check if at least one new column was added
            if len(ubiome_state.get_edited_df_metadata().columns) == 3:
                validation_errors.append(f"⚠️ {translate_service.translate('one_metadata_column_required')}")

            # Check if all columns are completely filled
            for col in ubiome_state.get_edited_df_metadata().columns:
                if ubiome_state.get_edited_df_metadata()[col].isna().any() or (ubiome_state.get_edited_df_metadata()[col] == "").any():
                    validation_errors.append(f"⚠️ '{col}' : {translate_service.translate('column_must_be_filled')}")

            # Check if there are any rows left
            if len(ubiome_state.get_edited_df_metadata()) == 0:
                validation_errors.append(f"⚠️ {translate_service.translate('one_sample_required')}")

            # Display validation results
            if validation_errors:
                for error in validation_errors:
                    st.error(error)
                save_disabled = True
            else:
                save_disabled = False

            if st.button(translate_service.translate("save"), disabled=save_disabled, width="content"):
                with StreamlitAuthenticateUser():
                    # Use the helper function to save
                    save_metadata_table(ubiome_state.get_edited_df_metadata(), header_lines, ubiome_state, protocol_proxy)
                    st.rerun()
        else:
            st.info(f"ℹ️ {translate_service.translate('standalone_metadata_info')}")
    else:
        st.info(f"ℹ️ {translate_service.translate('metadata_locked_info')}")