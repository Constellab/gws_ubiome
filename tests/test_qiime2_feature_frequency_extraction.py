import os

import pandas
from gws_core import BaseTestCase, Folder, Settings, TaskRunner
from gws_ubiome import Qiime2FeatureTableExtractorPE


class TestQiime2SampleFrequencies(BaseTestCase):
    def test_importer(self):
        settings = Settings.get_instance()
        large_testdata_dir = settings.get_variable("gws_ubiome", "large_testdata_dir")
        quality_check_folder = Folder(path=os.path.join(large_testdata_dir, "quality_check"))
        tester = TaskRunner(
            params={
                "threads": 2,
                "truncated_forward_reads_size": 270,
                "truncated_reverse_reads_size": 270,
            },
            inputs={"quality_check_folder": quality_check_folder},
            task_type=Qiime2FeatureTableExtractorPE,
        )
        outputs = tester.run()

        result_dir = outputs["result_folder"]

        feature_table = outputs["stats"]

        # get the generated output
        boxplot_csv_file_path = os.path.join(result_dir.path, "sample-frequency-detail.tsv")

        # get the expected output
        expected_file_path = os.path.join(
            large_testdata_dir, "sample_freq_details", "sample-frequency-detail.tsv"
        )

        t1 = pandas.read_csv(boxplot_csv_file_path, delimiter="\t")
        t2 = pandas.read_csv(expected_file_path, delimiter="\t")

        self.assertEqual(t1.shape, t2.shape)
