
import os

import pandas
from gws_core import BaseTestCase, File, Folder, Settings, TaskRunner

from gws_ubiome import Qiime2RarefactionAnalysis


class TestQiime2RarefactionAnalysis(BaseTestCase):

    def test_importer(self):
        settings = Settings.get_instance()
        large_testdata_dir = settings.get_variable("gws_ubiome:large_testdata_dir")
        tester = TaskRunner(
            params={
                'min_coverage': 20,
                'max_coverage': 5000
            },
            inputs={
                'feature_frequency_folder':   Folder(
                    path=os.path.join(large_testdata_dir, "sample_freq_details"))
            },
            task_type=Qiime2RarefactionAnalysis
        )
        outputs = tester.run()
        result_dir = outputs['result_folder']

        boxplot_csv_file_path = os.path.join(result_dir.path, "shannon.for_boxplot.csv")
        result_in_file = open(boxplot_csv_file_path, 'r', encoding="utf-8")
        result_first_line = result_in_file.readline()

        # Get the expected file output

        expected_first_line = '\t{"depth": 20 , "sample-id": "341F-785R-P01-A09-P17"}\t{"depth": 20 , "sample-id": "341F-785R-P01-E04-P26"}\t{"depth": 20 , "sample-id": "341F-785R-P01-G07-P20"}\t{"depth": 573 , "sample-id": "341F-785R-P01-A09-P17"}\t{"depth": 573 , "sample-id": "341F-785R-P01-E04-P26"}\t{"depth": 573 , "sample-id": "341F-785R-P01-G07-P20"}\t{"depth": 1126 , "sample-id": "341F-785R-P01-A09-P17"}\t{"depth": 1126 , "sample-id": "341F-785R-P01-E04-P26"}\t{"depth": 1126 , "sample-id": "341F-785R-P01-G07-P20"}\t{"depth": 1680 , "sample-id": "341F-785R-P01-A09-P17"}\t{"depth": 1680 , "sample-id": "341F-785R-P01-E04-P26"}\t{"depth": 1680 , "sample-id": "341F-785R-P01-G07-P20"}\t{"depth": 2233 , "sample-id": "341F-785R-P01-A09-P17"}\t{"depth": 2233 , "sample-id": "341F-785R-P01-E04-P26"}\t{"depth": 2233 , "sample-id": "341F-785R-P01-G07-P20"}\t{"depth": 2786 , "sample-id": "341F-785R-P01-A09-P17"}\t{"depth": 2786 , "sample-id": "341F-785R-P01-E04-P26"}\t{"depth": 2786 , "sample-id": "341F-785R-P01-G07-P20"}\t{"depth": 3340 , "sample-id": "341F-785R-P01-A09-P17"}\t{"depth": 3340 , "sample-id": "341F-785R-P01-E04-P26"}\t{"depth": 3340 , "sample-id": "341F-785R-P01-G07-P20"}\t{"depth": 3893 , "sample-id": "341F-785R-P01-A09-P17"}\t{"depth": 3893 , "sample-id": "341F-785R-P01-E04-P26"}\t{"depth": 3893 , "sample-id": "341F-785R-P01-G07-P20"}\t{"depth": 4446 , "sample-id": "341F-785R-P01-A09-P17"}\t{"depth": 4446 , "sample-id": "341F-785R-P01-E04-P26"}\t{"depth": 4446 , "sample-id": "341F-785R-P01-G07-P20"}\t{"depth": 5000 , "sample-id": "341F-785R-P01-A09-P17"}\t{"depth": 5000 , "sample-id": "341F-785R-P01-E04-P26"}\t{"depth": 5000 , "sample-id": "341F-785R-P01-G07-P20"}\n'

        self.assertEqual(expected_first_line, result_first_line)
        self.assertEqual((10, 31), pandas.read_csv(boxplot_csv_file_path, delimiter="\t").shape)
