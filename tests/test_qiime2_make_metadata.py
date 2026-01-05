import os

import pandas
from gws_core import BaseTestCase, Settings, TaskRunner
from gws_omix import FastqFolder
from gws_ubiome import Qiime2MetadataTableMaker


class TestQiime2MetadataMaker(BaseTestCase):
    def test_importer(self):
        settings = Settings.get_instance()
        large_testdata_dir = settings.get_variable("gws_ubiome", "large_testdata_dir")
        testdata_dir = settings.get_variable("gws_ubiome", "testdata_dir")
        tester = TaskRunner(
            inputs={
                "fastq_folder": FastqFolder(path=os.path.join(large_testdata_dir, "fastq_dir")),
            },
            task_type=Qiime2MetadataTableMaker,
        )
        outputs = tester.run()
        result = outputs["metadata_table"]

        result_path = result.path
        result_file = open(result_path, encoding="utf-8")
        result_first_line = result_file.readline()

        expected_file_path = os.path.join(testdata_dir, "gws_metadata.csv")
        expected_in_file = open(expected_file_path, encoding="utf-8")
        expected_first_line = expected_in_file.readline()

        self.assertEqual(expected_first_line, result_first_line)

        t1 = pandas.read_csv(result_path, delimiter="\t", comment="#")
        t2 = pandas.read_csv(expected_file_path, delimiter="\t", comment="#")

        self.assertEqual(t1.shape, t2.shape)
        self.assertEqual(t1.columns.tolist(), t2.columns.tolist())
        self.assertEqual(
            list(t1["forward-absolute-filepath"]), list(t2["forward-absolute-filepath"])
        )
        self.assertEqual(
            list(t1["reverse-absolute-filepath"]), list(t2["reverse-absolute-filepath"])
        )
