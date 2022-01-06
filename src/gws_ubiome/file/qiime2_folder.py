# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import (BarPlotView, BoxPlotView, ConfigParams, File, Folder,
                      MultiViews, StrParam, StrRField, Table, TableImporter,
                      TableView, resource_decorator, view)

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

    @view(view_type=TableView, human_name='SequencingQualityTableView',
          short_description='Table view of the reads sequencing quality (PHRED score per base, from first to last base)',
          specs={"type": StrParam(allowed_value=["forward_reads", "reverse_reads"])})
    def view_as_table(self, params: ConfigParams) -> TableView:
        type_ = params["type"]
        table: Table
        if type_ == "forward_reads":
            table = ImporterHelper.import_table(self.forward_reads_file_path)
        elif type_ == "reverse_reads":
            table = ImporterHelper.import_table(self.reverse_reads_file_path)

        return TableView(data=table.get_data())

    @view(view_type=BoxPlotView, human_name='SequencingQualityBoxplotView',
          short_description='Boxplot view of the reads sequencing quality (PHRED score per base, from first to last base)',
          specs={"type": StrParam(allowed_value=["forward_reads", "reverse_reads"])})
    def view_as_boxplot(self, params: ConfigParams) -> TableView:
        type_ = params["type"]
        table: Table
        if type_ == "forward_reads":
            table = ImporterHelper.import_table(self.forward_reads_file_path)
        elif type_ == "reverse_reads":
            table = ImporterHelper.import_table(self.reverse_reads_file_path)

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

    @view(view_type=TableView, human_name='RarefactionTableView',
          short_description='Table view of the rarefaction table (observed features or shannon index)',
          specs={"type": StrParam(allowed_value=["rarefaction_shannon", "rarefaction_observed"])})
    def view_as_table(self, params: ConfigParams) -> TableView:
        type_ = params["type"]
        table: Table
        if type_ == "forward_reads":
            table = ImporterHelper.import_table(self.shannon_index_table_path)
        elif type_ == "reverse_reads":
            table = ImporterHelper.import_table(self.observed_features_table_path)

        return TableView(data=table.get_data())

    @view(view_type=BoxPlotView, human_name='RarefactionBoxplotView',
          short_description='Boxplot view of the rarefaction table (X-axis: depth per samples, Y-axis: shannon index or observed features value)',
          specs={"type": StrParam(allowed_value=["rarefaction_shannon", "rarefaction_observed"])})
    def view_as_boxplot(self, params: ConfigParams) -> BoxPlotView:
        type_ = params["type"]
        table: Table
        if type_ == "rarefaction_shannon":
            table: Table = ImporterHelper.import_table(
                self.shannon_index_table_path,
                params=ConfigParams({
                    "delimiter": "\t",
                    "header": 1
                })
            )
        elif type_ == "rarefaction_observed":
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
          human_name='AlphaDiversityTableView',
          short_description='Table view of the alpha diversity indexes table',
          specs={
              "type": StrParam(allowed_value=["shannon", "chao_1", "evenness", "faith_pd", "observed_community_richness", "feature_frequencies"])
          })
    def view_as_alpha_table(self, params: ConfigParams) -> TableView:
        type_ = params["type"]
        table: Table
        if type_ == "shannon":
            table = ImporterHelper.import_table(self.shannon_vector_table_path)
        elif type_ == "chao_1":
            table = ImporterHelper.import_table(self.chao_1_table_path)
        elif type_ == "evenness":
            table = ImporterHelper.import_table(self.evenness_table_path)
        elif type_ == "faith_pd":
            table = ImporterHelper.import_table(self.faith_pd_table_path)
        elif type_ == "observed_community_richness":
            table = ImporterHelper.import_table(self.observed_features_vector_table_path)
        elif type_ == "feature_frequencies":
            table = ImporterHelper.import_table(self.feature_freq_detail_table_path)

        return TableView(data=table.get_data())

    @view(view_type=TableView, human_name='BetaDiversityTableView',
          short_description='Table view of the beta diversity indexes table',
          specs={
              "type":
              StrParam(
                  allowed_value=["bray_curtis_index", "jaccard", "jaccard_unweighted", "weighted_unifrac",
                                 "unweighted_unifrac", "simpson", "inverse_simpson"])})
    def view_as_beta_table(self, params: ConfigParams) -> TableView:
        type_ = params["type"]
        table: Table
        if type_ == "bray_curtis":
            table = ImporterHelper.import_table(self.bray_curtis_table_path)
        elif type_ == "jaccard":
            table = ImporterHelper.import_table(self.jaccard_distance_table_path)
        elif type_ == "jaccard_unweighted":
            table = ImporterHelper.import_table(self.jaccard_unweighted_unifrac_distance_table_path)
        elif type_ == "weighted_unifrac":
            table = ImporterHelper.import_table(self.weighted_unifrac_distance_table_path)
        elif type_ == "unweighted_unifrac":
            table = ImporterHelper.import_table(self.unweighted_unifrac_distance_table_path)
        elif type_ == "simpson":
            table = ImporterHelper.import_table(self.simpson_table_path)
        elif type_ == "inverse_simpson":
            table = ImporterHelper.import_table(self.inv_simpson_table_path)

        return TableView(data=table.get_data())

    @view(view_type=TableView, human_name='TaxonomicTablesView',
          short_description='Table view of the Taxonomic composition table (7 levels)',
          specs={
              "type":
              StrParam(
                  allowed_value=["1_Kingdom", "2_Phylum", "3_Class", "4_Order",
                                 "5_Family", "6_Genus", "7_Species"])})
    def view_as_taxo_table(self, params: ConfigParams) -> TableView:
        type_ = params["type"]
        table: Table
        if type_ == "1_Kingdom":
            table = ImporterHelper.import_table(self.taxo_level_1_table_path)
        elif type_ == "2_Phylum":
            table = ImporterHelper.import_table(self.taxo_level_2_table_path)
        elif type_ == "3_Class":
            table = ImporterHelper.import_table(self.taxo_level_3_table_path)
        elif type_ == "4_Order":
            table = ImporterHelper.import_table(self.taxo_level_4_table_path)
        elif type_ == "5_Family":
            table = ImporterHelper.import_table(self.taxo_level_5_table_path)
        elif type_ == "6_Genus":
            table = ImporterHelper.import_table(self.taxo_level_6_table_path)
        elif type_ == "7_Species":
            table = ImporterHelper.import_table(self.taxo_level_7_table_path)

        return TableView(data=table.get_data())


####

    # @view(view_type=TableView, human_name='ForwardQualityTable', short_description='Table view forward reads quality')
    # def view_as_table_forward(self, params: ConfigParams) -> TableView:
    #     table: Table = ImporterHelper.import_table(self.forward_reads_file_path)
    #     return TableView(data=table.get_data())

    # @view(view_type=BoxPlotView)
    # def view_as_boxplot_forward(self) -> BoxPlotView:
    #     table: Table = ImporterHelper.import_table(self.forward_reads_file_path)
    #     return BoxPlotView(data=table.get_data())

    # @view(view_type=TableView,
    #       human_name='ReverseQualityTable',
    #       short_description='Table view reverse reads quality'
    #       )
    # def view_as_table_reverse(self, params: ConfigParams) -> TableView:
    #     table: Table = ImporterHelper.import_table(self.reverse_reads_file_path)
    #     return TableView(data=table.get_data())

    # @view(view_type=BoxPlotView)
    # def view_as_boxplot_reverse(self) -> BoxPlotView:
    #     table: Table = ImporterHelper.import_table(self.reverse_reads_file_path)
    #     return BoxPlotView(data=table.get_data())

    # @view(view_type=TableView,
    #       human_name='ShannonRarefactionTable',
    #       short_description='Table view of the rarefaction table (shannon index)'
    #       )
    # def view_as_table_shannon(self, params: ConfigParams) -> TableView:
    #     table: Table = ImporterHelper.import_table(self.shannon_index_table_path)
    #     return TableView(data=table.get_data())

    # @view(view_type=TableView,
    #       human_name='ObservedFeaturesRarefactionTable',
    #       short_description='Table view of the rarefaction table (observed features index)'
    #       )
    # def view_as_table_observed_features(self, params: ConfigParams) -> TableView:
    #     table: Table = ImporterHelper.import_table(self.observed_features_table_path)
    #     return TableView(data=table.get_data())

    # @view(view_type=BoxPlotView,
    #       human_name='ShannonRarefactionBoxplot',
    #       short_description='Boxplot view of the shannon rarefaction table (X-axis: depth per samples, Y-axis: shannon index value)',
    #       )
    # def view_shannon_table_as_boxplot(self) -> BoxPlotView:
    #     table: Table = ImporterHelper.import_table(
    #         self.shannon_index_table_path,
    #         params=ConfigParams({
    #             "delimiter": "\t",
    #             "header": 1
    #         })
    #     )
    #     return BoxPlotView(data=table.get_data())

    # @view(view_type=BoxPlotView,
    #       human_name='ObservedFeaturesRarefactionBoxplot',
    #       short_description='Boxplot view of the observed values rarefaction table (X-axis: depth per samples, Y-axis: observed values)',
    #       )
    # def view_observed_features_table_as_boxplot(self) -> BoxPlotView:
    #     table: Table = ImporterHelper.import_table(
    #         self.observed_features_table_path,
    #         params=ConfigParams({
    #             "delimiter": "\t",
    #             "header": 1
    #         })
    #     )
    #     return BoxPlotView(data=table.get_data())

    # @view(view_type=TableView,
    #       human_name='TaxoLevel1Table',
    #       short_description='Table view of the taxonomic level 1 (i.e, Kingdom) table'
    #       )
    # def view_as_table_taxo_level_1(self, params: ConfigParams) -> TableView:
    #     table: Table = ImporterHelper.import_table(self.taxo_level_1_table_path)
    #     return TableView(data=table.get_data())

    # @view(view_type=TableView,
    #       human_name='TaxoLevel2Table',
    #       short_description='Table view of the taxonomic level 2 (i.e, Phylum) table'
    #       )
    # def view_as_table_taxo_level_2(self, params: ConfigParams) -> TableView:
    #     table: Table = ImporterHelper.import_table(self.taxo_level_2_table_path)
    #     return TableView(data=table.get_data())

    # @view(view_type=TableView,
    #       human_name='TaxoLevel3Table',
    #       short_description='Table view of the taxonomic level 3 (i.e, Class) table'
    #       )
    # def view_as_table_taxo_level_3(self, params: ConfigParams) -> TableView:
    #     table: Table = ImporterHelper.import_table(self.taxo_level_3_table_path)
    #     return TableView(data=table.get_data())

    # @view(view_type=TableView,
    #       human_name='TaxoLevel4Table',
    #       short_description='Table view of the taxonomic level 4 (i.e, Order) table'
    #       )
    # def view_as_table_taxo_level_4(self, params: ConfigParams) -> TableView:
    #     table: Table = ImporterHelper.import_table(self.taxo_level_4_table_path)
    #     return TableView(data=table.get_data())

    # @view(view_type=TableView,
    #       human_name='TaxoLevel5Table',
    #       short_description='Table view of the taxonomic level 5 (i.e, Family) table'
    #       )
    # def view_as_table_taxo_level_5(self, params: ConfigParams) -> TableView:
    #     table: Table = ImporterHelper.import_table(self.taxo_level_5_table_path)
    #     return TableView(data=table.get_data())

    # @view(view_type=TableView,
    #       human_name='TaxoLevel6Table',
    #       short_description='Table view of the taxonomic level 6 (i.e, Genus) table'
    #       )
    # def view_as_table_taxo_level_6(self, params: ConfigParams) -> TableView:
    #     table: Table = ImporterHelper.import_table(self.taxo_level_6_table_path)
    #     return TableView(data=table.get_data())

    # @view(view_type=TableView,
    #       human_name='TaxoLevel7Table',
    #       short_description='Table view of the taxonomic level 7 (i.e, Species) table'
    #       )
    # def view_as_table_taxo_level_7(self, params: ConfigParams) -> TableView:
    #     table: Table = ImporterHelper.import_table(self.taxo_level_7_table_path)
    #     return TableView(data=table.get_data())

    # @view(view_type=TableView,
    #       human_name='ObservedFeaturesVectorTable',
    #       short_description='Table view of the observed features vector index table'
    #       )
    # def view_as_table_observed_features_vector(self, params: ConfigParams) -> TableView:
    #     table: Table = ImporterHelper.import_table(self.observed_features_vector_table_path)
    #     return TableView(data=table.get_data())

    # @view(view_type=TableView,
    #       human_name='ShannonIndexTable',
    #       short_description='Table view of the shannon index table'
    #       )
    # def view_as_table_shannon_vector(self, params: ConfigParams) -> TableView:
    #     table: Table = ImporterHelper.import_table(self.shannon_vector_table_path)
    #     return TableView(data=table.get_data())

    # @view(view_type=TableView,
    #       human_name='SimpsonIndexTable',
    #       short_description='Table view of the simpson index table'
    #       )
    # def view_as_table_simpson(self, params: ConfigParams) -> TableView:
    #     table: Table = ImporterHelper.import_table(self.simpson_table_path)
    #     return TableView(data=table.get_data())

    # @view(view_type=TableView,
    #       human_name='UnweightedDistanceIndexTable',
    #       short_description='Table view of the unweighted unifrac distance table'
    #       )
    # def view_as_table_unweighted_unifrac_distance(self, params: ConfigParams) -> TableView:
    #     table: Table = ImporterHelper.import_table(self.unweighted_unifrac_distance_table_path)
    #     return TableView(data=table.get_data())

    # @view(view_type=TableView,
    #       human_name='WeightedDistanceIndexTable',
    #       short_description='Table view of the Weighted unifrac distance table'
    #       )
    # def view_as_table_weighted_unifrac_distance(self, params: ConfigParams) -> TableView:
    #     table: Table = ImporterHelper.import_table(self.weighted_unifrac_distance_table_path)
    #     return TableView(data=table.get_data())

    # @view(view_type=TableView,
    #       human_name='BrayCurtisIndexTable',
    #       short_description='Table view of the Bray-Curtis index table'
    #       )
    # def view_as_table_bray_curtis(self, params: ConfigParams) -> TableView:
    #     table: Table = ImporterHelper.import_table(self.bray_curtis_table_path)
    #     return TableView(data=table.get_data())

    # @view(view_type=TableView,
    #       human_name='chao1IndexTable',
    #       short_description='Table view of the chao1 index table'
    #       )
    # def view_as_table_chao_1(self, params: ConfigParams) -> TableView:
    #     table: Table = ImporterHelper.import_table(self.chao_1_table_path)
    #     return TableView(data=table.get_data())

    # @view(view_type=TableView,
    #       human_name='EvennessIndexTable',
    #       short_description='Table view of the evenness index table'
    #       )
    # def view_as_table_evenness(self, params: ConfigParams) -> TableView:
    #     table: Table = ImporterHelper.import_table(self.evenness_table_path)
    #     return TableView(data=table.get_data())

    # @view(view_type=TableView,
    #       human_name='FaithPdIndexTable',
    #       short_description='Table view of the faith_pd index table'
    #       )
    # def view_as_table_faith_pd(self, params: ConfigParams) -> TableView:
    #     table: Table = ImporterHelper.import_table(self.faith_pd_table_path)
    #     return TableView(data=table.get_data())

    # @view(view_type=TableView,
    #       human_name='FeatureFreqDetailIndexTable',
    #       short_description='Table view of the feature frequrncies detail  table'
    #       )
    # def view_as_table_features_freq(self, params: ConfigParams) -> TableView:
    #     table: Table = ImporterHelper.import_table(self.feature_freq_detail_table_path)
    #     return TableView(data=table.get_data())

    # @view(view_type=TableView,
    #       human_name='InvSimpsonIndexTable',
    #       short_description='Table view of the inverse simpson (i.e, 1/simpson index) index table'
    #       )
    # def view_as_table_inv_simpson(self, params: ConfigParams) -> TableView:
    #     table: Table = ImporterHelper.import_table(self.inv_simpson_table_path)
    #     return TableView(data=table.get_data())

    # @view(view_type=TableView,
    #       human_name='JaccardDistanceIndexTable',
    #       short_description='Table view of the jaccard distance index table'
    #       )
    # def view_as_table_jaccard_distance(self, params: ConfigParams) -> TableView:
    #     table: Table = ImporterHelper.import_table(self.jaccard_distance_table_path)
    #     return TableView(data=table.get_data())

    # @view(view_type=TableView,
    #       human_name='JaccardUnweightedDistanceIndexTable',
    #       short_description='Table view of the jaccard distance (unweighted unifrac version) index table'
    #       )
    # def view_as_table_jaccard_unweighted_unifrac_distance(self, params: ConfigParams) -> TableView:
    #     table: Table = ImporterHelper.import_table(self.jaccard_unweighted_unifrac_distance_table_path)
    #     return TableView(data=table.get_data())
