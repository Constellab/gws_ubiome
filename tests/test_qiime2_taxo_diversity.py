
import os
from gws_core import Settings, TaskRunner, File, BaseTestCase, Folder, IntParam, ConfigParams, StrParam, TaskInputs, TaskOutputs, Utils, task_decorator
from gws_ubiome import FastqFolder, Qiime2RarefactionFolder, Qiime2Rarefaction, Qiime2TaxonomyDiversityFolder, Qiime2TaxonomyDiversity
import pandas


class TestQiime2TaxonomyDiversity(BaseTestCase):

    async def test_importer(self):        
        settings = Settings.retrieve()
        data_dir = settings.get_variable("gws_ubiome:testdata_dir")
        large_data_dir = settings.get_variable("gws_ubiome:large_testdata_dir")
        #/lab/user/bricks/gws_ubiome/tests/testdata/build/rarefaction
        tester = TaskRunner(
            params = {
                'rarefactionPlateauValue': 1673 ,
                'threads': 2
                },
            inputs = {
                 'Rarefaction_Result_Folder':   Qiime2RarefactionFolder(path=os.path.join(data_dir,"build","rarefaction"))
                },
            task_type = Qiime2TaxonomyDiversity
        ) 
        outputs = await tester.run()
        result_dir = outputs['result_folder']

#/lab/user/bricks/gws_ubiome/tests/testdata/build/diversity/table_files/level-1.tsv

        boxplot_csv_file_path = os.path.join(result_dir.path , "table_files", "level-1.tsv")
        boxplot_csv = File(path=boxplot_csv_file_path)
        resultInFile = open(boxplot_csv_file_path, 'r')
        resultFirstLine = resultInFile.readline()
        result_content = boxplot_csv.read()

            
        # Get the expected file output     
#        expectedDir = os.path.join(path=os.path.join(large_data_dir,"build","table_files"))  
        expected_file_path = os.path.join(data_dir,"build", "diversity", "table_files", "level-1.tsv")
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