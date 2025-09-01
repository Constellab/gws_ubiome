from gws_core import (ConfigParams, AppConfig, AppType, OutputSpec,
                      OutputSpecs, StreamlitResource, Task, TaskInputs,
                      CredentialsDataLab, CredentialsParam, CredentialsType,
                      TaskOutputs, app_decorator, task_decorator,
                      InputSpecs, ConfigSpecs, BoolParam)


@app_decorator("UbiomeDashboardAppConfig", app_type=AppType.STREAMLIT,
               human_name="Generate Ubiome Dashboard app")
class UbiomeDashboardAppConfig(AppConfig):
    """
    Configuration class for the Ubiome Dashboard Streamlit application.

    This class defines the configuration and setup for a Streamlit-based dashboard
    that provides visualization and analysis capabilities for microbiome data.
    """

    # retrieve the path of the app folder, relative to this file
    # the app code folder starts with a underscore to avoid being loaded when the brick is loaded
    def get_app_folder_path(self):
        return self.get_app_folder_from_relative_path(__file__, "_ubiome_dashboard")


@task_decorator("GenerateUbiomeDashboard", human_name="Generate Ubiome Dashboard app",
                style=StreamlitResource.copy_style())
class GenerateUbiomeDashboard(Task):
    """
    Task that generates the Ubiome Dashboard app.
    This dashboard provides visualization and analysis capabilities for microbiome data.
    The Ubiome Dashboard is a Streamlit application designed for microbiome data analysis and visualization. It provides an interactive interface for processing, analyzing, and interpreting 16S rRNA sequencing data through various bioinformatics workflows.

    The aim is to simplify the use of the Ubiome Brick by providing an application that makes running the pipeline and retrieving results easier. Dependencies between scenarios are also maintained, allowing you to navigate more easily.

    Multi-Step Analysis Pipeline

    The dashboard implements a structured analysis workflow with the following steps:

    - Metadata table: Create a metadata table from a fastq folder
    - Quality Control (QC): Initial data quality assessment
    - MultiQC Reporting: Comprehensive quality control reporting
    - Feature Inference: ASV/OTU identification and quantification
    - Taxonomy Assignment: Taxonomic classification of features
    - Rarefaction Analysis: Diversity curve generation
    - PCoA (Principal Coordinate Analysis): Beta diversity visualization
    - ANCOM (Analysis of Composition of Microbiomes): Differential abundance testing
    - Database Annotation: Feature annotation against reference databases
    - Functional Prediction: Metabolic pathway inference using tools like PICRUSt2

    """

    input_specs = InputSpecs()
    output_specs = OutputSpecs({
        'streamlit_app': OutputSpec(StreamlitResource)
    })

    config_specs : ConfigSpecs = ConfigSpecs({'associate_scenario_with_folder': BoolParam(
        default_value=False, human_name="Associate Scenario with Folder", short_description="Set to True if it is mandatory to associate scenarios with a folder."
    ),
    'credentials_lab_large' : CredentialsParam(
        credentials_type=CredentialsType.LAB, human_name="Credentials lab large to run 16s step", short_description="Credentials to request lab large's API", optional = True)})


    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        credentials_data: CredentialsDataLab = params.get_value(
            'credentials_lab_large')

        """ Run the task """

        streamlit_app = StreamlitResource()

        streamlit_app.set_app_config(UbiomeDashboardAppConfig())
        streamlit_app.name = "Ubiome Dashboard"

        # Add param
        associate_scenario_with_folder: bool = params.get_value(
            'associate_scenario_with_folder')
        streamlit_app.set_param(
            'associate_scenario_with_folder', associate_scenario_with_folder)
        if credentials_data:
            streamlit_app.set_param(
                "credentials_name", credentials_data.meta.name)

        return {"streamlit_app": streamlit_app}
