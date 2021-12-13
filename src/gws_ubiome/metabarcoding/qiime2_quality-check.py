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
    Qiime2QualityCheck class. 
    
    Process that wraps QIIME2 program.

    [Mandatory]: 
        - fastq_folder must contains all fastq files (paired or not).

        - metadata file must follow specific nomenclature (columns are tab separated), including $PWD/*/ before file names :

            For paired-end files :
                sample-id   forward-absolute-filepath   reverse-absolute-filepath
                sample-1    $PWD/*/sample0_R1.fastq.gz  $PWD/*/sample1_R2.fastq.gz
                sample-2    $PWD/*/sample2_R1.fastq.gz  $PWD/*/sample2_R2.fastq.gz
                sample-3    $PWD/*/sample3_R1.fastq.gz  $PWD/*/sample3_R2.fastq.gz

            For single-end files :
                sample-id   absolute-filepath
                sample-1    $PWD/*/sample0.fastq.gz
                sample-2    $PWD/*/sample2.fastq.gz
                sample-3    $PWD/*/sample3.fastq.gz

    """
   

    input_specs = {
        'fastq_folder': (FastqFolder,),
        'metadata_file': (MetadataFile,)
    }
    output_specs = {
        'result_folder': (Qiime2QualityCheckResultFolder,)
    }
    config_specs = {
        "sequencing_type": StrParam(default_value="paired-end",allowed_values=["paired-end","single-end"], short_description="Type of sequencing strategy [Respectivly, options : paired-end, single-end ]. Default = paired-end"),
        "project_id": StrParam(short_description="Project ID to name outputs")  
    }
       
    def gather_outputs(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        result_file = Qiime2QualityCheckResultFolder()
        result_file.path = self._output_file_path
        result_file.forward_reads_file = "forward-seven-number-summaries.tsv"
        result_file.reverse_reads_file = "reverse-seven-number-summaries.tsv"
        return {"result_folder": result_file} 
    
    def build_command(self, params: ConfigParams, inputs: TaskInputs) -> list:   
        fastq_folder = inputs["fastq_folder"]
        meta_data = inputs["metadata_file"]

        seq = params["sequencing_type"]
        proj_id = params["project_id"]

        if  seq == "paired-end":
            self._output_file_path = self._get_output_file_path(proj_id)
            script_file_dir = os.path.dirname(os.path.realpath(__file__))
            cmd = [ 
                " bash ", 
                os.path.join(script_file_dir, "./sh/1_qiime2_demux_trimmed_import.paired_end.sh"),      
                fastq_folder.path, 
                meta_data.path,
                proj_id
            ]
            
            return cmd

        else:
            self._output_file_path = self._get_output_file_path(proj_id)
            script_file_dir = os.path.dirname(os.path.realpath(__file__))
            cmd = [ 
                " bash ", 
                os.path.join(script_file_dir, "./sh/1_qiime2_demux_trimmed_import.single_end.sh"),      
                fastq_folder.path, 
                meta_data.path,
                proj_id
            ]
            
            return cmd


    def _get_output_file_path(self, output_dir_name) :
        return os.path.join(
            self.working_dir, 
            output_dir_name + ".qiime2.import.quality-check"
        )
