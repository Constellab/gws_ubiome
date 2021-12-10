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
from ..file.fastq_folder import FastqFolder
from ..file.qiime1_folder import Qiime2QualityCheckResultFolder

@task_decorator("Qiime2QualityCheck")
class Qiime2QualityCheck(Qiime2EnvTask):
    """
    Qiime2 class. Represents a process that wraps Qiime2.

    """

    input_specs = {
        'sequencing_and_barcodes_fastq_folder': (FastqFolder,),
        'metadata_file': (MetadataFile,)
    }
    output_specs = {
        'result_folder': (Qiime2QualityCheckResultFolder,)
    }
    config_specs = {
        "sequencing_type": StrParam(default_value="paired-end",allowed_values=["paired-end","single-end"], short_description="Type of sequencing strategy [Respectivly, options : paired-end, single-end ]. Default = paired-end"),
        "barcode_column_name": StrParam(short_description="Barcode column name in the metadata file"),
        "project_id": StrParam(short_description="Project ID to name outputs")  

    }
       
    def gather_outputs(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        result_file = Qiime2QualityCheckResultFolder()
        result_file.path = self._output_file_path
        return {"result_folder": result_file} 
    
    def build_command(self, params: ConfigParams, inputs: TaskInputs) -> list:   
        fastq_folder = inputs["sequencing_and_barcodes_fastq_folder"]
        meta_data = inputs["metadata_file"]

        seq = params["sequencing_type"]
        proj_id = params["project_id"]
        barcode_colname = params["barcode_column_name"]

        if  seq == "paired-end":
            self._output_file_path = self._get_output_file_path(proj_id)
            script_file_dir = os.path.dirname(os.path.realpath(__file__))
            cmd = [ 
                " bash ", 
                os.path.join(script_file_dir, "./sh/qiime2_quality_paired_end_cmd.sh"),      
                fastq_folder.path, 
                meta_data.path,
                barcode_colname,
                proj_id
            ]
            
            return cmd

        else:
            self._output_file_path = self._get_output_file_path(proj_id)
            script_file_dir = os.path.dirname(os.path.realpath(__file__))
            cmd = [ 
                " bash ", 
                os.path.join(script_file_dir, "./sh/qiime2_quality_single_end_cmd.sh.sh"),      
                fastq_folder.path, 
                meta_data.path,
                barcode_colname,
                proj_id
            ]
            
            return cmd


    def _get_output_file_path(self, output_dir_name) :
        return os.path.join(
            self.working_dir, 
            output_dir_name + ".qiime.output.directory.part.1"
        )
