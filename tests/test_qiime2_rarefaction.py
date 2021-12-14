
import os
from gws_core import Settings, TaskRunner, File, BaseTestCase, Folder, IntParam, ConfigParams, StrParam, TaskInputs, TaskOutputs, Utils, task_decorator
from gws_ubiome import FastqFolder, Qiime2SampleFrequenciesFolder, Qiime2SampleFrequenciesPE, Qiime2RarefactionFolder, Qiime2Rarefaction
import pandas


class TestQiime2Rarefaction(BaseTestCase):

    async def test_importer(self):        
        settings = Settings.retrieve()
        data_dir = settings.get_variable("gws_ubiome:testdata_dir")
        large_data_dir = settings.get_variable("gws_ubiome:large_testdata_dir")
        #/lab/user/bricks/gws_ubiome/tests/testdata/build/sample_freq_details
        tester = TaskRunner(
            params = {
                'min_coverage': 20 ,
                'max_coverage': 5000
                },
            inputs = {
                 'sample-frequencies_Result_Folder':   Qiime2SampleFrequenciesFolder(path=os.path.join(data_dir,"build","sample_freq_details"))
                },
            task_type = Qiime2Rarefaction
        ) 
        outputs = await tester.run()
        result_dir = outputs['result_folder']

#/lab/user/bricks/gws_ubiome/tests/testdata/build/rarefaction/shannon.for_boxplot.tsv

        boxplot_csv_file_path = os.path.join(result_dir.path , "shannon.for_boxplot.tsv")
        boxplot_csv = File(path=boxplot_csv_file_path)
        resultInFile = open(boxplot_csv_file_path, 'r')
        resultFirstLine = resultInFile.readline()
        result_content = boxplot_csv.read()

            
        # Get the expected file output     
#        expectedDir = os.path.join(path=os.path.join(large_data_dir,"build","rarefaction"))  
        expected_file_path = os.path.join(data_dir,"build","rarefaction", "shannon.for_boxplot.tsv")
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
