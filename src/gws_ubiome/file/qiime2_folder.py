# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import (BarPlotView, BoxPlotView, ConfigParams, File, Folder,
                      MultiViews, StrRField, Table, TableImporter, TableView,
                      resource_decorator, view)

from ..helper.importer_helper import ImporterHelper

# Qiime 2 : output formats

# STEP 1 : Qiime2QualityCheck -> Result Folder


@resource_decorator("Qiime2QualityCheckResultFolder",
                    human_name="Qiime2QualityCheckResultFolder",
                    short_description="Qiime2QualityCheckResultFolder", hide=True)
class Qiime2QualityCheckResultFolder(Folder):
    """
    Qiime2QualityCheckResultFolder Folder file class
    """

    forward_reads_file_path: str = StrRField()
    reverse_reads_file_path: str = StrRField()

    @view(view_type=TableView, human_name='ForwardQualityTable', short_description='Table view forward reads quality')
    def view_as_table_forward(self, params: ConfigParams) -> TableView:
        table: Table = ImporterHelper.import_table(self.forward_reads_file_path)
        return TableView(data=table.get_data())

    @view(view_type=BoxPlotView)
    def view_as_boxplot_forward(self) -> BoxPlotView:
        table: Table = ImporterHelper.import_table(self.forward_reads_file_path)
        return BoxPlotView(data=table.get_data())

    @view(view_type=TableView,
          human_name='ReverseQualityTable',
          short_description='Table view reverse reads quality'
          )
    def view_as_table_reverse(self, params: ConfigParams) -> TableView:
        table: Table = ImporterHelper.import_table(self.reverse_reads_file_path)
        return TableView(data=table.get_data())

    @view(view_type=BoxPlotView)
    def view_as_boxplot_reverse(self) -> BoxPlotView:
        table: Table = ImporterHelper.import_table(self.reverse_reads_file_path)
        return BoxPlotView(data=table.get_data())


####### STEP 2 : Qiime2SampleFrequencies -> Result Folder #######

@resource_decorator("Qiime2SampleFrequenciesFolder",
                    human_name="Qiime2SampleFrequenciesFolder",
                    short_description="Qiime2SampleFrequenciesFolder", hide=True)
class Qiime2SampleFrequenciesFolder(Folder):
    ''' Qiime2SampleFrequenciesFolder Folder file class '''

    sample_frequency_file_path: str = StrRField()  # ''

    @view(view_type=TableView,
          human_name='SampleFrequencyTable',
          short_description='Table view of sample frequencies (median value needed for qiime 2 pipeline next step)'
          )
    def view_as_table(self, params: ConfigParams) -> TableView:
        table: Table = ImporterHelper.import_table(self.sample_frequency_file_path)
        return TableView(data=table.get_data())


#######  STEP 3 : Qiime2Rarefaction -> ResultFolder #######

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
        table: Table = ImporterHelper.import_table(self.shannon_index_table_path)
        return TableView(data=table.get_data())

    @view(view_type=TableView,
          human_name='ObservedFeaturesRarefactionTable',
          short_description='Table view of the rarefaction table (observed features index)'
          )
    def view_as_table_observed_features(self, params: ConfigParams) -> TableView:
        table: Table = ImporterHelper.import_table(self.observed_features_table_path)
        return TableView(data=table.get_data())

    @view(view_type=BoxPlotView,
          human_name='ShannonRarefactionBoxplot',
          short_description='Boxplot view of the shannon rarefaction table (X-axis: depth per samples, Y-axis: shannon index value)',
          )
    def view_shannon_table_as_boxplot(self) -> BoxPlotView:
        table: Table = ImporterHelper.import_table(
            self.shannon_index_table_path,
            params=ConfigParams({
                "delimiter": "\t",
                "header": 1
            })
        )
        return BoxPlotView(data=table.get_data())

    @view(view_type=BoxPlotView,
          human_name='ObservedFeaturesRarefactionBoxplot',
          short_description='Boxplot view of the observed values rarefaction table (X-axis: depth per samples, Y-axis: observed values)',
          )
    def view_observed_features_table_as_boxplot(self) -> BoxPlotView:
        table: Table = ImporterHelper.import_table(
            self.observed_features_table_path,
            params=ConfigParams({
                "delimiter": "\t",
                "header": 1
            })
        )
        return BoxPlotView(data=table.get_data())

####### STEP 4 : Qiime2TaxonomyDiversity -> Result Folder #######


@resource_decorator("Qiime2TaxonomyDiversityFolder",
                    human_name="Qiime2TaxonomyDiversityFolder",
                    short_description="Qiime2TaxonomyDiversityFolder", hide=True)
class Qiime2TaxonomyDiversityFolder(Folder):
    ''' Qiime2TaxonomyDiversityFolder Folder file class '''

    bray_curtis_table_path: str = StrRField()
    chao_1_table_path: str = StrRField()
    evenness_table_path: str = StrRField()
    faith_pd_table_path: str = StrRField()
    feature_freq_detail_table_path: str = StrRField()
    inv_simpson_table_path: str = StrRField()
    jaccard_distance_table_path: str = StrRField()
    jaccard_unweighted_unifrac_distance_table_path: str = StrRField()
    taxo_level_1_table_path: str = StrRField()
    taxo_level_2_table_path: str = StrRField()
    taxo_level_3_table_path: str = StrRField()
    taxo_level_4_table_path: str = StrRField()
    taxo_level_5_table_path: str = StrRField()
    taxo_level_6_table_path: str = StrRField()
    taxo_level_7_table_path: str = StrRField()
    observed_features_vector_table_path: str = StrRField()
    shannon_vector_table_path: str = StrRField()
    simpson_table_path: str = StrRField()
    unweighted_unifrac_distance_table_path: str = StrRField()
    weighted_unifrac_distance_table_path: str = StrRField()

    @view(view_type=TableView,
          human_name='BrayCurtisIndexTable',
          short_description='Table view of the Bray-Curtis index table'
          )
    def view_as_table_bray_curtis(self, params: ConfigParams) -> TableView:
        table: Table = ImporterHelper.import_table(self.bray_curtis_table_path)
        return TableView(data=table.get_data())

    @view(view_type=TableView,
          human_name='chao1IndexTable',
          short_description='Table view of the chao1 index table'
          )
    def view_as_table_chao_1(self, params: ConfigParams) -> TableView:
        table: Table = ImporterHelper.import_table(self.chao_1_table_path)
        return TableView(data=table.get_data())

    @view(view_type=TableView,
          human_name='EvennessIndexTable',
          short_description='Table view of the evenness index table'
          )
    def view_as_table_evenness(self, params: ConfigParams) -> TableView:
        table: Table = ImporterHelper.import_table(self.evenness_table_path)
        return TableView(data=table.get_data())

    @view(view_type=TableView,
          human_name='FaithPdIndexTable',
          short_description='Table view of the faith_pd index table'
          )
    def view_as_table_faith_pd(self, params: ConfigParams) -> TableView:
        table: Table = ImporterHelper.import_table(self.faith_pd_table_path)
        return TableView(data=table.get_data())

    @view(view_type=TableView,
          human_name='FeatureFreqDetailIndexTable',
          short_description='Table view of the feature frequrncies detail  table'
          )
    def view_as_table_features_freq(self, params: ConfigParams) -> TableView:
        table: Table = ImporterHelper.import_table(self.feature_freq_detail_table_path)
        return TableView(data=table.get_data())

    @view(view_type=TableView,
          human_name='InvSimpsonIndexTable',
          short_description='Table view of the inverse simpson (i.e, 1/simpson index) index table'
          )
    def view_as_table_inv_simpson(self, params: ConfigParams) -> TableView:
        table: Table = ImporterHelper.import_table(self.inv_simpson_table_path)
        return TableView(data=table.get_data())

    @view(view_type=TableView,
          human_name='JaccardDistanceIndexTable',
          short_description='Table view of the jaccard distance index table'
          )
    def view_as_table_jaccard_distance(self, params: ConfigParams) -> TableView:
        table: Table = ImporterHelper.import_table(self.jaccard_distance_table_path)
        return TableView(data=table.get_data())

    @view(view_type=TableView,
          human_name='JaccardUnweightedDistanceIndexTable',
          short_description='Table view of the jaccard distance (unweighted unifrac version) index table'
          )
    def view_as_table_jaccard_unweighted_unifrac_distance(self, params: ConfigParams) -> TableView:
        table: Table = ImporterHelper.import_table(self.jaccard_unweighted_unifrac_distance_table_path)
        return TableView(data=table.get_data())

    @view(view_type=TableView,
          human_name='TaxoLevel1Table',
          short_description='Table view of the taxonomic level 1 (i.e, Kingdom) table'
          )
    def view_as_table_taxo_level_1(self, params: ConfigParams) -> TableView:
        table: Table = ImporterHelper.import_table(self.taxo_level_1_table_path)
        return TableView(data=table.get_data())

    @view(view_type=TableView,
          human_name='TaxoLevel2Table',
          short_description='Table view of the taxonomic level 2 (i.e, Phylum) table'
          )
    def view_as_table_taxo_level_2(self, params: ConfigParams) -> TableView:
        table: Table = ImporterHelper.import_table(self.taxo_level_2_table_path)
        return TableView(data=table.get_data())

    @view(view_type=TableView,
          human_name='TaxoLevel3Table',
          short_description='Table view of the taxonomic level 3 (i.e, Class) table'
          )
    def view_as_table_taxo_level_3(self, params: ConfigParams) -> TableView:
        table: Table = ImporterHelper.import_table(self.taxo_level_3_table_path)
        return TableView(data=table.get_data())

    @view(view_type=TableView,
          human_name='TaxoLevel4Table',
          short_description='Table view of the taxonomic level 4 (i.e, Order) table'
          )
    def view_as_table_taxo_level_4(self, params: ConfigParams) -> TableView:
        table: Table = ImporterHelper.import_table(self.taxo_level_4_table_path)
        return TableView(data=table.get_data())

    @view(view_type=TableView,
          human_name='TaxoLevel5Table',
          short_description='Table view of the taxonomic level 5 (i.e, Family) table'
          )
    def view_as_table_taxo_level_5(self, params: ConfigParams) -> TableView:
        table: Table = ImporterHelper.import_table(self.taxo_level_5_table_path)
        return TableView(data=table.get_data())

    @view(view_type=TableView,
          human_name='TaxoLevel6Table',
          short_description='Table view of the taxonomic level 6 (i.e, Genus) table'
          )
    def view_as_table_taxo_level_6(self, params: ConfigParams) -> TableView:
        table: Table = ImporterHelper.import_table(self.taxo_level_6_table_path)
        return TableView(data=table.get_data())

    @view(view_type=TableView,
          human_name='TaxoLevel7Table',
          short_description='Table view of the taxonomic level 7 (i.e, Species) table'
          )
    def view_as_table_taxo_level_7(self, params: ConfigParams) -> TableView:
        table: Table = ImporterHelper.import_table(self.taxo_level_7_table_path)
        return TableView(data=table.get_data())

    @view(view_type=TableView,
          human_name='ObservedFeaturesVectorTable',
          short_description='Table view of the observed features vector index table'
          )
    def view_as_table_observed_features_vector(self, params: ConfigParams) -> TableView:
        table: Table = ImporterHelper.import_table(self.observed_features_vector_table_path)
        return TableView(data=table.get_data())

    @view(view_type=TableView,
          human_name='ShannonIndexTable',
          short_description='Table view of the shannon index table'
          )
    def view_as_table_shannon_vector(self, params: ConfigParams) -> TableView:
        table: Table = ImporterHelper.import_table(self.shannon_vector_table_path)
        return TableView(data=table.get_data())

    @view(view_type=TableView,
          human_name='SimpsonIndexTable',
          short_description='Table view of the simpson index table'
          )
    def view_as_table_simpson(self, params: ConfigParams) -> TableView:
        table: Table = ImporterHelper.import_table(self.simpson_table_path)
        return TableView(data=table.get_data())

    @view(view_type=TableView,
          human_name='UnweightedDistanceIndexTable',
          short_description='Table view of the unweighted unifrac distance table'
          )
    def view_as_table_unweighted_unifrac_distance(self, params: ConfigParams) -> TableView:
        table: Table = ImporterHelper.import_table(self.unweighted_unifrac_distance_table_path)
        return TableView(data=table.get_data())

    @view(view_type=TableView,
          human_name='WeightedDistanceIndexTable',
          short_description='Table view of the Weighted unifrac distance table'
          )
    def view_as_table_weighted_unifrac_distance(self, params: ConfigParams) -> TableView:
        table: Table = ImporterHelper.import_table(self.weighted_unifrac_distance_table_path)
        return TableView(data=table.get_data())
