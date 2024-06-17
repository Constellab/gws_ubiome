
import os

import pandas
from gws_core import BaseTestCase, File, Folder, Settings, TaskRunner

from gws_ubiome import Qiime2FeatureTableExtractorSE


class TestQiime2SampleFrequenciesSE(BaseTestCase):

    def test_importer(self):
        test_folder_path = "/lab/user/bricks/gws_ubiome/tests/testdata/quality_check_2"
        quality_check_folder = Folder(path=test_folder_path)
        # Folder(path=os.path.join(large_testdata_dir, "quality_check"))
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

        # get the generated output
        boxplot_csv_file_path = os.path.join(result_dir.path, "sample-frequency-detail.tsv")

        # get the expected output
        # expected_file_path = os.path.join(large_testdata_dir, "sample_freq_details", "sample-frequency-detail.tsv")
        expected_file_path = "/lab/user/bricks/gws_ubiome/tests/testdata/sample_freq_details_2/sample-frequency-detail.tsv"

        t1 = pandas.read_csv(boxplot_csv_file_path, delimiter="\t")
        t2 = pandas.read_csv(expected_file_path, delimiter="\t")

        self.assertEqual(t1.shape, t2.shape)
