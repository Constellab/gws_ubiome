# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
from gws_core import (ConfigParams,  InputSpec, InputSpecs, IntParam, OutputSpec, OutputSpecs, Folder,
                      Task, TaskInputs, TaskOutputs, task_decorator, File, )

from gws_core.config.config_types import ConfigSpecs
from gws_omix import FastaFile
# from gws_core import ShellProxy

from ..base_env.Picrust2_env import Picrust2ShellProxyHelper


@task_decorator("Picrust2FunctionalAnalysis", human_name="Picrust2 Functional Analysis",
                short_description="this task permit to predict functional analysis of 16s rRNA data")
class Picrust2FunctionalAnalysis(Task):
    """
    This task uses PICRUSt2 : Phylogenetic Investigation of Communities by Reconstruction of Unobserved States(paper can be found <a href="https://www.nature.com/articles/s41587-020-0548-6">here</a>).It wraps a number of tools to generate functional predictions based on 16S rRNA gene sequencing data.
    The input files should be a FASTA of amplicon sequences variants (ASVs; i.e. your representative sequences, not your raw reads, which is <b> ASV-sequences.fasta </b> generated using Q2FeatureInference task) and a CSV table of the abundance of each ASV across each sample which is <b> asv_table.csv </b> (generated using Taxonomy_Diversity task ).
    The key output files are:
    - <b style="margin-left: 2.5em"> EC_metagenome_out </b> : Folder containing unstratified EC number metagenome predictions.
      (pred_metagenome_unstrat.tsv.gz), sequence table normalized by predicted 16S copy number abundances.
      (seqtab_norm.tsv.gz), and the per-sample NSTI values weighted by the abundance of each ASV (weighted_nsti.tsv.gz).
    - <b style="margin-left: 2.5em"> KO_metagenome_out </b> : As EC_metagenome_out above, but for Kegg orthology metagenomes.
    - <b style="margin-left: 2.5em"> pathways_out </b>      : Folder containing predicted pathway abundances and coverages per-sample, based on predicted EC number abundances.
    """

    input_specs = InputSpecs({
        'ASV_count_abundance':
        InputSpec(
            File, human_name="ASV_count_abundance",
            short_description="File containing the abundance of each ASV across each sample"),
        'FASTA_of_asv':
        InputSpec(
            FastaFile, human_name="FASTA_of_amplicon_sequences_variants",
            short_description="This file contain FASTA of amplicon sequences variants")
    })

    output_specs = OutputSpecs({
        'Folder_result':
        OutputSpec(
            Folder, human_name="picrust2_out_pipeline",
            short_description="This folder contain the outputs")
    })

    config_specs: ConfigSpecs = {
        "num_processes": IntParam(default_value=2, min_value=2, short_description="Number of threads ")
    }

    python_file_path = os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        "_picrust2_functional_analysis.py"
    )

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        """ Run the task """

        # retrive the input table
        input_file: File = inputs['ASV_count_abundance']
        seq_file_path: File = inputs['FASTA_of_asv']
        num_processes = params["num_processes"]

        # retrieve the factor param value
        # shell_proxy = ShellProxy(message_dispatcher=self.message_dispatcher)
        # Define the command to run
        # cmd = f"conda run -n picrust2 python3 {self.python_file_path} {input_file.path} {seq_file_path.path} {num_processes}"
        # Execute the command
        # shell_proxy.run(cmd, shell_mode=True)

        ######################################
        # retrieve the factor param value
        shell_proxy = Picrust2ShellProxyHelper.create_proxy(self.message_dispatcher)

        # call python file
        cmd = f"python3 {self.python_file_path} {input_file.path} {seq_file_path.path} {num_processes}"
        shell_proxy.run(cmd, shell_mode=True)

       #############################

        combined_results = os.path.join(shell_proxy.working_dir, "picrust2_out_pipeline")

        # return the output table
        return {
            'Folder_result': Folder(combined_results),
        }