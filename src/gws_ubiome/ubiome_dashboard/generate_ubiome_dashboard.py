from gws_core import (ConfigParams, AppConfig, AppType, OutputSpec,
                      OutputSpecs, StreamlitResource, Task, TaskInputs,
                      TaskOutputs, app_decorator, task_decorator,
                      InputSpecs, ConfigSpecs)


@app_decorator("UbiomeDashboardAppConfig", app_type=AppType.STREAMLIT,
               human_name="Generate Ubiome Dashboard app")
class UbiomeDashboardAppConfig(AppConfig):

    # retrieve the path of the app folder, relative to this file
    # the app code folder starts with a underscore to avoid being loaded when the brick is loaded
    def get_app_folder_path(self):
        return self.get_app_folder_from_relative_path(__file__, "_ubiome_dashboard")


@task_decorator("GenerateUbiomeDashboard", human_name="Generate Ubiome Dashboard app",
                style=StreamlitResource.copy_style())
class GenerateUbiomeDashboard(Task):
    """
    Task that generates the Ubiome Dashboard app.
    """

    input_specs = InputSpecs()
    output_specs = OutputSpecs({
        'streamlit_app': OutputSpec(StreamlitResource)
    })

    config_specs = ConfigSpecs({})

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        """ Run the task """

        streamlit_app = StreamlitResource()

        streamlit_app.set_app_config(UbiomeDashboardAppConfig())
        streamlit_app.name = "Ubiome Dashboard"

        return {"streamlit_app": streamlit_app}
