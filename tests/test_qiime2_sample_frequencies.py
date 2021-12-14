
import os
from gws_core import Settings, TaskRunner, File, BaseTestCase, Folder, IntParam, ConfigParams, StrParam, TaskInputs, TaskOutputs, Utils, task_decorator
from gws_ubiome import FastqFolder, Qiime2QualityCheckResultFolder, Qiime2QualityCheck,  Qiime2SampleFrequenciesFolder, Qiime2SampleFrequenciesPE
import pandas


class TestQiime2SampleFrequencies(BaseTestCase):

    async def test_importer(self):        
        settings = Settings.retrieve()
        data_dir = settings.get_variable("gws_ubiome:testdata_dir")
#        large_data_dir = settings.get_variable("gws_ubiome:large_testdata_dir")
        #/lab/user/bricks/gws_ubiome/tests/testdata/build/quality-check
        tester = TaskRunner(
            params = {
                'threads': 2 ,
                'truncatedForwardReadsSize': 270 ,
                'truncatedReverseReadsSize': 270
                },
            inputs = {
                 'Quality-Check_Result_Folder':   Qiime2QualityCheckResultFolder(path=os.path.join(data_dir,"build","quality-check"))
                },
            task_type = Qiime2SampleFrequenciesPE
        ) 
        outputs = await tester.run()
        result_dir = outputs['result_folder']

#/lab/user/bricks/gws_ubiome/tests/testdata/build/sample_freq_details/sample-frequency-detail.tsv

        boxplot_csv_file_path = os.path.join(result_dir.path , "sample-frequency-detail.tsv")
        boxplot_csv = File(path=boxplot_csv_file_path)
        resultInFile = open(boxplot_csv_file_path, 'r')
        resultFirstLine = resultInFile.readline()
        result_content = boxplot_csv.read()

            
        # Get the expected file output     
#        expectedDir = os.path.join(path=os.path.join(data_dir,"build","sample_freq_details"))  
        expected_file_path = os.path.join(data_dir,"build","sample_freq_details", "sample-frequency-detail.tsv")
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
