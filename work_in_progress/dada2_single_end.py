# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json
import os
import re
import csv

from gws_core import task_decorator, File, ConfigParams, TaskInputs, TaskOutputs, Utils
from ..base_env.dada2_env_task import Dada2EnvTask
from ..file.trimmed_filtered_fastq_file import TrimmedFilteredFastqFile

@task_decorator("Dada2PairedEnd")
class Dada2PairedEnd(Dada2EnvTask):
    """
    Dada2 class. Represents a process that wraps Dada2 R package.

    """

    input_specs = {
        'trim_filtered_fastq_file': (TrimmedFilteredFastqFile,),
    }
    output_specs = {
        'dada2_files': (Folder,)
    }
    config_specs = {
        "sequence_type": StrParam(default_value="rRNA",allowed_values=["rRNA","ITS"], short_description="Type of sequence type sequenced. [Respectivly, options : rRNA, ITS ]. Default = rRNA"),
        "trimmed": StrParam(default_value="Yes",allowed_values=["Yes","No"], short_description="Adaptators have been trimmed from reads [Respectivly, options : Yes, No ]. Default = Yes"),
        "amplicon_length": IntParam(min_value=1, short_description="Amplicon size"),
        "read_length": IntParam(default_value=250, min_value=1, short_description="Read sequenced length in bp"),
        "overlap_size": IntParam(min_value=20, short_description="For paired-end sequencing, specify the expected reads overlap size in bp [min: 20 bp]"), 
        "max_sequencing_errors_forward": IntParam(default_value=2, min_value=0, short_description="For paired-end sequencing, specify the maximum sequencing error for the forward read in bp"),
        "max_sequencing_errors_reverse": IntParam(default_value=5, min_value=0, short_description="For paired-end sequencing, specify the maximum sequencing error for the reverse read in bp"),     
        "threads": IntParam(default_value=4, min_value=2, short_description="Number of threads")
    }
       
    def gather_outputs(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        result_file = DeepECFile()
        result_file.path = self._output_file_path
        return {"deepec_file": result_file} 
    
    def build_command(self, params: ConfigParams, inputs: TaskInputs) -> list:   
        fastq_file= inputs["fastq_file"]
        seq = params["sequence_type"]

        if  seq == "paired-end":

        else:

        fasta_file_name = os.path.basename(fasta_file.path)
        self._output_file_path = self._get_output_file_path(fasta_file_name)

        script_file_dir = os.path.dirname(os.path.realpath(__file__))
        cmd = [ 
            " bash ", 
            os.path.join(script_file_dir, "./sh/dada2_paired_end.sh"),    
            deepec_py,       
            fasta_file.path, 
            self.working_dir,
            self._output_file_path
        ]
          
        return cmd

    def _get_output_file_path(self, fasta_file_name) :
        return os.path.join(
            self.working_dir, 
            fasta_file_name + ".deepec_output"
        )
