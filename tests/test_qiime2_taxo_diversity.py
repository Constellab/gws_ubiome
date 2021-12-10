
import os
from gws_core import Settings, TaskRunner, File, BaseTestCase, Folder
from gws_ubiome import MetadataFile
from gws_ubiome import Qiime2QualityCheckResultFolder
from gws_ubiome import Qiime2PartTwoPE
import pandas

class TestQiime2TaxoDiversity(BaseTestCase):

    async def test_importer(self):        
        settings = Settings.retrieve()
        data_dir = settings.get_variable("gws_ubiome:testdata_dir")
#        data_folder = FastqFolder()
#        data_folder.path = os.path.join(data_dir, "./fastq_dir_test")
#        metadata_file = MetadataFile()
#        metadata_file.path = os.path.join(data_dir, "./sample_metadata.tsv")
    input_specs = {
        'qiime_files_part1_folders': (Qiime2QualityCheckResultFolder,),
        'metadata_file': (MetadataFile,)
    }
    output_specs = {
        'qiime_files': (Folder,)
    }
    config_specs = {
        "barcode_column_name": StrParam(short_description="Barcode column name in the metadata file"),
        "project_id": StrParam(short_description="Project ID to name outputs") ,
        "truncF": IntParam(short_description="Size after truncated forward reads "),
        "truncR": IntParam(short_description="Size after truncated reverse reads ")
    }
   



        # run trainer
        tester = TaskRunner(
            params = {
                'truncF': '150',
                'truncR': '150',
                'barcode_column_name': 'barcode-sequence',
                'project_id': 'test-unit'
                },

            inputs = {
#                "sequencing_and_barcodes_fastq_folder": data_folder,
#                "metadata_file": metadata_file
                 'qiime_files_part1_folders':   FastqFolder(path=os.path.join(data_dir, "fastq_dir_test")),
                 'metadata_file':   MetadataFile(path=os.path.join(data_dir, "./sample_metadata.tsv"))
                },

            task_type = Qiime2QualityCheck
        )
        outputs = await tester.run()
        result_dir = outputs['result_folder']

        boxplot_csv_file_path = os.path.join(result_dir.path , "test-unit.forward_boxplot.csv")
        boxplot_csv = File(path=boxplot_csv_file_path)
        result_content = boxplot_csv.read()

        # out_result_file = os.path.join(data_dir, "expected_quality.csv")
        # with open(out_result_file, "w") as fp:
        #     fp.write(result_content)
            

        # Get the expected file output       
        expected_file_path = os.path.join(data_dir, "expected_quality.csv")
        expected_result_file = File(path=expected_file_path)
        expected_result_content = expected_result_file.read()

        print("----")
        print(result_content)
        print("----")
        print(expected_result_content)
        print("----")

        t1 = pandas.read_csv(boxplot_csv_file_path, delimiter="\t")
        t2 = pandas.read_csv(expected_file_path, delimiter="\t")

        self.assertEqual(t1.shape, t2.shape)
        self.assertEqual(t1.iloc[0,:].to_list(), t2.iloc[0,:].to_list())

        #self.assertEqual( result_content, expected_result_content  )
