# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


import os

from gws_core import (ConfigParams, ConfigSpecs, File, InputSpec, InputSpecs,
                      IntParam, MetadataTableImporter, OutputSpec, OutputSpecs,
                      ResourceSet, StrParam, Table, TableAnnotatorHelper,
                      TableImporter, Task, TaskInputs, TaskOutputs,
                      task_decorator)

from ..base_env.qiime2_env_task import Qiime2ShellProxyHelper
from ..differential_analysis.qiime2_differential_analysis_result_folder import \
    Qiime2DifferentialAnalysisResultFolder
from ..taxonomy_diversity.qiime2_taxonomy_diversity_folder import \
    Qiime2TaxonomyDiversityFolder


@task_decorator("Qiime2DifferentialAnalysis", human_name="Qiime2 ANCOM differential analysis",
                short_description="Perform ANCOM differential analysis using metadata information")
class Qiime2DifferentialAnalysis(Task):
    """
    Qiime2DifferentialAnalysis class.

    This task perform ANCOM differential analysis test (integrated to Qiime2 suite) using input metadata informations.

    For more information: the ANCOM test is a well described in the original paper: https://www.tandfonline.com/doi/full/10.3402/mehd.v26.27663

    """
    OUTPUT_FILES = {
        "Phylum - ANCOM Stat : W stat": "2.ancom.tsv",
        "Phylum - Volcano plot: y=F-score, x=W stat": "2.data.tsv",
        "Class - ANCOM Stat: W stat": "3.ancom.tsv",
        "Class - Volcano plot: y=F-score, x=W stat": "3.data.tsv",
        "Order - ANCOM Stat: W stat": "4.ancom.tsv",
        "Order - Volcano plot: y=F-score, x=W stat": "4.data.tsv",
        "Family - ANCOM Stat: W stat": "5.ancom.tsv",
        "Family - Volcano plot: y=F-score, x=W stat": "5.data.tsv",
        "Genus - ANCOM Stat: W stat": "6.ancom.tsv",
        "Genus - Volcano plot: y=F-score, x=W stat": "6.data.tsv",
        "Species - ANCOM Stat: W stat": "7.ancom.tsv",
        "Species - Volcano plot: y=F-score, x=W stat": "7.data.tsv"
    }
    PERCENTILE_TABLE = {
        "Phylum - Percentile abundances": "2.percent-abundances.tsv",
        "Class - Percentile abundances": "3.percent-abundances.tsv",
        "Order - Percentile abundances": "4.percent-abundances.tsv",
        "Family - Percentile abundances": "5.percent-abundances.tsv",
        "Genus - Percentile abundances": "6.percent-abundances.tsv",
        "Species - Percentile abundances": "7.percent-abundances.tsv"
    }

    input_specs: InputSpecs = {
        'taxonomy_diversity_folder': InputSpec(Qiime2TaxonomyDiversityFolder),
        'metadata_file': InputSpec(File, short_description="Metadata file", human_name="Metadata_file")
    }
    output_specs: OutputSpecs = {
        'result_tables': OutputSpec(ResourceSet),
        'result_folder': OutputSpec(Qiime2DifferentialAnalysisResultFolder)
    }
    config_specs: ConfigSpecs = {
        "metadata_column": StrParam(
            human_name="Metadata column",
            short_description="Column on which the differential analysis will be performed"),
        "threads": IntParam(default_value=2, min_value=2, short_description="Number of threads")}

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:

        # get options, I/O variables
        qiime2_folder = inputs["taxonomy_diversity_folder"]
        metadata_col = params["metadata_column"]
        metadata_f = inputs["metadata_file"]
        thrds = params["threads"]

        script_file_dir = os.path.dirname(os.path.realpath(__file__))
        # test last qiime2 version, for the new ancom fonction (ancombc)
        # shell_proxy = Qiime2_2022_11_ShellProxyHelper.create_proxy(self.message_dispatcher)
        shell_proxy = Qiime2ShellProxyHelper.create_proxy(self.message_dispatcher)

        # perform ANCOM analysis

        outputs = self.run_cmd(shell_proxy,
                               qiime2_folder,
                               metadata_col,
                               metadata_f,
                               thrds,
                               script_file_dir
                               )

        return outputs

    def run_cmd(self, shell_proxy: Qiime2ShellProxyHelper,  # shell_proxy: Qiime2_2022_11_ShellProxyHelper,
                qiime2_folder: str,
                metadata_col: str,
                metadata_f: str,
                thrds: int,
                script_file_dir: str) -> None:

        cmd = [
            " bash ", os.path.join(script_file_dir, "./sh/5_qiime2.differential_analysis.all_taxa_levels.sh"),
            qiime2_folder.path,
            metadata_col,
            thrds,
            metadata_f.path
        ]

        shell_proxy.run(cmd)

        result_folder = Qiime2DifferentialAnalysisResultFolder()
        result_folder.path = os.path.join(shell_proxy.working_dir, "differential_analysis")

        resource_table_set: ResourceSet = ResourceSet()
        resource_table_set.name = "Set of differential analysis tables"
        for key, value in self.OUTPUT_FILES.items():
            path = os.path.join(shell_proxy.working_dir, "differential_analysis", value)
            table = TableImporter.call(File(path=path), {'delimiter': 'tab', "index_column": 0})
            table.name = key

            # Metadata table
            path = os.path.join(shell_proxy.working_dir, "differential_analysis", value)
            metadata_table = MetadataTableImporter.call(File(path=path), {'delimiter': 'tab'})

            table_annotated = TableAnnotatorHelper.annotate_rows(table, metadata_table)
            table_annotated.name = key
            resource_table_set.add_resource(table_annotated)

        for key, value in self.PERCENTILE_TABLE.items():
            path = os.path.join(shell_proxy.working_dir, "differential_analysis", value)
            table = TableImporter.call(File(path=path), {'delimiter': 'tab', "index_column": 0})
            data = table.get_data()
            column_tags = []

            column_names = table.column_names
            first_row = [val if val else "unknown" for _, val in enumerate(data.iloc[0, :])]
            group_key = metadata_col
            final_col_names = []
            for i, col_name in enumerate(column_names):
                column_tags.append({
                    group_key: first_row[i],
                    "quantile": col_name,
                })
                final_col_names.append(str(first_row[i])+"_"+str(col_name))

            data = data.iloc[1:, :]
            data.columns = final_col_names
            data = data.apply(pd.to_numeric, errors='coerce')

            table = Table(data=data)
            table.set_all_column_tags(column_tags)  # set_column_tags

            table.name = key
            resource_table_set.add_resource(table)

        return {
            "result_folder": result_folder,
            "result_tables": resource_table_set
        }
