# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os

import pandas
from gws_core import BaseTestCase, File, Settings, TableExporter, TaskRunner
from gws_omix import FastqFolder
from gws_ubiome import Qiime2MetadataTableMaker


class TestQiime2MetadataMaker(BaseTestCase):

    async def test_importer(self):
        settings = Settings.retrieve()
        large_testdata_dir = settings.get_variable("gws_ubiome:large_testdata_dir")
        testdata_dir = settings.get_variable("gws_ubiome:testdata_dir")
        tester = TaskRunner(
            inputs={
                'fastq_folder': FastqFolder(path=os.path.join(large_testdata_dir,  "fastq_dir")),
            },
            task_type=Qiime2MetadataTableMaker
        )
        outputs = await tester.run()
        result = outputs['metadata_table']
        metadata_table_file = TableExporter.call(result, params={'delimiter': "tab", 'write_index': False})
        result_path = metadata_table_file.path
        result_file = open(result_path, 'r', encoding="utf-8")
        result_first_line = result_file.readline()
        result_content = result_file.read()

        expected_file_path = os.path.join(testdata_dir, "gws_metadata.csv")
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

        t1 = pandas.read_csv(result_path, delimiter="\t", comment="#")
        t2 = pandas.read_csv(expected_file_path, delimiter="\t", comment="#")

        self.assertEqual(t1.shape, t2.shape)
