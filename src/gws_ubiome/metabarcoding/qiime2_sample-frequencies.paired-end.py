# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json
import os
import re
import csv

from gws_core import task_decorator, File, ConfigParams, StrParam, TaskInputs, TaskOutputs, Utils, Folder
from ..base_env.qiime2_env_task import Qiime2EnvTask
from ..file.metadata_file import MetadataFile
from ..file.qiime_folder import Qiime2QualityCheckResultFolder
from ..file.qiime_folder import Qiime2SampleFrequenciesFolder


@task_decorator("Qiime2SampleFrequencies")
class Qiime2SampleFrequencies(Qiime2EnvTask):
    """
    Qiime2SampleFrequencies class. 
    
    Process that wraps QIIME2 program.

    [Mandatory]: 
        -  Qiime2QualityCheck output file (Qiime2QualityCheckResultFolder)

    """
   

    input_specs = {
        'Qiime2_Quality-Check_Result_Folder': (Qiime2QualityCheckResultFolder,),
    }
    output_specs = {
        'result_folder': (Qiime2SampleFrequenciesFolder,)
    }
    config_specs = {
        "project_id": StrParam(short_description="Project ID to name outputs"),
        "truncatedForwardReadsSize": IntParam(min_value=20, short_description="Read size to conserve after quality PHRED check in the previous step"),
        "truncatedReverseReads": IntParam(min_value=20, short_description="Read size to conserve after quality PHRED check in the previous step")
    }
#        "e_value": FloatParam(default_value=0.00001, min_value=0.0, short_description="E-value : Default = 0.00001 (i.e 1e-5)"),
#        "threads": IntParam(default_value=4, min_value=2, short_description="Number of threads"),
       
    def gather_outputs(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        result_file = Qiime2SampleFrequenciesFolder()
        result_file.path = self._output_file_path
        return {"result_folder": result_file} 
    
    def build_command(self, params: ConfigParams, inputs: TaskInputs) -> list:   
        qiime2_folder = inputs["Qiime2_Quality-Check_Result_Folder"]
        proj_id = params["project_id"]
        trctF = params["truncatedForwardReadsSize"]
        trctR = params["truncatedReverseReadsSize"]

        self._output_file_path = self._get_output_file_path(proj_id)
        script_file_dir = os.path.dirname(os.path.realpath(__file__))
        cmd = [ 
            " bash ", 
            os.path.join(script_file_dir, "./sh/2_qiime2_sample_frequencies.paired-end.sh"),      
            qiime2_folder.path, 
            proj_id,
            trctF,
            trctR
        ]
        
        return cmd


    def _get_output_file_path(self, output_dir_name) :
        return os.path.join(
            self.working_dir, 
            output_dir_name + ".qiime2.output.sample_freq_details"
        )
