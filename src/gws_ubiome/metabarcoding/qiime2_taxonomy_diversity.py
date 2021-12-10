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
from ..file.qiime_folder import Qiime2RarefactionFolder
from ..file.qiime_folder import Qiime2TaxonomyDiversityFolder


@task_decorator("Qiime2Rarefaction")
class Qiime2Rarefaction(Qiime2EnvTask):
    """
    Qiime2Rarefaction class. 
    
    Process that wraps QIIME2 program.

    [Mandatory]: 
        -  Qiime2SampleFrequencies output file (Qiime2SampleFrequencies-X-EndFolder)

    """
   

    input_specs = {
        'Qiime2_Rarefaction_Result_Folder': (Qiime2RarefactionFolder,),
    }
    output_specs = {
        'result_folder': (Qiime2TaxonomyDiversityFolder,)
    }
    config_specs = {
        "project_id": StrParam(short_description="Project ID to name outputs"),
        "rareficationPlateauValue": IntParam(min_value=20, short_description="Depth of coverage when reaching the plateau of the curve on the previous step"),
        "threads": IntParam(default_value=4, min_value=2, short_description="Number of threads"),
    }
       
    def gather_outputs(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        result_file = Qiime2TaxonomyDiversityFolder()
        result_file.path = self._output_file_path
        return {"result_folder": result_file} 
    
    def build_command(self, params: ConfigParams, inputs: TaskInputs) -> list:   
        quiime_folder = inputs["Qiime2_Rarefaction_Result_Folder"]
        proj_id = params["project_id"]
        plateauVal = params["rareficationPlateauValue"]
        thrds = params["threads"]

        self._output_file_path = self._get_output_file_path(proj_id)
        script_file_dir = os.path.dirname(os.path.realpath(__file__))
        cmd = [ 
            " bash ", 
            os.path.join(script_file_dir, "./sh/4_qiime2.taxonomy_diversity.sh"),      
            quiime_folder.path,
            proj_id,
            plateauVal,
            thrds

        ]
        
        return cmd


    def _get_output_file_path(self, output_dir_name) :
        return os.path.join(
            self.working_dir, 
            output_dir_name + ".core-metrics-results"
        )
