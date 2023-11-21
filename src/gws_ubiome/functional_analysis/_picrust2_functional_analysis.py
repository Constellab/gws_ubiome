import subprocess
import sys
import os


class PipelineWorkflow:
    def __init__(self, input_file, seq_file, processes):
        self.input_file = input_file
        self.input_file_ext = os.path.splitext(input_file)[1]
        self.tsv_file = input_file if self.input_file_ext == '.biom' else input_file.replace('.csv', '.tsv')
        self.seq_file = seq_file
        self.output_dir = self.set_output_directory()
        self.processes = processes

    def csv_to_tsv(self):
        if self.input_file_ext != '.csv':
            return
        with open(self.input_file, 'r') as csv_in, open(self.tsv_file, 'w', newline='') as tsv_out:
            for line in csv_in:
                tsv_line = line.strip().replace(',', '\t')
                tsv_out.write(tsv_line + '\n')

    def set_output_directory(self):
        return "picrust2_out_pipeline"

    def run_picrust2_pipeline(self):

        cmd = [
            "picrust2_pipeline.py",
            "-s", self.seq_file,
            "-i", self.tsv_file,
            "-o", self.output_dir,
            "-p", str(self.processes)
        ]
        subprocess.run(cmd)

    def run(self):
        self.csv_to_tsv()
        self.set_output_directory()
        self.run_picrust2_pipeline()


# Paths and parameters from command line arguments
# input_file = sys.argv[1]
# seq_file = sys.argv[2]
# num_processes = int(sys.argv[3])

# Execute the combined workflow
workflow = PipelineWorkflow(sys.argv[1], sys.argv[2], int(sys.argv[3]))
workflow.run()
