# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import File, resource_decorator, Folder, BarPlotView, view, TableFile, Table, TableView

@resource_decorator("Qiime2QualityCheckResultFolder",
                    human_name="Qiime2QualityCheckResultFolder",
                    short_description="Qiime2QualityCheckResultFolder")
class Qiime2QualityCheckResultFolder(Folder):
    ''' Qiime2QualityCheckResultFolder Folder file class '''

    fasta_file: str = StrRField()

    @view(view_type=TableView, 
            human_name='Table', 
            short_description='View as table', 
            specs={
                "file_type": StrParam(allowed_values=["fasta","quality"])
            }
    )
    def view_as_table(sefl, params: ConfigParam) -> TableView:
        file_type = params["file_type"]
        if file_type == "fasta":
            table_file = TableFile(os.path.join(path=self.fasta_file))
        else:
            pass
        table: Table = table_file.read()
        return TableView(data=table.get_data())

    @view(view_type=BoxPlotView)
    def view_as_table(sefl) -> BoxPlotView:
        table_file = TableFile(path=self.path, '.csv')
        table: Table = table_file.read()
        return BoxPlotView(data=table.get_data())

@resource_decorator("Qiime2SampleFrequenciesFolder",
                    human_name="Qiime2SampleFrequenciesFolder",
                    short_description="Qiime2SampleFrequenciesFolder")
class Qiime2SampleFrequenciesFolder(Folder):
    ''' Qiime2SampleFrequenciesFolder Folder file class '''



@resource_decorator("Qiime2RarefactionFolder",
                    human_name="Qiime2RarefactionFolder",
                    short_description="Qiime2RarefactionFolder")
class Qiime2RarefactionFolder(Folder):
    ''' Qiime2RarefactionFolder Folder file class '''

@resource_decorator("Qiime2TaxonomyDiversityFolder",
                    human_name="Qiime2TaxonomyDiversityFolder",
                    short_description="Qiime2TaxonomyDiversityFolder")
class Qiime2TaxonomyDiversityFolder(Folder):
    ''' Qiime2TaxonomyDiversityFolder Folder file class '''
