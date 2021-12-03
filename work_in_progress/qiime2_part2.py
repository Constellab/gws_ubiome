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
from ..file.fastq_folder import FastqFolder


@task_decorator("Qiime2PartTwo")
class Qiime2PartTwo(Qiime2EnvTask):
    """
    Qiime2 class. Represents a process that wraps Dada2 R package.

    """

    input_specs = {
        'fastq_files_folders': (FastqFolder,),
        'metadata_file': (MetadataFile,)
    }
    output_specs = {
        'qiime_files': (Folder,)
    }
    config_specs = {
        "sequencing_type": StrParam(default_value="paired-end",allowed_values=["paired-end","single-end"], short_description="Type of sequencing strategy [Respectivly, options : paired-end, single-end ]. Default = paired-end"),
        "barcode_column_name": StrParam(short_description="Barcode column name in the metadata file"),
        "project_id": StrParam(short_description="Project ID to name outputs") ,
        "truncF": IntParam(short_description="Size after truncated forward reads "),
        "truncR": IntParam(short_description="Size after truncated reverse reads ")
    }
       
    def gather_outputs(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        result_file = DeepECFile()
        result_file.path = self._output_file_path
        return {"deepec_file": result_file} 
    
    def build_command(self, params: ConfigParams, inputs: TaskInputs) -> list:   
        fastq_folder = inputs["fastq_files_folders"]
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
