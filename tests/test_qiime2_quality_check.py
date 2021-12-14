# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
import json
from gws_core import Settings, TaskRunner, File, BaseTestCase, Folder, GTest, ViewTester
from gws_ubiome import Qiime2ManifestTableFile, FastqFolder, Qiime2QualityCheckResultFolder, Qiime2QualityCheck
import pandas

class TestQiime2QualityCheck(BaseTestCase):

    async def test_importer(self):        
        settings = Settings.retrieve()
        testdata_dir = settings.get_variable("gws_ubiome:testdata_dir")
#        large_data_dir = settings.get_variable("gws_ubiome:large_testdata_dir")
        tester = TaskRunner(
            params = {
                'sequencing_type': 'paired-end'
                },
            inputs = {
#                 'fastq_folder':   FastqFolder(path=os.path.join(large_data_dir,"build","fastq_dir")),
#                 'metadata_file':   MetadataFile(path=os.path.join(large_data_dir, "manifest_test.txt"))
                 'fastq_folder':   FastqFolder(path=os.path.join(testdata_dir,"build","fastq_dir")),
                 'manifest_table_file':   Qiime2ManifestTableFile(path=os.path.join(testdata_dir, "manifest_test.txt"))                 
                },
            task_type = Qiime2QualityCheck
        )
        outputs = await tester.run()
        result_dir = outputs['result_folder']

        boxplot_csv_file_path = os.path.join(result_dir.path , "forward_boxplot.csv")
        boxplot_csv = File(path=boxplot_csv_file_path)
        resultInFile = open(boxplot_csv_file_path, 'r')
        resultFirstLine = resultInFile.readline()
        result_content = boxplot_csv.read()

#/lab/user/bricks/gws_ubiome/tests/testdata/build/quality-check            
        # Get the expected file output     
#        expectedDir.path = os.path.join(testdata_dir ,"build","quality-check") 
#        expectedDir = os.path.join(path=os.path.join(large_data_dir,"build","quality-check"))  
        expected_file_path = os.path.join(testdata_dir ,"build","quality-check", "forward_boxplot.csv")
        expectedInFile = open(expected_file_path, 'r')
        expectedFirstLine = expectedInFile.readline()

        expected_result_file = File(path=expected_file_path)
        expected_result_content = expected_result_file.read()

        print("----")
        print(result_content)
        print("----")
        print(expected_result_content)
        print("----")

        self.assertEqual(expectedFirstLine, resultFirstLine)

        t1 = pandas.read_csv(boxplot_csv_file_path, delimiter="\t")
        t2 = pandas.read_csv(expected_file_path, delimiter="\t")

        self.assertEqual(t1.shape, t2.shape)
#        self.assertEqual(t1.iloc[0,:].to_list(), t2.iloc[0,:].to_list())
