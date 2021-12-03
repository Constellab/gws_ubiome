# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json
import os
import re
import csv

from gws_core import task_decorator, File, ConfigParams, TaskInputs, TaskOutputs, Utils, Folder, IntParam, StrParam
from ..base_env.qiime2_env_task import Qiime2EnvTask
from ..file.metadata_file import MetadataFile
from ..file.qiime1_folder import Qiime2QualityCheckResultFolder


@task_decorator("Qiime2PartTwoPE")
class Qiime2PartTwoPE(Qiime2EnvTask):
    """
    Qiime2 class. Represents a process that wraps Quiime2.

    """

    input_specs = {
        'qiime_files_part1_folders': (Qiime2QualityCheckResultFolder,),
        'metadata_file': (MetadataFile,)
    }
    output_specs = {
        'qiime_files': (Folder,)
    }
    config_specs = {
        "barcode_column_name": StrParam(short_description="Barcode column name in the metadata file"),
        "project_id": StrParam(short_description="Project ID to name outputs") ,
        "truncF": IntParam(short_description="Size after truncated forward reads "),
        "truncR": IntParam(short_description="Size after truncated reverse reads ")
    }
       
    def gather_outputs(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        result_file = Folder()
        result_file.path = self._output_file_path
        return {"qiime_files": result_file} 
    
    def build_command(self, params: ConfigParams, inputs: TaskInputs) -> list:   
        fastq_folder = inputs["fastq_files_folders"]
        meta_data = inputs["metadata_file"]

        seq = params["sequencing_type"]
        proj_id = params["project_id"]
        barcode_colname = params["barcode_column_name"]
        truncatedF = params["truncF"]
        truncatedR = params["truncR"]

        self._output_file_path = self._get_output_file_path(proj_id)
        script_file_dir = os.path.dirname(os.path.realpath(__file__))
        cmd = [ 
            " bash ", 
            os.path.join(script_file_dir, "./sh/qiime2_part2_PE_cmd.sh"),      
            fastq_folder.path, 
            meta_data.path,
            barcode_colname,
            proj_id,
            truncatedF,
            truncatedR
        ]
            



    def _get_output_file_path(self, output_dir_name) :
        return os.path.join(
            self.working_dir, 
            output_dir_name + ".qiime.output.directory.part.2"
        )
