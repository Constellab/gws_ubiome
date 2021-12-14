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
from ..file.qiime2_folder import Qiime2RarefactionFolder
from ..file.qiime2_folder import Qiime2SampleFrequenciesFolder


@task_decorator("Qiime2Rarefaction")
class Qiime2Rarefaction(Qiime2EnvTask):
    """
    Qiime2Rarefaction class. 
    
    Process that wraps QIIME2 program.

    [Mandatory]: 
        -  Qiime2SampleFrequencies output file (Qiime2SampleFrequencies-X-EndFolder)

    """
   

    input_specs = {
        'sample-frequencies_Result_Folder': (Qiime2SampleFrequenciesFolder,),
    }
    output_specs = {
        'result_folder': (Qiime2RarefactionFolder,)
    }
    config_specs = {
        "min_coverage": IntParam(min_value=20, short_description="Minimum read number to test"),
        "max_coverage": IntParam(min_value=20, short_description="Maximum read number value to test. Near to median value of the previous sample frequencies is advised")
    }
#        "e_value": FloatParam(default_value=0.00001, min_value=0.0, short_description="E-value : Default = 0.00001 (i.e 1e-5)"),
#        "threads": IntParam(default_value=4, min_value=2, short_description="Number of threads"),
       
    def gather_outputs(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        result_file = Qiime2RarefactionFolder()
        result_file.path = self._get_output_file_path()
        result_file.observed_features_table_path = "observed_features.for_boxplot.tsv"
        result_file.shannon_index_table_path = "shannon.for_boxplot.tsv"
        return {"result_folder": result_file} 
    
    def build_command(self, params: ConfigParams, inputs: TaskInputs) -> list:   
        quiime_folder = inputs["sample-frequencies_Result_Folder"]
        minDepth = params["min_coverage"]
        maxDepth = params["max_coverage"]

        self._output_file_path = self._get_output_file_path()
        script_file_dir = os.path.dirname(os.path.realpath(__file__))
        cmd = [ 
            " bash ", 
            os.path.join(script_file_dir, "./sh/3_qiime2_alpha_rarefaction.sh"),      
            quiime_folder.path,
            minDepth,
            maxDepth,
            os.path.join(script_file_dir, "./Perl/3_transform_table_for_boxplot.pl")
        ]
        
        return cmd


    def _get_output_file_path(self) :
        return os.path.join(self.working_dir, "rarefaction")