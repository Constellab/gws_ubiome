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
