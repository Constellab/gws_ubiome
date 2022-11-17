# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os

from gws_core import (ConfigParams, File, IntParam, MetadataTableImporter,
                      Table, TableImporter, TableRowAnnotatorHelper,
                      TaskInputs, TaskOutputs, task_decorator)
from gws_core.config.config_types import ConfigParams, ConfigSpecs
from gws_core.io.io_spec import InputSpec, OutputSpec
from gws_core.io.io_spec_helper import InputSpecs, OutputSpecs

from ..base_env.qiime2_env_task import Qiime2EnvTask
from ..feature_frequency_table.qiime2_feature_frequency_folder import \
    Qiime2FeatureFrequencyFolder
from ..quality_check.qiime2_quality_check_result_folder import \
    Qiime2QualityCheckResultFolder


@task_decorator("Qiime2FeatureTableExtractorPE",  human_name="Qiime2 feature inference (paired-end)",
                short_description="Infers ASVs from paired-end sequencing")
class Qiime2FeatureTableExtractorPE(Qiime2EnvTask):
    """
    Qiime2FeatureTableExtractorPE class.

    This task infers Amplicon Sequence Variants (ASVs) using the function ```qiime dada2 denoise-paired``` from Qiime2. This task starts by trimming and filtering sequences (see below) before joining paired reads to infer ASVs with DADA2 (The Divisive Amplicon Denoising Algorithm).

    **About trimming sequences:**

    It is convenient to ensure that paired-end reads overlap at least 12 nucleotides and that the quality of the reads does not fall below a PHRED score at 25 (corresponding to 1 incorrect base over a length of 320). To avoid problems in the determination of chimeras it is convenient to eliminate the first nucleotides as they may correspond to the primers that have been used in the 16S amplification.

    ```truncated_forward_reads_size``` and ```truncated_reverse_reads_size``` refer to the position at which forward/reverse read sequences should be *truncated* due to decrease in quality. This truncates the 3' end of sequences (i.e. the right side).

    ```5_prime_hard_trimming_reads_size``` refers to the position at which forward and reverse read sequences should be *trimmed* due to low quality. This trims the 5' end of the input sequences (i.e. the left side).

    If both truncLen and trimLeft are provided, filtered reads will have length truncLen-trimLeft.

    *Example*

    With the following sequence of 10 nucleotides **ATCATCATCG**, using ```truncated_forward_reads_size``` at 8 and ```5_prime_hard_trimming_reads_size``` at 2 will result in a sequence of 6 nucleotide **CATCAT**.

    **About Dada2:**

    Dada2 turns paired-end sequences into merged, denoised, chimera-free, inferred sample sequences. The core denoising algorithm is built on a model of the errors in sequenced amplicon reads. For more information about Dada2, we suggest to read Benjamin J. Callahan *et al.*, 2016 (https://www.nature.com/articles/nmeth.3869)

    """
    input_specs: InputSpecs = {
        'quality_check_folder': InputSpec(Qiime2QualityCheckResultFolder)
    }
    output_specs: OutputSpecs = {
        'feature_table': OutputSpec(Table),
        'stats': OutputSpec(Table),
        'result_folder':
        OutputSpec(
            Qiime2FeatureFrequencyFolder,
            short_description="Rarefaction curves folder. Can be used with taxonomy task (!no rarefaction are done on counts!))",
            human_name="Rarefaction_curves")}
    config_specs: ConfigSpecs = {
        "threads": IntParam(default_value=2, min_value=2, short_description="Number of threads"),
        "truncated_forward_reads_size": IntParam(min_value=20, short_description="Read size to conserve after quality PHRED check in the previous step"),
        "truncated_reverse_reads_size": IntParam(min_value=20, short_description="Read size to conserve after quality PHRED check in the previous step"),
        "5_prime_hard_trimming_reads_size": IntParam(optional=True, default_value=0, min_value=0, short_description="Read size to trim in 5prime")
    }

    def gather_outputs(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        result_file = Qiime2FeatureFrequencyFolder()
        result_file.path = self._get_output_file_path()

        # create annotated feature table
        path = os.path.join(result_file.path, "sample-frequency-detail.tsv")
        feature_table = TableImporter.call(File(path=path), {'delimiter': 'tab', "index_column": 0})

        path = os.path.join(result_file.path, "denoising-stats.tsv")
        stats_table = TableImporter.call(File(path=path), {'delimiter': 'tab', "index_column": 0})

        path = os.path.join(result_file.path, "gws_metadata.csv")
        metadata_table = MetadataTableImporter.call(File(path=path), {'delimiter': 'tab'})
        feature_table = TableRowAnnotatorHelper.annotate(feature_table, metadata_table)
        stats_table = TableRowAnnotatorHelper.annotate(stats_table, metadata_table)

        return {
            "result_folder": result_file,
            "stats": stats_table,
            "feature_table": feature_table
        }

    def build_command(self, params: ConfigParams, inputs: TaskInputs) -> list:
        qiime2_folder = inputs["quality_check_folder"]
        thrd = params["threads"]
        trct_forward = params["truncated_forward_reads_size"]
        trct_reverse = params["truncated_reverse_reads_size"]
        hard_trim = params["5_prime_hard_trimming_reads_size"]
        script_file_dir = os.path.dirname(os.path.realpath(__file__))
        if (hard_trim == 0):
            cmd = [
                " bash ",
                os.path.join(script_file_dir, "./sh/2_qiime2_feature_frequency_extraction_paired_end.sh"),
                qiime2_folder.path,
                trct_forward,
                trct_reverse,
                thrd
            ]

        else:
            cmd = [
                " bash ",
                os.path.join(script_file_dir, "./sh/2_qiime2_feature_frequency_extraction_paired_end.hard_trim.sh"),
                qiime2_folder.path,
                trct_forward,
                trct_reverse,
                thrd,
                hard_trim
            ]

        return cmd

    def _get_output_file_path(self):
        return os.path.join(
            self.working_dir,
            "sample_freq_details"
        )
