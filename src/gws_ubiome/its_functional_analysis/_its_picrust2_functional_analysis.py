import subprocess
import sys
import os


class PipelineWorkflow:
    def __init__(self, input_file, seq_file, processes):
        self.input_file = input_file
        self.seq_file = seq_file
        self.output_dir = self.set_output_directory()
        self.processes = processes

    def set_output_directory(self):
        return "picrust2_out_pipeline"

    def run_picrust2_pipeline(self):
        cmd = [
            "picrust2_pipeline.py",
            "-s", self.seq_file,
            "-i", self.input_file,
            "-o", self.output_dir,
            "-p", str(self.processes),
            "--custom_trait_tables", "/lab/.sys/.env/Picrust2ShellProxy/.venv/lib/python3.8/site-packages/picrust2/default_files/fungi/ec_ITS_counts.txt.gz",
            "--min_reads", "1",
            "-r", "/lab/.sys/.env/Picrust2ShellProxy/.venv/lib/python3.8/site-packages/picrust2/default_files/fungi/fungi_ITS",
            "--marker_gene_table", "/lab/.sys/.env/Picrust2ShellProxy/.venv/lib/python3.8/site-packages/picrust2/default_files/fungi/ITS_counts.txt.gz",
            "--pathway_map", "/lab/.sys/.env/Picrust2ShellProxy/.venv/lib/python3.8/site-packages/picrust2/default_files/pathway_mapfiles/metacyc_path2rxn_struc_filt_fungi_present.txt",
            "--reaction_func", "/lab/.sys/.env/Picrust2ShellProxy/.venv/lib/python3.8/site-packages/picrust2/default_files/fungi/ec_ITS_counts.txt.gz"
        ]
        subprocess.run(cmd)

    def run(self):
        self.set_output_directory()
        self.run_picrust2_pipeline()


# Paths and parameters from command line arguments
# input_file = sys.argv[1]
# seq_file = sys.argv[2]
# num_processes = int(sys.argv[3])

# Execute the combined workflow
workflow = PipelineWorkflow(sys.argv[1], sys.argv[2], int(sys.argv[3]))
workflow.run()


