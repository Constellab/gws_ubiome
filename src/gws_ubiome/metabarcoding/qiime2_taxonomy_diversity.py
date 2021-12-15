# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json
import os
import re
import csv

from gws_core import task_decorator, File, ConfigParams, StrParam, TaskInputs, TaskOutputs, Utils, Folder, IntParam
from ..base_env.qiime2_env_task import Qiime2EnvTask
#from ..file.metadata_file import MetadataFile
from ..file.qiime2_folder import Qiime2RarefactionFolder, Qiime2TaxonomyDiversityFolder


@task_decorator("Qiime2TaxonomyDiversity")
class Qiime2TaxonomyDiversity(Qiime2EnvTask):
    """
    Qiime2TaxonomyDiversity class. 
    
    Process that wraps QIIME2 program.

    [Mandatory]: 
        -  Qiime2SampleFrequencies output file (Qiime2SampleFrequencies-X-EndFolder)

    """
   

    input_specs = {
        'Rarefaction_Result_Folder': (Qiime2RarefactionFolder,),
    }
    output_specs = {
        'result_folder': (Qiime2TaxonomyDiversityFolder,)
    }
    config_specs = {
        "rarefactionPlateauValue": IntParam(min_value=20, short_description="Depth of coverage when reaching the plateau of the curve on the previous step"),
        "threads": IntParam(default_value=4, min_value=2, short_description="Number of threads")
    }
       
    def gather_outputs(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        result_file = Qiime2TaxonomyDiversityFolder()
        
        result_file.path = self._output_file_path
        
        # Table Files

        result_file.bray_curtis_table_path="/table_files/bray_curtis_distance_matrix.qza.diversity_metrics.bray_curtis_distance_matrix.qza.diversity_metrics.tsv"
        result_file.chao_1_table_path="/table_files/chao1.qza.diversity_metrics.chao1.qza.diversity_metrics.tsv"
        result_file.evenness_table_path="/table_files/evenness_vector.qza.diversity_metrics.evenness_vector.qza.diversity_metrics.tsv"
        result_file.faith_pd_table_path="/table_files/faith_pd_vector.qza.diversity_metrics.faith_pd_vector.qza.diversity_metrics.tsv"
        result_file.feature_freq_detail_table_path="/table_files/feature-frequency-detail.tsv"
        result_file.inv_simpson_table_path="/table_files/invSimpson.tab.tsv"
        result_file.jaccard_distance_table_path="/table_files/"
        result_file.jaccard_unweighted_unifrac_distance_table_path="/table_files/jaccard_distance_matrix.qza.diversity_metrics.jaccard_distance_matrix.qza.diversity_metrics.tsv"
        result_file.taxo_level_1_table_path="/table_files/level-1.tsv"
        result_file.taxo_level_2_table_path="/table_files/level-2.tsv"
        result_file.taxo_level_3_table_path="/table_files/level-3.tsv"
        result_file.taxo_level_4_table_path="/table_files/level-4.tsv"
        result_file.taxo_level_5_table_path="/table_files/level-5.tsv"
        result_file.taxo_level_6_table_path="/table_files/level-6.tsv"
        result_file.taxo_level_7_table_path="/table_files/level-7.tsv"
        result_file.observed_features_vector_table_path="/table_files/observed_features_vector.qza.diversity_metrics.observed_features_vector.qza.diversity_metrics.tsv"
        result_file.shannon_vector_table_path="/table_files/shannon_vector.qza.diversity_metrics.shannon_vector.qza.diversity_metrics.tsv"
        result_file.simpson_table_path="/table_files/simpson.qza.diversity_metrics.simpson.qza.diversity_metrics.tsv"
        result_file.unweighted_unifrac_distance_table_path="/table_files/unweighted_unifrac_distance_matrix.qza.diversity_metrics.unweighted_unifrac_distance_matrix.qza.diversity_metrics.tsv"
        result_file.weighted_unifrac_distance_table_path="/table_files/weighted_unifrac_distance_matrix.qza.diversity_metrics.weighted_unifrac_distance_matrix.qza.diversity_metrics.tsv"

        return {"result_folder": result_file} 
    
    def build_command(self, params: ConfigParams, inputs: TaskInputs) -> list:   
        qiime2_folder = inputs["Rarefaction_Result_Folder"]
        plateauVal = params["rarefactionPlateauValue"]
        thrds = params["threads"]
        db_gg_path = "/lab/user/bricks/gws_ubiome/tests/testdata/build/gg-13-8-99-nb-classifier.qza" # Temporary
        self._output_file_path = self._get_output_file_path()
        script_file_dir = os.path.dirname(os.path.realpath(__file__))
        cmd = [ 
            " bash ", 
            os.path.join(script_file_dir, "./sh/4_qiime2.taxonomy_diversity.sh"),      
            qiime2_folder.path,
            plateauVal,
            thrds,
            db_gg_path
        ]
        
        return cmd


    def _get_output_file_path(self) :
        return os.path.join(
            self.working_dir, 
            "diversity"
        )
