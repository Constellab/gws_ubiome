import os

import pandas
from gws_core import BaseTestCase, File, Folder, Settings, TaskRunner
from gws_ubiome import Qiime2DifferentialAnalysis


class TestQiime2TaxonomyDiversityExtractor(BaseTestCase):
    def test_importer(self):
        settings = Settings.get_instance()
        large_testdata_dir = settings.get_variable("gws_ubiome", "large_testdata_dir")
        if not large_testdata_dir or not os.path.isdir(large_testdata_dir):
            self.skipTest(f"large_testdata_dir not found: {large_testdata_dir}")
        taxonomy_diversity_folder = Folder(path=os.path.join(large_testdata_dir, "diversity"))
        metadata_file = File(path=os.path.join(large_testdata_dir, "metadata", "qiime2_metadata.csv"))
        tester = TaskRunner(
            params={"metadata_column": "subject", "threads": 2},
            inputs={
                "taxonomy_diversity_folder": taxonomy_diversity_folder,
                "metadata_file": metadata_file,
            },
            task_type=Qiime2DifferentialAnalysis,
        )
        outputs = tester.run()
        result_dir = outputs["result_folder"]

        boxplot_csv_file_path = os.path.join(result_dir.path, "percent-abundances.tsv")
        boxplot_csv = File(path=boxplot_csv_file_path)
        result_in_file = open(boxplot_csv_file_path, encoding="utf-8")
        result_first_line = result_in_file.readline()

        # Get the expected file output
        expected_file_path = os.path.join(
            large_testdata_dir, "diff-analysis", "percent-abundances.tsv"
        )
        expected_in_file = open(expected_file_path, encoding="utf-8")
        expected_first_line = expected_in_file.readline()

        self.assertEqual(expected_first_line, result_first_line)

        t1 = pandas.read_csv(boxplot_csv_file_path, delimiter="\t")
        t2 = pandas.read_csv(expected_file_path, delimiter="\t")

        self.assertEqual(t1.shape, t2.shape)


#        self.assertEqual(t1.iloc[0,:].to_list(), t2.iloc[0,:].to_list())
