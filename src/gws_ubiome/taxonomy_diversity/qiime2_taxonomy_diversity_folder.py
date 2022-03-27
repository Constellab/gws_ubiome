# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import (BarPlotView, ConfigParams, File, Folder,
                      StackedBarPlotView, StrParam, StrRField, Table,
                      TableImporter, resource_decorator, view)
from gws_core.extra import TableView


@resource_decorator("Qiime2TaxonomyDiversityFolder",
                    human_name="Qiime2 taxonomy diversity folder",
                    short_description="Folder containing all extracted Qiime2 taxonomy diversity tables", hide=True)
class Qiime2TaxonomyDiversityFolder(Folder):
    ''' Qiime2TaxonomyDiversityFolder Folder file class '''

    bray_curtis_table_path: str = StrRField()
    chao_1_table_path: str = StrRField()
    evenness_table_path: str = StrRField()
    faith_pd_table_path: str = StrRField()
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
          human_name='Alpha diversity tables',
          short_description='Tables of the alpha diversity indexes',
          specs={"type": StrParam(allowed_values=["shannon", "chao_1", "evenness", "faith_pd", "observed_community_richness"])})
    def view_as_alpha_table(self, params: ConfigParams) -> TableView:
        type_ = params["type"]
        table: Table
        if type_ == "shannon":  # shannon_vector.qza.diversity_metrics.shannon_vector.qza.diversity_metrics.tsv
            file_path = self.get_sub_path(
                "table_files/shannon_vector.qza.diversity_metrics.alpha-diversity.tsv")
        elif type_ == "chao_1":
            file_path = self.get_sub_path("table_files/chao1.qza.diversity_metrics.alpha-diversity.tsv")
        elif type_ == "evenness":
            file_path = self.get_sub_path(
                "table_files/evenness_vector.qza.diversity_metrics.alpha-diversity.tsv")
        elif type_ == "faith_pd":
            file_path = self.get_sub_path("table_files/faith_pd_vector.qza.diversity_metrics.alpha-diversity.tsv")
        elif type_ == "observed_community_richness":
            file_path = self.get_sub_path(
                "table_files/observed_features_vector.qza.diversity_metrics.alpha-diversity.tsv")

        table = TableImporter.call(File(path=file_path), {'delimiter': 'tab'})
        return TableView(table=table)

    @view(view_type=TableView, human_name='Beta diversity tables',
          short_description='Tables of the beta diversity indexes',
          specs={
              "type":
              StrParam(
                  allowed_values=["bray_curtis_index", "jaccard", "jaccard_unweighted", "weighted_unifrac",
                                  "unweighted_unifrac", "simpson", "inverse_simpson"])})
    def view_as_beta_table(self, params: ConfigParams) -> TableView:
        type_ = params["type"]
        table: Table
        if type_ == "bray_curtis_index":
            file_path = self.get_sub_path(
                "table_files/bray_curtis_distance_matrix.qza.diversity_metrics.distance-matrix.tsv")
        elif type_ == "jaccard":
            file_path = self.get_sub_path(
                "table_files/jaccard_distance_matrix.qza.diversity_metrics.distance-matrix.tsv")
        elif type_ == "jaccard_unweighted":
            file_path = self.get_sub_path(
                "table_files/jaccard_unweighted_unifrac_distance_matrix.qza.diversity_metrics.distance-matrix.tsv")
        elif type_ == "weighted_unifrac":
            file_path = self.get_sub_path(
                "table_files/weighted_unifrac_distance_matrix.qza.diversity_metrics.distance-matrix.tsv")
        elif type_ == "unweighted_unifrac":
            file_path = self.get_sub_path(
                "table_files/unweighted_unifrac_distance_matrix.qza.diversity_metrics.distance-matrix.tsv")
        elif type_ == "simpson":
            file_path = self.get_sub_path("table_files/simpson.qza.diversity_metrics.alpha-diversity.tsv")
        elif type_ == "inverse_simpson":
            file_path = self.get_sub_path("./table_files/invSimpson.tab.tsv")

        table = TableImporter.call(File(path=file_path), {'delimiter': 'tab'})
        return TableView(table=table)

    @view(view_type=TableView, human_name='Taxonomy tables',
          short_description='Tables of the taxonomic composition (7 levels)',
          specs={"type": StrParam(allowed_values=["1_Kingdom", "2_Phylum", "3_Class", "4_Order", "5_Family", "6_Genus", "7_Species"])})
    def view_as_taxo_table(self, params: ConfigParams) -> TableView:
        type_ = params["type"]
        table: Table
        table = self._read_table(type_)
        return TableView(table=table)

    @view(view_type=StackedBarPlotView, human_name='Taxonomy stacked barplot',
          short_description='Stacked barplots of the taxonomic composition (7 levels)',
          specs={"type": StrParam(allowed_values=["1_Kingdom", "2_Phylum", "3_Class", "4_Order", "5_Family", "6_Genus", "7_Species"])})
    def view_as_taxo_stacked_bar_plot(self, params: ConfigParams) -> StackedBarPlotView:
        type_ = params["type"]
        table: Table
        table = self._read_table(type_)
        data = table.get_data()
        s_view = StackedBarPlotView()
        s_view.normalize = True
        for i in range(1, data.shape[1]):
            if isinstance(data.iat[0, i], str):
                continue
            y = data.iloc[:, i].values.tolist()
            s_view.add_series(y=y, name=data.columns[i])
        s_view.x_tick_labels = data.iloc[:, 0].values.tolist()
        return s_view

    def _read_table(self, type_) -> Table:
        if type_ == "1_Kingdom":
            file_path = self.get_sub_path(
                "table_files/gg.taxa-bar-plots.qzv.diversity_metrics.level-1.csv.tsv.parsed.tsv")
        elif type_ == "2_Phylum":
            file_path = self.get_sub_path(
                "table_files/gg.taxa-bar-plots.qzv.diversity_metrics.level-2.csv.tsv.parsed.tsv")
        elif type_ == "3_Class":
            file_path = self.get_sub_path(
                "table_files/gg.taxa-bar-plots.qzv.diversity_metrics.level-3.csv.tsv.parsed.tsv")
        elif type_ == "4_Order":
            file_path = self.get_sub_path(
                "table_files/gg.taxa-bar-plots.qzv.diversity_metrics.level-4.csv.tsv.parsed.tsv")
        elif type_ == "5_Family":
            file_path = self.get_sub_path(
                "table_files/gg.taxa-bar-plots.qzv.diversity_metrics.level-5.csv.tsv.parsed.tsv")
        elif type_ == "6_Genus":
            file_path = self.get_sub_path(
                "table_files/gg.taxa-bar-plots.qzv.diversity_metrics.level-6.csv.tsv.parsed.tsv")
        elif type_ == "7_Species":
            file_path = self.get_sub_path(
                "table_files/gg.taxa-bar-plots.qzv.diversity_metrics.level-7.csv.tsv.parsed.tsv")

        table = TableImporter.call(File(path=file_path), {'delimiter': 'tab'})
        return table
