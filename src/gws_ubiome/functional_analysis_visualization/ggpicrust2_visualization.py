
import os

import pandas as pd
import plotly.express as px
from gws_core import (BoolParam, ConfigParams, ConfigSpecs, File, InputSpec,
                      InputSpecs, IntParam, OutputSpec, OutputSpecs,
                      PlotlyResource, ResourceSet, ShellProxy, StrParam,
                      TableImporter, Task, TaskInputs, TaskOutputs,
                      task_decorator,FloatParam)

from ..base_env.Ggpicrust2_env import Ggpicrust2ShellProxyHelper


@task_decorator("Ggpicrust2FunctionalAnalysisVisualization", human_name="16s Functional Analysis Prediction Visualization",
                short_description="This task permit to analyze and interpret the results of PICRUSt2 functional prediction of 16s rRNA data")
class Ggpicrust2FunctionalAnalysis(Task):
    """
    - ggPicrust2 (paper can be found <a href="https://academic.oup.com/bioinformatics/article/39/8/btad470/7234609?login=false">here</a>)  is an R package developed explicitly for PICRUSt2 predicted functional profile.
    - ggpicrust2() integrates ko abundance which is the abundance of different gene orthologs in your microbial community generated by Picrust2 to kegg pathway abundance conversion that represents the predicted abundance of entire metabolic pathways, which are composed of multiple KO groups. It also involves annotation of pathway and differential abundance (DA) analysis in order to understand the functional potential of your microbial community at the pathway level
    - It takes PICRUSt2 original output pred_metagenome_unstrat.tsv generated using Picrust2 Functional Analysis task without reformat and a metadata file.
    - The mainstream visualization of PICRUSt2 is error_bar_plot, pca_plot and heatmap_plot.
        <b style="margin-left: 2.5em"> pathway_errorbar </b> can show the relative abundance difference between groups and log2 fold change and P-values (adjusted) derived from DA results in term of pathway abundance. All the p-adjusted values that you see are significantly < 0.05.
        <b style="margin-left: 2.5em">pathway_pca() </b> can show the difference after dimensional reduction via principal component analysis.
        <b style="margin-left: 2.5em">pathway_heatmap() </b> Pairwise comparison between groups in terms of pathway differential abundance.
    """

    input_specs = InputSpecs({
        'ko_abundance_file':
        InputSpec(
            File, human_name="ko_abundance_file",
            short_description="File containing the kegg orthology (KO) abundance"),
        'metadata_file':
        InputSpec(
            File, human_name="Metadata file",
            short_description="This file contain informations about the experince")
    })
    output_specs = OutputSpecs({
        'resource_set':
        OutputSpec(
            ResourceSet, human_name="Metadata associated to each cell",
            short_description="This table stores metadata associated with each cell such as mitochondrial content , number of counts etc"),

        'plotly_result':
        OutputSpec(
            PlotlyResource, human_name="pathway_pca",
            short_description="Show the difference after dimensional reduction via principal component analysis.")
    })

    config_specs: ConfigSpecs = {
        "DA_method": StrParam(allowed_values=["LinDA", " "], short_description="Differential abundance (DA) method"),
        "Samples_column_name": StrParam(short_description="Column name in metadata file containing the sample name"),
        "Reference_column": StrParam(short_description="Column name in metadata file containing the reference group"),
        "Reference_group": StrParam(short_description="Reference group level for DA"),
        "Round_digit": BoolParam(
            default_value=False, human_name="Round Digit",
            short_description="Remember to click on this button whenever you observe p-adjust values higher than 0.05 in order to ensure accurate and appropriately formatted results."),
        "PCA_component": BoolParam(
            default_value=False, human_name="PCA Component",
            short_description="Perform 3D PCA if True, 2D PCA if False."),

        "Slice_start": IntParam(
            default_value=1, min_value=1, human_name="Slice start", visibility=IntParam.PROTECTED_VISIBILITY,
            short_description="You can modify the slice window of the errorbar and the heatmap by modifying the slice start in order to focus on a subset of the results"),
    }

    r_file_path = os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        "_ggpicrust2_annotation.R"
    )

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        """ Run the task """
        # retrive the input table
        ko_abundance_file: File = inputs['ko_abundance_file']
        metadata_file: File = inputs['metadata_file']
        DA_method = params["DA_method"]
        Samples_column_name = params["Samples_column_name"]
        Reference_column = params["Reference_column"]
        Reference_group = params["Reference_group"]
        Round_digit = params["Round_digit"]
        PCA_component = params["PCA_component"]
        Slice_start = params["Slice_start"]

        # retrieve the factor param value
        shell_proxy: ShellProxy = Ggpicrust2ShellProxyHelper.create_proxy(self.message_dispatcher)

        # call python file
        cmd = f"Rscript --vanilla {self.r_file_path} {ko_abundance_file.path} {metadata_file.path} {DA_method} {Samples_column_name} {Reference_column} {Reference_group} {Round_digit} {PCA_component} {Slice_start}"
        result = shell_proxy.run(cmd, shell_mode=True)

        if result != 0:
            raise Exception("An error occured during the execution of the script. No statistically significant biomarkers found. Statistically significant biomarkers refer to those biomarkers that demonstrate a significant difference in expression between different groups, as determined by a statistical test (p_adjust < 0.05 in this case")

        # table_file_path = os.path.join(shell_proxy.working_dir, "daa_annotated_sub_method_results_df1.csv")
        # pathway_errorbar = os.path.join(shell_proxy.working_dir, "pathway_errorbar.png")
        # pathway_heatmap = os.path.join(shell_proxy.working_dir, "pathway_heatmap.png")

        # Loop through the working directory and add files to the resource set
        resource_set = ResourceSet()
        for filename in os.listdir(shell_proxy.working_dir):
            file_path = os.path.join(shell_proxy.working_dir, filename)
            if os.path.isfile(file_path):
                if filename.startswith("pathway_errorbar_") and filename.endswith(".png"):
                    resource_set.add_resource(File(file_path), filename)
                elif filename.startswith("pathway_heatmap_") and filename.endswith(".png"):
                    resource_set.add_resource(File(file_path), filename)
                elif filename.startswith("daa_annotated_results_") and filename.endswith(".csv"):
                    resource_set.add_resource(TableImporter.call(File(file_path)), filename)

        pca_proportion_file_path = os.path.join(shell_proxy.working_dir, "pca_proportion.csv")
        pca_file_path = os.path.join(shell_proxy.working_dir, "pca_results.csv")
        plolty_resource = self.build_plotly(pca_file_path, pca_proportion_file_path, Reference_column)

    #    # return the output table
    #    return {
    #        'table_1': table,
    #        'errorbar_result': File(pathway_errorbar),
    #        'heatmap_result': File(pathway_heatmap),
    #        'plotly_result': plolty_resource
    #    }

        # return the output plotly resource and resource set
        return {
            'plotly_result': plolty_resource,
            'resource_set': resource_set
        }

    def build_plotly(self, pca_file_path, pca_proportion_file_path, Reference_column) -> PlotlyResource:
        # Read the CSV data
        data = pd.read_csv(pca_file_path)
        proportion_data = pd.read_csv(pca_proportion_file_path)

        # Extract the values for principal components
        num_components = data.shape[1] - 2

        # Create a scatter plot
        if num_components == 2:
            fig = px.scatter(data, x=data.columns[0], y=data.columns[1], color=Reference_column)
        elif num_components == 3:
            fig = px.scatter_3d(data, x=data.columns[0], y=data.columns[1], z=data.columns[2], color=Reference_column)
            # Customize the 3D plot layout
            fig.update_layout(
                scene=dict(
                    xaxis_title=f"PC1 ({proportion_data.iloc[0, 0]:.2f}%)",
                    yaxis_title=f"PC2 ({proportion_data.iloc[1, 0]:.2f}%)",
                    zaxis_title=f"PC3 ({proportion_data.iloc[2, 0]:.2f}%)"
                ),
                width=800,
                height=600
            )
        else:
            raise ValueError("Number of principal components must be 2 or 3")

        # Customize the plot layout for both 2D and 3D
        fig.update_layout(
            title="Principal Component Analysis (PCA) applied to pathway abundance data",
            xaxis_title=f"{data.columns[0]} ({proportion_data.iloc[0, 0]:.2f}%)",
            yaxis_title=f"{data.columns[1]} ({proportion_data.iloc[1, 0]:.2f}%)",
            xaxis=dict(
                showline=True,
                linecolor='black',
                mirror=True,
                showticklabels=True
            ),
            yaxis=dict(
                showline=True,
                linecolor='black',
                mirror=True,
                showticklabels=True
            )
        )

        # Add dashed lines for the axes covering the whole plot
        fig.add_shape(
            type="line",
            x0=min(data[data.columns[0]]) - 5,
            x1=max(data[data.columns[0]]) + 5,
            y0=0,
            y1=0,
            line=dict(dash="dash", color="black", width=0.5)
        )

        fig.add_shape(
            type="line",
            x0=0,
            x1=0,
            y0=min(data[data.columns[1]]) - 5,
            y1=max(data[data.columns[1]]) + 5,
            line=dict(dash="dash", color="black", width=0.5)
        )

        if num_components == 3:
            fig.add_shape(
                type="line",
                x0=0,
                x1=0,
                y0=0,
                y1=0,
                line=dict(dash="dash", color="black", width=0.5)
            )

        return PlotlyResource(fig)
