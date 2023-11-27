# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os

from gws_core import (ConfigParams, ConfigSpecs, File, Folder, InputSpec,
                      InputSpecs, IntParam, OutputSpec, OutputSpecs,
                      ShellProxy, Table, TableAnnotatorHelper, TableImporter,
                      Task, TaskInputs, TaskOutputs, task_decorator)

from ..base_env.qiime2_env_task import Qiime2ShellProxyHelper
from ..feature_frequency_table.feature_frequency_table import \
    FeatureFrequencyTable


@task_decorator("old_Qiime2FeatureTableExtractorSE", human_name="old_Q2FeatureInferenceSE",
                short_description="Inference of ASVs from single-end sequencing (Depreceated)",
                deprecated_since="0.5.3", deprecated_message="USe Q2FeatureInferenceSE instead")
class old_Qiime2FeatureTableExtractorSE(Task):
    """
    old_Qiime2FeatureTableExtractorSE class.

    DEPRECATED: Use instead Qiime2FeatureTableExtractorSE class (old_Q2FeatureInferenceSE)

    This task infers Amplicon Sequence Variants (ASVs) using the function ```qiime dada2 denoise-single``` from Qiime2. This task starts by trimming and filtering sequences (see below) before infering ASVs with DADA2 (The Divisive Amplicon Denoising Algorithm).

    **About trimming sequences:**

    It is convenient to ensure that the quality of the reads does not fall below a PHRED score at 25 (corresponding to 1 incorrect base over a length of 320). To avoid problems in the determination of chimeras it is convenient to eliminate the first nucleotides as they may correspond to the primers that have been used in the 16S amplification.

    ```truncated_reads_size``` refers to the position at which read sequences should be *truncated* due to decrease in quality. This truncates the 3' end of sequences (i.e. the right side).

    ```5_prime_hard_trimming_reads_size``` refers to the position at which read sequences should be *trimmed* due to low quality. This trims the 5' end of the input sequences (i.e. the left side).

    If both ```truncated_reads_size``` and ```5_prime_hard_trimming_reads_size``` are provided, filtered reads will have length ```truncated_reads_size```-```5_prime_hard_trimming_reads_size```.

    *Example*

    With the following sequence of 10 nucleotides **ATCATCATCG**, using ```truncated_reads_size``` at 8 and ```5_prime_hard_trimming_reads_size``` at 2 will result in a sequence of 6 nucleotide **CATCAT**.

    **About Dada2:**

    Dada2 turns single-end sequences into denoised, chimera-free, inferred sample sequences. The core denoising algorithm is built on a model of the errors in sequenced amplicon reads. For more information about Dada2, we suggest to read Benjamin J. Callahan *et al.*, 2016 (https://www.nature.com/articles/nmeth.3869)


    """
    input_specs: InputSpecs = InputSpecs({
        'quality_check_folder': InputSpec(Folder)
    })
    output_specs: OutputSpecs = OutputSpecs({
        'feature_table': OutputSpec(FeatureFrequencyTable),
        'stats': OutputSpec(Table),
        'result_folder': OutputSpec(Folder,
                                    short_description="Rarefaction curves folder. Can be used with taxonomy task (!no rarefaction are done on counts!))",
                                    human_name="Rarefaction_curves")
    })
    config_specs: ConfigSpecs = {
        "threads": IntParam(default_value=2, min_value=2, short_description="Number of threads"),
        "truncated_reads_size": IntParam(
            min_value=20, short_description="Read size to conserve after quality PHRED check in the previous step")}

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        qiime2_folder = inputs["quality_check_folder"]
        qiime2_folder_path = qiime2_folder.path
        thrds = params["threads"]
        truncated_reads_size = params["truncated_reads_size"]
        script_file_dir = os.path.dirname(os.path.realpath(__file__))

        shell_proxy = Qiime2ShellProxyHelper.create_proxy(self.message_dispatcher)
        outputs = self.run_cmd_single_end(shell_proxy,
                                          script_file_dir,
                                          qiime2_folder_path,
                                          truncated_reads_size,
                                          thrds
                                          )

        # Output formating and annotation

        annotated_outputs = self.outputs_annotation(outputs)

        return annotated_outputs

    def run_cmd_single_end(self, shell_proxy: ShellProxy,
                           script_file_dir: str,
                           qiime2_folder_path: str,
                           trct: int,
                           thrd: int
                           ) -> str:

        cmd_1 = [
            " bash ",
            os.path.join(script_file_dir, "./sh/1_qiime2_feature_freq_extraction_SE.sh"),
            qiime2_folder_path,
            trct,
            thrd
        ]
        self.log_info_message("[Step-1] : Qiime2 features inference")
        res = shell_proxy.run(cmd_1)
        if res != 0:
            raise Exception("First step did not finished")
        self.update_progress_value(90, "[Step-1] : Done")

        # This script perform Qiime2 demux , quality assessment
        cmd_2 = [
            "bash",
            os.path.join(script_file_dir, "./sh/2_qiime2_outputs_formating.sh"),
            qiime2_folder_path,
            shell_proxy.working_dir
        ]
        self.log_info_message("[Step-2] : Formating output files for data visualisation")
        res = shell_proxy.run(cmd_2)
        if res != 0:
            raise Exception("Second step did not finished")
        self.update_progress_value(100, "[Step-2] : Done")

        output_folder_path = os.path.join(shell_proxy.working_dir, "sample_freq_details")

        return output_folder_path

    def outputs_annotation(self, output_folder_path: str) -> TaskOutputs:

        result_file = Folder(output_folder_path)

        # create annotated feature table
        path = os.path.join(result_file.path, "denoising-stats.tsv")
        feature_table = TableImporter.call(File(path=path), {'delimiter': 'tab', "index_column": 0})

        path = os.path.join(result_file.path, "denoising-stats.tsv")
        stats_table = TableImporter.call(File(path=path), {'delimiter': 'tab', "index_column": 0})

        path = os.path.join(result_file.path, "gws_metadata.csv")
        metadata_table = TableImporter.call(File(path=path), {'delimiter': 'tab'})
        feature_table = TableAnnotatorHelper.annotate_rows(
            feature_table, metadata_table, use_table_row_names_as_ref=True)
        stats_table = TableAnnotatorHelper.annotate_rows(stats_table, metadata_table, use_table_row_names_as_ref=True)

        return {
            "result_folder": result_file,
            "stats": stats_table,
            "feature_table": feature_table
        }
