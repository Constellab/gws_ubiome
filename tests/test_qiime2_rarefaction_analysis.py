
import os

import pandas
from gws_core import BaseTestCase, File, Settings, TaskRunner
from gws_ubiome import Qiime2FeatureFrequencyFolder, Qiime2RarefactionAnalysis


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
                'feature_frequency_folder':   Qiime2FeatureFrequencyFolder(
                    path=os.path.join(large_testdata_dir, "sample_freq_details"))
            },
            task_type=Qiime2RarefactionAnalysis
        )
        outputs = tester.run()
        result_dir = outputs['result_folder']

        boxplot_csv_file_path = os.path.join(result_dir.path, "shannon.for_boxplot.tsv")
        boxplot_csv = File(path=boxplot_csv_file_path)
        result_in_file = open(boxplot_csv_file_path, 'r', encoding="utf-8")
        result_first_line = result_in_file.readline()
        result_content = boxplot_csv.read()

        # Get the expected file output
        expected_file_path = os.path.join(large_testdata_dir, "rarefaction", "shannon.for_boxplot.tsv")
        expected_in_file = open(expected_file_path, 'r', encoding="utf-8")
        expected_first_line = expected_in_file.readline()

        expected_result_file = File(path=expected_file_path)
        expected_result_content = expected_result_file.read()

        print("----")
        print(result_content)
        print("----")
        print(expected_result_content)
        print("----")

        self.assertEqual(expected_first_line, result_first_line)

        t1 = pandas.read_csv(boxplot_csv_file_path, delimiter="\t")
        t2 = pandas.read_csv(expected_file_path, delimiter="\t")

        self.assertEqual(t1.shape, t2.shape)
#        self.assertEqual(t1.iloc[0,:].to_list(), t2.iloc[0,:].to_list())
