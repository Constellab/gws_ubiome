import os

from gws_core import (
    AppConfig,
    AppType,
    ConfigParams,
    OutputSpec,
    OutputSpecs,
    StreamlitResource,
    Task,
    TaskInputs,
    TaskOutputs,
    TypingStyle,
    app_decorator,
    task_decorator,
)


@app_decorator("UbiomeStandaloneDashboard", app_type=AppType.STREAMLIT)
class UbiomeStandaloneDashboardClass(AppConfig):

    def get_app_folder_path(self):
        return os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            "_ubiome_standalone"
        )


@task_decorator("UbiomeStandaloneDashboard",
                human_name="Standalone Ubiome",
                short_description="Standalone Streamlit dashboard for Ubiome",
                style=TypingStyle.community_icon(icon_technical_name="dashboard", background_color="#178394"))
class UbiomeStandaloneDashboard(Task):
    """
    Standalone Constellab 16S rRNA-seq. No data is stored.

    This dashboard provides visualization for microbiome data.

    The Constellab 16S rRNA-seq is a Streamlit application designed for microbiome visualization. It provides an interactive interface for interpreting 16S rRNA sequencing data through various bioinformatics workflows.

    The aim is to simplify the use of the Ubiome Brick by providing an application that makes retrieving results easier. Dependencies between scenarios are also maintained, allowing you to navigate more easily.

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

    output_specs: OutputSpecs = OutputSpecs(
        {'streamlit_app': OutputSpec(StreamlitResource, human_name="Standalone Variant Detection dashboard")}
    )

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        streamlit_app = StreamlitResource()
        streamlit_app.set_app_config(UbiomeStandaloneDashboardClass())
        streamlit_app.name = "Constellab 16S rRNA-seq Standalone"

        streamlit_app.set_requires_authentication(False)
        return {'streamlit_app': streamlit_app}
