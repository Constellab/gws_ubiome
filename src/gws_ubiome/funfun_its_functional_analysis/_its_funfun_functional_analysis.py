import pandas as pd
import subprocess
import tempfile
import os
import sys


class OTUFilter:
    def __init__(self, input_file, fasta_file, its_type, output_folder):
        self.input_file = input_file
        self.fasta_file = fasta_file
        self.its_type = its_type
        self.output_folder = output_folder
        self.output_file = None
        self.output_fasta_file = None

    def filter_highest_otus(self):
        # Read the TSV file into a DataFrame, skipping the first line
        df = pd.read_csv(self.input_file, sep='\t', index_col='#OTU ID', skiprows=1)

        # Create a new DataFrame to store the highest OTU for each sample
        highest_otus_df = pd.DataFrame(columns=df.columns)

        # Iterate over each sample column
        for sample in df.columns:
            # Find the OTU with the highest count for the current sample
            highest_otu = df[sample].idxmax()

            # Add the highest OTU and its count to the new DataFrame
            highest_otus_df.loc[highest_otu, sample] = df.loc[highest_otu, sample]

        # Create temporary files for intermediate results
        _, self.output_file = tempfile.mkstemp(suffix=".tsv")
        _, self.output_fasta_file = tempfile.mkstemp(suffix=".fasta")

        # Write the new DataFrame to the temporary TSV file
        highest_otus_df.to_csv(self.output_file, sep='\t', index=True)

        # Read the sample-OTU mapping from the TSV file
        sample_otu_df = highest_otus_df

        # Read the FASTA file into a dictionary
        fasta_dict = {}
        current_otu = ""
        with open(self.fasta_file, "r") as fasta_file:
            for line in fasta_file:
                if line.startswith(">"):
                    current_otu = line.strip()[1:]
                else:
                    fasta_dict[current_otu] = line.strip()

        # Create a new dictionary with selected OTUs
        selected_fasta_dict = {}

        # Replace OTU IDs with sample names in the new dictionary
        for otu, sequence in fasta_dict.items():
            if otu in sample_otu_df.index:
                sample_names = sample_otu_df.columns[sample_otu_df.loc[otu].notnull()].tolist()
                if sample_names:
                    for sample_name in sample_names:
                        new_identifier = f">{sample_name}"
                        selected_fasta_dict[new_identifier] = sequence

        # Write the selected FASTA sequences to the temporary FASTA file
        with open(self.output_fasta_file, "w") as output_file:
            for identifier, sequence in selected_fasta_dict.items():
                output_file.write(f"{identifier}\n{sequence}\n")

    def run_funfun(self):
        # Example command: funfun -its /path/to/fasta/file.fasta -type its1 -out /path/to/output/folder
        command = [
            "funfun",
            "-its", self.output_fasta_file,
            "-type", self.its_type,
            "-out", self.output_folder
        ]
        subprocess.run(command)

    def clean_up(self):
        # Remove temporary files
        os.remove(self.output_file)
        os.remove(self.output_fasta_file)

    def execute(self):
        self.filter_highest_otus()
        self.run_funfun()
        self.clean_up()


# Example usage:
#input_file = sys.argv[1]
#fasta_file = sys.argv[2]
#its_type = str(sys.argv[3])

# Create an instance of OTUFilter
otu_filter = OTUFilter(sys.argv[1], sys.argv[2], str(sys.argv[3]), sys.argv[4])

# Execute the filtering, funfun command, and clean up temporary files
otu_filter.execute()
