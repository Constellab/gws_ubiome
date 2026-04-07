
import os

import pandas
from gws_core import BaseTestCase, Folder, TaskRunner
from gws_ubiome import Qiime2FeatureTableExtractorSE


class TestQiime2SampleFrequenciesSE(BaseTestCase):

    def test_importer(self):
        testdata_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "testdata"))
        test_folder_path = os.path.join(testdata_dir, "quality_check_2")
        quality_check_folder = Folder(path=test_folder_path)

        # Feature extraction requires a 'demux.qza' QIIME2 artifact in the folder
        if not os.path.exists(os.path.join(test_folder_path, "demux.qza")):
            self.skipTest("SE feature extraction requires 'demux.qza' in quality_check_2 — large testdata needed")
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
        testdata_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "testdata"))
        expected_file_path = os.path.join(testdata_dir, "sample_freq_details_2", "sample-frequency-detail.tsv")

        t1 = pandas.read_csv(boxplot_csv_file_path, delimiter="\t")
        t2 = pandas.read_csv(expected_file_path, delimiter="\t")

        self.assertEqual(t1.shape, t2.shape)
