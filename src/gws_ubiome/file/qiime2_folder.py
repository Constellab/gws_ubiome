# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import (File, resource_decorator, Folder, BarPlotView, 
                        view, File, Table, TableView, BoxPlotView, MultiViews, StrRField, ConfigParams)



## Qiime 2 : output formats

## STEP 1 : Qiime2QualityCheck -> Result Folder

@resource_decorator("Qiime2QualityCheckResultFolder",
                    human_name="Qiime2QualityCheckResultFolder",
                    short_description="Qiime2QualityCheckResultFolder", hide=True)
class Qiime2QualityCheckResultFolder(Folder):
    ''' Qiime2QualityCheckResultFolder Folder file class '''

    forward_reads_file_path: str = StrRField() # raw boxplot quartile positions (i.e boxplot already done)
    reverse_reads_file_path: str = StrRField() # ''

    @view(view_type=TableView, human_name='ForwardQualityTable', short_description='Table view forward reads quality')
    def view_as_table_forward(self, params: ConfigParams) -> TableView:
        table: Table = Table.import_from_path(
            file=File(path=self.forward_reads_file_path),
            params = ConfigParams({})
        )
        return TableView(data=table.get_data())

    @view(view_type=BoxPlotView)
    def view_as_boxplot_forward(self) -> BoxPlotView:
        table: Table = Table.import_from_path(
            file=File(path=self.forward_reads_file_path),
            params = ConfigParams({})
        )
        return BoxPlotView(data=table.get_data())

#        multi_view: MultiViews = MultiViews(2)
#        multi_view.add_view(view, {}, 2, 1)
#        multi_view.add_view(text_view, {}, 2, 1)
#        multi_view.add_empty_block(2, 2)

#        dict = multi_view.to_dict(ConfigParams())


    @view(view_type=TableView, 
            human_name='ReverseQualityTable', 
            short_description='Table view reverse reads quality'
    )
    def view_as_table_reverse(self, params: ConfigParams) -> TableView:
        table: Table = Table.import_from_path(
            file=File(path=self.reverse_reads_file_path),
            params = ConfigParams({})
        )
        return TableView(data=table.get_data())

    @view(view_type=BoxPlotView)
    def view_as_boxplot_reverse(self) -> BoxPlotView:
        table: Table = Table.import_from_path(
            file=File(path=self.reverse_reads_file_path),
            params = ConfigParams({})
        )
        return BoxPlotView(data=table.get_data())



## STEP 2 : Qiime2SampleFrequencies -> Result Folder

@resource_decorator("Qiime2SampleFrequenciesFolder",
                    human_name="Qiime2SampleFrequenciesFolder",
                    short_description="Qiime2SampleFrequenciesFolder", hide=True)
class Qiime2SampleFrequenciesFolder(Folder):
    ''' Qiime2SampleFrequenciesFolder Folder file class '''

    sample_frequency_file_path: str = StrRField() # ''

    @view(view_type=TableView, 
            human_name='SampleFrequencyTable', 
            short_description='Table view of sample frequencies (median value needed for qiime 2 pipeline next step)'
    )
    def view_as_table(self, params: ConfigParams) -> TableView:
        table: Table = Table.import_from_path(
            file=File(path=self.sample_frequency_file_path),
            params = ConfigParams({})
        )
        return TableView(data=table.get_data())


## STEP 3 : Qiime2Rarefaction -> ResultFolder

@resource_decorator("Qiime2RarefactionFolder",
                    human_name="Qiime2RarefactionFolder",
                    short_description="Qiime2RarefactionFolder", hide=True)
class Qiime2RarefactionFolder(Folder):
    ''' Qiime2RarefactionFolder Folder file class '''

    shannon_index_table_path: str = StrRField()
    observed_features_table_path: str = StrRField()

    @view(view_type=TableView, 
            human_name='ShannonRarefactionTable', 
            short_description='Table view of the rarefaction table (shannon index)'
    )
    def view_as_table_shannon(self, params: ConfigParams) -> TableView:
        table: Table = Table.import_from_path(
            file=File(path=self.shannon_index_table_path),
            params = ConfigParams({})
        )
        return TableView(data=table.get_data())

    @view(view_type=TableView, 
            human_name='ObservedFeaturesRarefactionTable', 
            short_description='Table view of the rarefaction table (observed features index)'
    )
    def view_as_table_observed_features(self, params: ConfigParams) -> TableView:
        table: Table = Table.import_from_path(
            file=File(path=self.observed_features_table_path),
            params = ConfigParams({})
        )
        return TableView(data=table.get_data())        

    @view(view_type=BoxPlotView,
          human_name='ShannonRarefactionBoxplot', 
          short_description='Boxplot view of the shannon rarefaction table (X-axis: depth per samples, Y-axis: shannon index value)',   
    )
    def view_shannon_table_as_boxplot(self) -> BoxPlotView:
        table: Table = Table.import_from_path(
            file=File(path=self.shannon_index_table_path),
            params = ConfigParams({
                "delimiter": "\t", 
                "header": 1
            })
        )
        return BoxPlotView(data=table.get_data())

    @view(view_type=BoxPlotView,
            human_name='ObservedFeaturesRarefactionBoxplot', 
            short_description='Boxplot view of the observed values rarefaction table (X-axis: depth per samples, Y-axis: observed values)' ,  
    )
    def view_observed_features_table_as_boxplot(self) -> BoxPlotView:
        table: Table = Table.import_from_path(
            file=File(path=self.observed_features_table_path),
            params = ConfigParams({
                "delimiter": "\t", 
                "header": 1
            })
        )
        return BoxPlotView(data=table.get_data())



## STEP 4 : Qiime2TaxonomyDiversity -> Result Folder

@resource_decorator("Qiime2TaxonomyDiversityFolder",
                    human_name="Qiime2TaxonomyDiversityFolder",
                    short_description="Qiime2TaxonomyDiversityFolder", hide=True)
class Qiime2TaxonomyDiversityFolder(Folder):
    ''' Qiime2TaxonomyDiversityFolder Folder file class '''

    @view(view_type=TableView, 
            human_name='XXXIndexTable', 
            short_description='Table view of the XXX index table'
    )
    def view_as_table_observed_features(self, params: ConfigParams) -> TableView:
        table: Table = Table.import_from_path(
            file=File(path=self.observed_features_table_path),
            params = ConfigParams({})
        )

        return TableView(data=table.get_data())  



#######################


#    @view(view_type=TableView, 
#            human_name='Table', 
#            short_description='View as table', 
 #           specs={
 #               "file_type": StrParam(allowed_values=["fasta","quality"])
 #           }
#    )
#    def view_as_table(self, params: ConfigParams) -> TableView:
#        file_type = params["file_type"]
#        if file_type == "fasta":
#        table_file_rvs = TableFile(os.path.join(path=self.reverse_reads_file))
#        else:
#            pass
#        table: Table = table_file.read()
#        return TableView(data=table.get_data())

#    @view(view_type=BoxPlotView)
#    def view_as_table(self) -> BoxPlotView:
#        table_file = TableFile(path=self.path)
#        table: Table = table_file.read()
#        return BoxPlotView(data=table.get_data())

