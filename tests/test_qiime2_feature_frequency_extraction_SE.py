
import os

import pandas
from gws_core import BaseTestCase, File, Settings, TaskRunner
from gws_ubiome import (Qiime2FeatureTableExtractorSE,
                        Qiime2QualityCheckResultFolder)


class TestQiime2SampleFrequenciesSE(BaseTestCase):

    def test_importer(self):
        settings = Settings.get_instance()
        large_testdata_dir = settings.get_variable("gws_ubiome:large_testdata_dir")
        test_folder_path = "/lab/user/bricks/gws_ubiome/tests/testdata/quality_check_2"
        quality_check_folder = Qiime2QualityCheckResultFolder(path=test_folder_path)
        # Qiime2QualityCheckResultFolder(path=os.path.join(large_testdata_dir, "quality_check"))
        tester = TaskRunner(
            params={
                'threads': 2,
                'truncated_reads_size': 270
            },
            inputs={
                'quality_check_folder':  quality_check_folder
            },
            task_type=Qiime2FeatureTableExtractorSE
        )
        outputs = tester.run()

        result_dir = outputs['result_folder']
        print(result_dir)

        feature_table = outputs['feature_table']
        print(feature_table)
        print(feature_table.get_row_tags())

        # get the generated output
        boxplot_csv_file_path = os.path.join(result_dir.path, "sample-frequency-detail.tsv")
        print(boxplot_csv_file_path)
        boxplot_csv = File(path=boxplot_csv_file_path)
        print(boxplot_csv)
        result_content = boxplot_csv.read()

        # get the expected output
        # expected_file_path = os.path.join(large_testdata_dir, "sample_freq_details", "sample-frequency-detail.tsv")
        expected_file_path = "/lab/user/bricks/gws_ubiome/tests/testdata/sample_freq_details_2/sample-frequency-detail.tsv"
        print(expected_file_path)
        expected_result_file = File(path=expected_file_path)
        expected_result_content = expected_result_file.read()

        print("----")
        print(result_content)
        print("----")
        print(expected_result_content)
        print("----")

        t1 = pandas.read_csv(boxplot_csv_file_path, delimiter="\t")
        t2 = pandas.read_csv(expected_file_path, delimiter="\t")

        self.assertEqual(t1.shape, t2.shape)
