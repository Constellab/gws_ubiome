import os

import pandas
from gws_core import BaseTestCase, File, Settings, TaskRunner
from gws_omix import FastqFolder
from gws_ubiome import Qiime2QualityCheck


# gws_ubiome/test_qiime2_quality_check
class TestQiime2QualityCheck(BaseTestCase):
    def test_quality_check(self):
        settings = Settings.get_instance()
        large_testdata_dir = settings.get_variable("gws_ubiome", "large_testdata_dir")
        testdata_dir = settings.get_variable("gws_ubiome", "testdata_dir")

        metadata_file: File = File(path=os.path.join(testdata_dir, "gws_metadata.csv"))

        tester = TaskRunner(
            params={"sequencing_type": "paired-end"},
            inputs={
                "fastq_folder": FastqFolder(path=os.path.join(large_testdata_dir, "fastq_dir")),
                "metadata_table": metadata_file,
            },
            task_type=Qiime2QualityCheck,
        )
        outputs = tester.run()
        result_dir = outputs["result_folder"]

        boxplot_csv_file_path = os.path.join(result_dir.path, "forward_boxplot.csv")
        boxplot_csv = File(path=boxplot_csv_file_path)
        result_in_file = open(boxplot_csv_file_path, encoding="utf-8")
        result_first_line = result_in_file.readline()
        result_content = boxplot_csv.read()

        expected_file_path = os.path.join(
            large_testdata_dir, "quality_check", "forward_boxplot.csv"
        )
        expected_in_file = open(expected_file_path, encoding="utf-8")
        expected_first_line = expected_in_file.readline()

        self.assertEqual(expected_first_line, result_first_line)

        t1 = pandas.read_csv(boxplot_csv_file_path, delimiter="\t")
        t2 = pandas.read_csv(expected_file_path, delimiter="\t")

        self.assertEqual(t1.shape, t2.shape)

        # # create test_datadir
        # shutil.copytree(
        #     result_dir.path,
        #     "/data/gws_ubiome/testdata/quality_check/"
        # )
