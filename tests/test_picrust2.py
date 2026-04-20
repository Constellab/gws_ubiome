import os

from gws_core import BaseTestCase, File, Folder, TaskRunner
from gws_ubiome import Picrust2FunctionalAnalysis

TESTDATA = os.path.abspath(os.path.join(os.path.dirname(__file__), "testdata"))


class TestPicrust2FunctionalAnalysis(BaseTestCase):

    def test_functional_analysis(self):
        """Picrust2FunctionalAnalysis runs on mini ASV count table (.tsv) + sequences FASTA."""
        self.print("Test Picrust2FunctionalAnalysis: mini_asv_counts.tsv + mini_asv_sequences.fasta")

        asv_counts = os.path.join(TESTDATA, "mini_asv_counts.tsv")
        asv_fasta = os.path.join(TESTDATA, "mini_asv_sequences.fasta")

        if not os.path.exists(asv_counts) or not os.path.exists(asv_fasta):
            self.skipTest("Picrust2 testdata not found (mini_asv_counts.tsv / mini_asv_sequences.fasta)")

        outputs = TaskRunner(
            task_type=Picrust2FunctionalAnalysis,
            inputs={
                "ASV_count_abundance": File(asv_counts),
                "FASTA_of_asv": File(asv_fasta),
            },
            params={"num_processes": 2},
        ).run()

        result_folder: Folder = outputs["Folder_result"]
        self.assertIsNotNone(result_folder)
        self.assertTrue(os.path.isdir(result_folder.path), msg="picrust2 output folder should exist")

        output_files = []
        for root, dirs, files in os.walk(result_folder.path):
            output_files.extend(files)
        self.print(f"picrust2 output files: {output_files}")
        self.assertGreater(len(output_files), 0, msg="Expected at least one output file from picrust2")
