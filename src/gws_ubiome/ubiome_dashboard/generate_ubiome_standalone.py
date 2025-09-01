import os

from gws_core import (
    ConfigParams, AppConfig, AppType, OutputSpec, OutputSpecs, StreamlitResource, Task, TaskInputs, TaskOutputs,
    app_decorator, task_decorator, TypingStyle
)


@app_decorator("UbiomeStandaloneDashboard", app_type=AppType.STREAMLIT)
class UbiomeStandaloneDashboardClass(AppConfig):

    def get_app_folder_path(self):
        return os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            "_ubiome_standalone"
        )


@task_decorator("UbiomeStandaloneDashboard",
                human_name="Standalone Ubiome AppConfig",
                short_description="Standalone Streamlit dashboard for Ubiome",
                style=TypingStyle.community_icon(icon_technical_name="dashboard", background_color="#178394"))
class UbiomeStandaloneDashboard(Task):
    """
    Standalone Ubiome dashboard. No data is stored.
    """

    output_specs: OutputSpecs = OutputSpecs(
        {'streamlit_app': OutputSpec(StreamlitResource, human_name="Standalone Variant Detection dashboard")}
    )

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        streamlit_app = StreamlitResource()
        streamlit_app.set_app_config(UbiomeStandaloneDashboardClass())
        streamlit_app.name = "Ubiome Standalone Dashboard"

        streamlit_app.set_requires_authentication(False)
        return {'streamlit_app': streamlit_app}
