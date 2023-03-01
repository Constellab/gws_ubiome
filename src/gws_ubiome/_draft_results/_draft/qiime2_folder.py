# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws_core import (BarPlotView, BoxPlotView, ConfigParams, File, Folder,
                      IntParam, LinePlot2DView, MultiViews, StackedBarPlotView,
                      StrParam, StrRField, Table, TableImporter,
                      resource_decorator, view)


# Qiime 2 : output formats

# STEP 1 : Qiime2QualityCheck -> Result Folder


# @resource_decorator("Qiime2QualityCheckResultFolder",
#                     human_name="Qiime2QualityCheckResultFolder",
#                     short_description="Qiime2QualityCheckResultFolder", hide=True)
# class Qiime2QualityCheckResultFolder(Folder):
#     """
#     Qiime2QualityCheckResultFolder Folder file class
#     """

#     # forward_reads_file_path: str = StrRField()
#     # reverse_reads_file_path: str = StrRField()

#     @view(view_type=TableView, human_name='Sequencing quality table',
#           short_description='Table of the reads sequencing quality (PHRED score per base)',
#           specs={"type": StrParam(allowed_values=["forward_reads", "reverse_reads"])})
#     def view_as_table(self, params: ConfigParams) -> TableView:
#         from ..metabarcoding.qiime2_quality_check import Qiime2QualityCheck
#         type_ = params["type"]
#         table: Table
#         if type_ == "forward_reads":
#             file_path = self.get_sub_path("forward_boxplot.csv")
#             table = ImporterHelper.import_table(file_path, {'delimiter': 'tab', "index_column": 0})
#         elif type_ == "reverse_reads":
#             file_path = self.get_sub_path("reverse_boxplot.csv")
#             table = ImporterHelper.import_table(file_path, {'delimiter': 'tab', "index_column": 0})

#         return TableView(table=table)

#     @view(view_type=BoxPlotView, human_name='Sequencing quality boxplot',
#           short_description='Boxplot of the reads sequencing quality',
#           specs={"type": StrParam(
#               allowed_values=["forward_reads", "reverse_reads"],
#               default_value="forward_reads")},
#           default_view=True)
#     def view_as_boxplot(self, params: ConfigParams) -> BoxPlotView:
#         type_ = params["type"]
#         table: Table
#         if type_ == "forward_reads":
#             file_path = self.get_sub_path("forward_boxplot.csv")
#             table = ImporterHelper.import_table(file_path, {'delimiter': 'tab', "index_column": 0})
#         elif type_ == "reverse_reads":
#             file_path = self.get_sub_path("reverse_boxplot.csv")
#             table = ImporterHelper.import_table(file_path, {'delimiter': 'tab', "index_column": 0})

#         bx_view = BoxPlotView()
#         data = table.get_data()
#         bx_view.add_series(
#             x=data.columns.values.tolist(),
#             median=data.iloc[2, :].values.tolist(),  # quality median
#             q1=data.iloc[1, :].values.tolist(),
#             q3=data.iloc[3, :].values.tolist(),
#             min=data.iloc[0, :].values.tolist(),
#             max=data.iloc[4, :].values.tolist(),
#             lower_whisker=data.iloc[0, :].values.tolist(),
#             upper_whisker=data.iloc[4, :].values.tolist()
#         )
#         bx_view.x_label = "Base position"
#         bx_view.y_label = "PHRED score"
#         return bx_view

#     # vue moyenne mobile avec median du boxplot (taille fenetre et le pas)

#     @view(view_type=LinePlot2DView, human_name='Quality line plot',
#           short_description='Boxplot of the reads sequencing quality',
#           specs={"type": StrParam(
#               allowed_values=["forward_reads", "reverse_reads"],
#               default_value="forward_reads"),
#               "window_size": IntParam(default_value=15)}, default_view=False)
#     def view_as_lineplot(self, params: ConfigParams) -> LinePlot2DView:
#         type_ = params["type"]
#         table: Table
#         if type_ == "forward_reads":
#             file_path = self.get_sub_path("forward_boxplot.csv")
#             table = ImporterHelper.import_table(file_path, {'delimiter': 'tab', "index_column": 0})
#         elif type_ == "reverse_reads":
#             file_path = self.get_sub_path("reverse_boxplot.csv")
#             table = ImporterHelper.import_table(file_path, {'delimiter': 'tab', "index_column": 0})

#         lp_view = LinePlot2DView()
#         data = table.get_data()

#         # sliding windows df.rolling(window=5).mean()
# #        y=data.iloc[2, :].values.tolist()
#         y = data.iloc[2, :]
#         q1 = data.iloc[1, :]
#         q3 = data.iloc[3, :]

#         mean_median = y.rolling(window=params["window_size"], min_periods=1).mean()
#         mean_q1 = q1.rolling(window=params["window_size"], min_periods=1).mean()
#         mean_q3 = q3.rolling(window=params["window_size"], min_periods=1).mean()
#         lp_view.add_series(
#             x=data.columns.values.tolist(),
#             y=mean_median.values.tolist()  # quality median
#         )

#         lp_view.add_series(
#             x=data.columns.values.tolist(),
#             y=mean_q1.values.tolist()  # quality median
#         )

#         lp_view.add_series(
#             x=data.columns.values.tolist(),
#             y=mean_q3.values.tolist()  # quality median
#         )
#         lp_view.x_label = "Base position"
#         lp_view.y_label = "PHRED score"
#         return lp_view


####### STEP 2 : Qiime2SampleFrequencies -> Result Folder #######

# @resource_decorator("Qiime2SampleFrequenciesFolder",
#                     human_name="Qiime2SampleFrequenciesFolder",
#                     short_description="Qiime2SampleFrequenciesFolder", hide=True)
# class Qiime2SampleFrequenciesFolder(Folder):
#     ''' Qiime2SampleFrequenciesFolder Folder file class '''

#     sample_frequency_file_path: str = StrRField()  # ''

#     @view(view_type=TableView,
#           human_name='Frequency table',
#           short_description='Table of sample frequencies',
#           default_view=True
#           )
# #    def view_as_table(self, params: ConfigParams) -> TableView:
# #        table: Table = ImporterHelper.import_table(self.sample_frequency_file_path)
# #        return TableView(table=table.get_data())
#     def view_as_table(self, params: ConfigParams) -> TableView:
#         table: Table
#         file_path = self.get_sub_path("sample-frequency-detail.tsv")
#         table = ImporterHelper.import_table(file_path, {'delimiter': 'tab', "index_column": 0})
#         view = TableView(table=table)
#         view.set_title("Sample frequency values")
#         data = table.get_data()
#         median = data.median(axis=0).iat[0]
#         average = data.mean(axis=0).iat[0]
#         view.set_caption(
#             f"For the following step, using close to median value is advised (ref).\nMedian: {median}, average: {average} ")
#         return TableView(table=table)

#     @view(view_type=BoxPlotView, human_name='Frequency boxplot',
#           short_description='Boxplot view of of sample frequencies')
#     def view_as_boxplot(self, params: ConfigParams) -> BoxPlotView:
#         table: Table
#         file_path = self.get_sub_path("sample-frequency-detail.tsv")
#         table = ImporterHelper.import_table(file_path, {'delimiter': 'tab', "index_column": 0})
#         view = TableView(table=table)
#         view.set_title("Sample frequency values")

#         bx_view = BoxPlotView()
#         data = table.get_data()
#         bx_view.add_data(data=data)
#         return bx_view

#######  STEP 3 : Qiime2Rarefaction -> ResultFolder #######


# @resource_decorator("Qiime2RarefactionFolder",
#                     human_name="Qiime2RarefactionFolder",
#                     short_description="Qiime2RarefactionFolder")
# class Qiime2RarefactionFolder(Folder):
#     ''' Qiime2RarefactionFolder Folder file class '''

#     shannon_index_table_path: str = StrRField()
#     observed_features_table_path: str = StrRField()

#     @view(view_type=TableView, human_name='Rarefaction table',
#           short_description='Rarefaction table',
#           specs={"type": StrParam(allowed_values=["rarefaction_shannon", "rarefaction_observed"])})
#     def view_as_table(self, params: ConfigParams) -> TableView:
#         type_ = params["type"]
#         table: Table = self._load_table(type_=type_)
#         view = TableView(table=table)
#         # if type_ == "rarefaction_shannon":
#         #     view.set_title("Rarefaction shannon table")
#         #     data = table.get_data()
#         #     median = data.median(axis=0).iat[0]
#         #     view.set_caption(f"blalblalb {median} blalblalblalblalb")

#         # elif type_ == "rarefaction_observed":
#         #     view.set_title("Rarefaction observed table")
#         #     data = table.get_data()
#         #     median = data.median(axis=1).iat[0]
#         #     view.set_caption(f"blalblalb {median} blalblalblalblalb")

#         return view

#     def _load_table(self, type_: str) -> Table:
#         if type_ == "rarefaction_observed":
#             file_path = self.get_sub_path("observed_features.for_boxplot.tsv")
#             table = ImporterHelper.import_table(file_path, {'delimiter': 'tab', "index_column": 0, "header": 0})
#         elif type_ == "rarefaction_shannon":
#             file_path = self.get_sub_path("shannon.for_boxplot.tsv")
#             table = ImporterHelper.import_table(file_path, {'delimiter': 'tab', "index_column": 0, "header": 0})

#         colnames = table.column_names
#         column_tags = []
#         column_names = []
#         for name in colnames:
#             name = name.replace("'", '"')
#             tag: dict = json.loads(name)
#             if "x-axis" in tag:
#                 tag["depth"] = tag["x-axis"]
#                 del tag["x-axis"]
#             column_tags.append(tag)
#             column_names.append(str(tag["depth"]) + "#" + tag["sample-id"])

#         data = table.get_data()
#         data.columns = column_names

#         table = Table(data=data)
#         table.set_column_tags(column_tags)

#         return table

#     @view(view_type=BoxPlotView, human_name='Rarefaction boxplot',
#           short_description='Boxplot of the rarefaction table',
#           specs={"type": StrParam(allowed_values=["rarefaction_shannon", "rarefaction_observed"])})
#     def view_as_boxplot(self, params: ConfigParams) -> BoxPlotView:
#         type_ = params["type"]
#         table: Table = self._load_table(type_=type_)

#         bx_view = BoxPlotView()
#         data = table.get_data()
#         bx_view.add_data(data=data)
#         bx_view.x_label = "depth"
#         bx_view.y_label = "shannon index" if type_ == "rarefaction_shannon" else "observed features value"
#         return bx_view

#     @view(view_type=LinePlot2DView, human_name='Rarefaction lineplot',
#           short_description='Lineplot of the rarefaction table',
#           specs={"type": StrParam(allowed_values=["rarefaction_shannon", "rarefaction_observed"])})
#     def view_as_lineplot(self, params: ConfigParams) -> LinePlot2DView:
#         type_ = params["type"]
#         table: Table = self._load_table(type_=type_)
#         table = table.select_numeric_columns(drop_na='all')

#         lp_view = LinePlot2DView()
#         #data = table.get_data()
#         column_tags = table.get_column_tags()
#         all_sample_ids = list(set([tag["sample-id"] for tag in column_tags]))

#         for sample_id in all_sample_ids:
#             sample_table = table.select_by_column_tags([{"sample-id": sample_id}])
#             sample_column_tags = sample_table.get_column_tags()
#             positions = [float(tag["depth"]) for tag in sample_column_tags]

#             sample_data = sample_table.get_data()
#             quantile = numpy.nanquantile(sample_data.to_numpy(), q=[0.25, 0.5, 0.75], axis=0)
#             median = quantile[1, :].tolist()
#             lp_view.add_series(x=positions, y=median, tags=sample_column_tags)

#         lp_view.x_label = "depth"
#         lp_view.y_label = "shannon index" if type_ == "rarefaction_shannon" else "observed features value"
#         return lp_view

####### STEP 4 : Qiime2TaxonomyDiversity -> Result Folder #######


# @resource_decorator("Qiime2TaxonomyDiversityFolder",
#                     human_name="Qiime2 taxonomy diversity folder",
#                     short_description="Qiime2 taxonomy diversity folder", hide=True)
# class Qiime2TaxonomyDiversityFolder(Folder):
#     ''' Qiime2TaxonomyDiversityFolder Folder file class '''

#     bray_curtis_table_path: str = StrRField()
#     chao_1_table_path: str = StrRField()
#     evenness_table_path: str = StrRField()
#     faith_pd_table_path: str = StrRField()
#     inv_simpson_table_path: str = StrRField()
#     jaccard_distance_table_path: str = StrRField()
#     jaccard_unweighted_unifrac_distance_table_path: str = StrRField()
#     taxo_level_1_table_path: str = StrRField()
#     taxo_level_2_table_path: str = StrRField()
#     taxo_level_3_table_path: str = StrRField()
#     taxo_level_4_table_path: str = StrRField()
#     taxo_level_5_table_path: str = StrRField()
#     taxo_level_6_table_path: str = StrRField()
#     taxo_level_7_table_path: str = StrRField()
#     observed_features_vector_table_path: str = StrRField()
#     shannon_vector_table_path: str = StrRField()
#     simpson_table_path: str = StrRField()
#     unweighted_unifrac_distance_table_path: str = StrRField()
#     weighted_unifrac_distance_table_path: str = StrRField()

#     @view(view_type=TableView,
#           human_name='Alpha diversity tables',
#           short_description='Tables of the alpha diversity indexes',
#           specs={
#               "type": StrParam(allowed_values=["shannon", "chao_1", "evenness", "faith_pd", "observed_community_richness"])
#           })
#     def view_as_alpha_table(self, params: ConfigParams) -> TableView:
#         type_ = params["type"]
#         table: Table
#         if type_ == "shannon":  # shannon_vector.qza.diversity_metrics.shannon_vector.qza.diversity_metrics.tsv
#             file_path = self.get_sub_path(
#                 "table_files/shannon_vector.qza.diversity_metrics.alpha-diversity.tsv")
#             table = ImporterHelper.import_table(file_path, {'delimiter': 'tab'})
# #            table = ImporterHelper.import_table(file_path, {'delimiter': 'tab', "index_column": 0})
# #            table = ImporterHelper.import_table(self.shannon_vector_table_path)
#         elif type_ == "chao_1":
#             file_path = self.get_sub_path("table_files/chao1.qza.diversity_metrics.alpha-diversity.tsv")
#             table = ImporterHelper.import_table(file_path, {'delimiter': 'tab'})
# #            table = ImporterHelper.import_table(file_path, {'delimiter': 'tab', "index_column": 0})
# #            table = ImporterHelper.import_table(self.chao_1_table_path)
#         elif type_ == "evenness":
#             file_path = self.get_sub_path(
#                 "table_files/evenness_vector.qza.diversity_metrics.alpha-diversity.tsv")
#             table = ImporterHelper.import_table(file_path, {'delimiter': 'tab'})
# #            table = ImporterHelper.import_table(file_path, {'delimiter': 'tab', "index_column": 0})
#             #            table = ImporterHelper.import_table(self.evenness_table_path)
#         elif type_ == "faith_pd":
#             file_path = self.get_sub_path(
#                 "table_files/faith_pd_vector.qza.diversity_metrics.alpha-diversity.tsv")
#             table = ImporterHelper.import_table(file_path, {'delimiter': 'tab'})
# #            table = ImporterHelper.import_table(file_path, {'delimiter': 'tab', "index_column": 0})
#             #            table = ImporterHelper.import_table(self.faith_pd_table_path)
#         elif type_ == "observed_community_richness":
#             file_path = self.get_sub_path(
#                 "table_files/observed_features_vector.qza.diversity_metrics.alpha-diversity.tsv")
#             table = ImporterHelper.import_table(file_path, {'delimiter': 'tab'})
# #            table = ImporterHelper.import_table(file_path, {'delimiter': 'tab', "index_column": 0})
#             #            table = ImporterHelper.import_table(self.observed_features_vector_table_path)

#         return TableView(table=table)

# #        return TableView(table=table.get_data())

#     @view(view_type=TableView, human_name='Beta diversity tables',
#           short_description='Tables of the beta diversity indexes',
#           specs={
#               "type":
#               StrParam(
#                   allowed_values=["bray_curtis_index", "jaccard", "jaccard_unweighted", "weighted_unifrac",
#                                   "unweighted_unifrac", "simpson", "inverse_simpson"])})
#     def view_as_beta_table(self, params: ConfigParams) -> TableView:
#         type_ = params["type"]
#         table: Table
#         if type_ == "bray_curtis_index":
#             file_path = self.get_sub_path(
#                 "table_files/bray_curtis_distance_matrix.qza.diversity_metrics.distance-matrix.tsv")
#             table = ImporterHelper.import_table(file_path, {'delimiter': 'tab'})
# #            table = ImporterHelper.import_table(file_path, {'delimiter': 'tab', "index_column": 0})
#             #            table = ImporterHelper.import_table(self.bray_curtis_table_path)
#         elif type_ == "jaccard":

#             file_path = self.get_sub_path(
#                 "table_files/jaccard_distance_matrix.qza.diversity_metrics.distance-matrix.tsv")
#             table = ImporterHelper.import_table(file_path, {'delimiter': 'tab'})
# #            table = ImporterHelper.import_table(file_path, {'delimiter': 'tab', "index_column": 0})
#             #            table = ImporterHelper.import_table(self.jaccard_distance_table_path)
#         elif type_ == "jaccard_unweighted":

#             file_path = self.get_sub_path(
#                 "table_files/jaccard_unweighted_unifrac_distance_matrix.qza.diversity_metrics.distance-matrix.tsv")
#             table = ImporterHelper.import_table(file_path, {'delimiter': 'tab'})
# #            table = ImporterHelper.import_table(file_path, {'delimiter': 'tab', "index_column": 0})
#             #            table = ImporterHelper.import_table(self.jaccard_unweighted_unifrac_distance_table_path)
#         elif type_ == "weighted_unifrac":

#             file_path = self.get_sub_path(
#                 "table_files/weighted_unifrac_distance_matrix.qza.diversity_metrics.distance-matrix.tsv")
#             table = ImporterHelper.import_table(file_path, {'delimiter': 'tab'})
# #            table = ImporterHelper.import_table(file_path, {'delimiter': 'tab', "index_column": 0})
#             #            table = ImporterHelper.import_table(self.weighted_unifrac_distance_table_path)
#         elif type_ == "unweighted_unifrac":

#             file_path = self.get_sub_path(
#                 "table_files/unweighted_unifrac_distance_matrix.qza.diversity_metrics.distance-matrix.tsv")
#             table = ImporterHelper.import_table(file_path, {'delimiter': 'tab'})
# #            table = ImporterHelper.import_table(file_path, {'delimiter': 'tab', "index_column": 0})
#          #           table = ImporterHelper.import_table(self.unweighted_unifrac_distance_table_path)
#         elif type_ == "simpson":

#             file_path = self.get_sub_path(
#                 "table_files/simpson.qza.diversity_metrics.alpha-diversity.tsv")
#             table = ImporterHelper.import_table(file_path, {'delimiter': 'tab'})
# #            table = ImporterHelper.import_table(file_path, {'delimiter': 'tab', "index_column": 0})
#          #           table = ImporterHelper.import_table(self.simpson_table_path)
#         elif type_ == "inverse_simpson":

#             file_path = self.get_sub_path(
#                 "./table_files/invSimpson.tab.tsv")
#             table = ImporterHelper.import_table(file_path, {'delimiter': 'tab'})
# #            table = ImporterHelper.import_table(file_path, {'delimiter': 'tab', "index_column": 0})
#           #          table = ImporterHelper.import_table(self.inv_simpson_table_path)

#         return TableView(table=table)
#    #     return TableView(table=table.get_data())

#     @view(view_type=TableView, human_name='Taxonomy tables',
#           short_description='Tables of the taxonomic composition (7 levels)',
#           specs={
#               "type":
#               StrParam(
#                   allowed_values=["1_Kingdom", "2_Phylum", "3_Class", "4_Order",
#                                   "5_Family", "6_Genus", "7_Species"])})
#     def view_as_taxo_table(self, params: ConfigParams) -> TableView:
#         type_ = params["type"]
#         table: Table
#         table = self._read_table(type_)
#         return TableView(table=table)
#      #   return TableView(table=table.get_data())

#     @view(view_type=StackedBarPlotView, human_name='Taxonomy stacked barplot',
#           short_description='Stacked barplots of the taxonomic composition (7 levels)',
#           specs={
#               "type":
#               StrParam(
#                   allowed_values=["1_Kingdom", "2_Phylum", "3_Class", "4_Order",
#                                   "5_Family", "6_Genus", "7_Species"])})
#     def view_as_taxo_stacked_bar_plot(self, params: ConfigParams) -> StackedBarPlotView:
#         type_ = params["type"]
#         table: Table
#         table = self._read_table(type_)
#         data = table.get_data()
#         s_view = StackedBarPlotView()
#         s_view.normalize = True
#         for i in range(1, data.shape[1]):
#             if isinstance(data.iat[0, i], str):
#                 continue
#             y = data.iloc[:, i].values.tolist()
#             s_view.add_series(y=y, name=data.columns[i])
#         s_view.x_tick_labels = data.iloc[:, 0].values.tolist()
#         return s_view

#     def _read_table(self, type_) -> Table:
#         if type_ == "1_Kingdom":
#             file_path = self.get_sub_path(
#                 "table_files/gg.taxa-bar-plots.qzv.diversity_metrics.level-1.csv.tsv.parsed.tsv")
#             table = ImporterHelper.import_table(file_path, {'delimiter': 'tab'})
# #            table = ImporterHelper.import_table(file_path, {'delimiter': 'tab', "index_column": 0})
#             #            table = ImporterHelper.import_table(self.taxo_level_1_table_path)
#         elif type_ == "2_Phylum":

#             file_path = self.get_sub_path(
#                 "table_files/gg.taxa-bar-plots.qzv.diversity_metrics.level-2.csv.tsv.parsed.tsv")
#             table = ImporterHelper.import_table(file_path, {'delimiter': 'tab', "index_column": 0})
# #            table = ImporterHelper.import_table(file_path, {'delimiter': 'tab', "index_column": 0})
#          #           table = ImporterHelper.import_table(self.taxo_level_2_table_path)
#         elif type_ == "3_Class":

#             file_path = self.get_sub_path(
#                 "table_files/gg.taxa-bar-plots.qzv.diversity_metrics.level-3.csv.tsv.parsed.tsv")
#             table = ImporterHelper.import_table(file_path, {'delimiter': 'tab'})
# #            table = ImporterHelper.import_table(file_path, {'delimiter': 'tab', "index_column": 0})
#           #          table = ImporterHelper.import_table(self.taxo_level_3_table_path)
#         elif type_ == "4_Order":

#             file_path = self.get_sub_path(
#                 "table_files/gg.taxa-bar-plots.qzv.diversity_metrics.level-4.csv.tsv.parsed.tsv")
#             table = ImporterHelper.import_table(file_path, {'delimiter': 'tab'})
# #            table = ImporterHelper.import_table(file_path, {'delimiter': 'tab', "index_column": 0})
#            #         table = ImporterHelper.import_table(self.taxo_level_4_table_path)
#         elif type_ == "5_Family":

#             file_path = self.get_sub_path(
#                 "table_files/gg.taxa-bar-plots.qzv.diversity_metrics.level-5.csv.tsv.parsed.tsv")
#             table = ImporterHelper.import_table(file_path, {'delimiter': 'tab'})
# #            table = ImporterHelper.import_table(file_path, {'delimiter': 'tab', "index_column": 0})
#             #        table = ImporterHelper.import_table(self.taxo_level_5_table_path)
#         elif type_ == "6_Genus":

#             file_path = self.get_sub_path(
#                 "table_files/gg.taxa-bar-plots.qzv.diversity_metrics.level-6.csv.tsv.parsed.tsv")
#             table = ImporterHelper.import_table(file_path, {'delimiter': 'tab'})
# #            table = ImporterHelper.import_table(file_path, {'delimiter': 'tab', "index_column": 0})
#          #       table = ImporterHelper.import_table(self.taxo_level_6_table_path)
#         elif type_ == "7_Species":

#             file_path = self.get_sub_path(
#                 "table_files/gg.taxa-bar-plots.qzv.diversity_metrics.level-7.csv.tsv.parsed.tsv")
#             table = ImporterHelper.import_table(file_path, {'delimiter': 'tab'})
# #            table = ImporterHelper.import_table(file_path, {'delimiter': 'tab', "index_column": 0})
#           #      table = ImporterHelper.import_table(self.taxo_level_7_table_path)

#         return table

@resource_decorator("Qiime2DifferentialAnalysisFolder",
                    human_name="Qiime2DifferentialAnalysisFolder",
                    short_description="Qiime2DifferentialAnalysisFolder", hide=True)
class Qiime2DifferentialAnalysisFolder(Folder):
    ''' Qiime2DifferentialAnalysisFolder Folder file class '''

#     data_table_path: str = StrRField()  # ''
#     ancom_stat_table_path: str = StrRField()  # ''
#     volcano_plot_path: str = StrRField()  # ''

#     @view(view_type=TableView,
#           human_name='Diff analysis table 1',
#           short_description='Table of differential analysis',
#           default_view=False
#           )
#     def view_as_table_1(self, params: ConfigParams) -> TableView:
#         table: Table
#         file_path = self.get_sub_path("data.tsv")
#         table = ImporterHelper.import_table(file_path, {'delimiter': 'tab', "index_column": 0})
#         view = TableView(table=table)
#         view.set_title("Sample frequency values")
#         # data = table.get_data()
#         # median = data.median(axis=0).iat[0]
#         # average = data.mean(axis=0).iat[0]
#         # view.set_caption(
#         #     f"Allowed to XXXXX. For the following step, using close to median value is advised (ref).\nMedian: {median}, average: {average} ")
#         return view

#     @view(view_type=TableView,
#           human_name='Diff analysis table 2',
#           short_description='Table of differential analysis',
#           default_view=False
#           )
#     def view_as_table_2(self, params: ConfigParams) -> TableView:
#         table: Table
#         file_path = self.get_sub_path("ancom.tsv")
#         table = ImporterHelper.import_table(file_path, {'delimiter': 'tab', "index_column": 0})
#         view = TableView(table=table)
#         view.set_title("Sample frequency values")
#         # data = table.get_data()
#         # median = data.median(axis=0).iat[0]
#         # average = data.mean(axis=0).iat[0]
#         # view.set_caption(
#         #     f"Allowed to XXXXX. For the following step, using close to median value is advised (ref).\nMedian: {median}, average: {average} ")
#         return view

#     @view(view_type=TableView,
#           human_name='Diff analysis table 3',
#           short_description='Table of differential analysis',
#           default_view=False
#           )
#     def view_as_table_3(self, params: ConfigParams) -> TableView:
#         table: Table
#         file_path = self.get_sub_path("percent-abundances.tsv")
#         table = ImporterHelper.import_table(file_path, {'delimiter': 'tab', "index_column": 0})
#         view = TableView(table=table)
#         view.set_title("Sample frequency values")
# #        data = table.get_data()
# #        median = data.median(axis=0).iat[0]
# #        average = data.mean(axis=0).iat[0]
# #        view.set_caption(
# #            f"Allowed to XXXXX. For the following step, using close to median value is advised (ref).\nMedian: {median}, average: {average} ")
#         return view

   # @view(view_type=BoxPlotView, human_name='SampleFrequencyBoxplotView',
   #       short_description='Boxplot view of of sample frequencies')
   # def view_as_boxplot(self, params: ConfigParams) -> BoxPlotView:
   #     table: Table
   #     file_path = self.get_sub_path("sample-frequency-detail.tsv")
   #     table = ImporterHelper.import_table(file_path, {'delimiter': 'tab', "index_column": 0})
   #     view = TableView(table=table)
   #     view.set_title("Sample frequency values")

   #     bx_view = BoxPlotView()
   #     data = table.get_data()
   #     bx_view.add_data(data=data)
   #     return bx_view


####

   # @view(view_type=TableView, human_name='ForwardQualityTable', short_description='Table view forward reads quality')
   # def view_as_table_forward(self, params: ConfigParams) -> TableView:
   #     table: Table = ImporterHelper.import_table(self.forward_reads_file_path)
   #     return TableView(table=table.get_data())

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
   #     return TableView(table=table.get_data())

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
   #     return TableView(table=table.get_data())

   # @view(view_type=TableView,
   #       human_name='ObservedFeaturesRarefactionTable',
   #       short_description='Table view of the rarefaction table (observed features index)'
   #       )
   # def view_as_table_observed_features(self, params: ConfigParams) -> TableView:
   #     table: Table = ImporterHelper.import_table(self.observed_features_table_path)
   #     return TableView(table=table.get_data())

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
   #     return TableView(table=table.get_data())

   # @view(view_type=TableView,
   #       human_name='TaxoLevel2Table',
   #       short_description='Table view of the taxonomic level 2 (i.e, Phylum) table'
   #       )
   # def view_as_table_taxo_level_2(self, params: ConfigParams) -> TableView:
   #     table: Table = ImporterHelper.import_table(self.taxo_level_2_table_path)
   #     return TableView(table=table.get_data())

   # @view(view_type=TableView,
   #       human_name='TaxoLevel3Table',
   #       short_description='Table view of the taxonomic level 3 (i.e, Class) table'
   #       )
   # def view_as_table_taxo_level_3(self, params: ConfigParams) -> TableView:
   #     table: Table = ImporterHelper.import_table(self.taxo_level_3_table_path)
   #     return TableView(table=table.get_data())

   # @view(view_type=TableView,
   #       human_name='TaxoLevel4Table',
   #       short_description='Table view of the taxonomic level 4 (i.e, Order) table'
   #       )
   # def view_as_table_taxo_level_4(self, params: ConfigParams) -> TableView:
   #     table: Table = ImporterHelper.import_table(self.taxo_level_4_table_path)
   #     return TableView(table=table.get_data())

   # @view(view_type=TableView,
   #       human_name='TaxoLevel5Table',
   #       short_description='Table view of the taxonomic level 5 (i.e, Family) table'
   #       )
   # def view_as_table_taxo_level_5(self, params: ConfigParams) -> TableView:
   #     table: Table = ImporterHelper.import_table(self.taxo_level_5_table_path)
   #     return TableView(table=table.get_data())

   # @view(view_type=TableView,
   #       human_name='TaxoLevel6Table',
   #       short_description='Table view of the taxonomic level 6 (i.e, Genus) table'
   #       )
   # def view_as_table_taxo_level_6(self, params: ConfigParams) -> TableView:
   #     table: Table = ImporterHelper.import_table(self.taxo_level_6_table_path)
   #     return TableView(table=table.get_data())

   # @view(view_type=TableView,
   #       human_name='TaxoLevel7Table',
   #       short_description='Table view of the taxonomic level 7 (i.e, Species) table'
   #       )
   # def view_as_table_taxo_level_7(self, params: ConfigParams) -> TableView:
   #     table: Table = ImporterHelper.import_table(self.taxo_level_7_table_path)
   #     return TableView(table=table.get_data())

   # @view(view_type=TableView,
   #       human_name='ObservedFeaturesVectorTable',
   #       short_description='Table view of the observed features vector index table'
   #       )
   # def view_as_table_observed_features_vector(self, params: ConfigParams) -> TableView:
   #     table: Table = ImporterHelper.import_table(self.observed_features_vector_table_path)
   #     return TableView(table=table.get_data())

   # @view(view_type=TableView,
   #       human_name='ShannonIndexTable',
   #       short_description='Table view of the shannon index table'
   #       )
   # def view_as_table_shannon_vector(self, params: ConfigParams) -> TableView:
   #     table: Table = ImporterHelper.import_table(self.shannon_vector_table_path)
   #     return TableView(table=table.get_data())

   # @view(view_type=TableView,
   #       human_name='SimpsonIndexTable',
   #       short_description='Table view of the simpson index table'
   #       )
   # def view_as_table_simpson(self, params: ConfigParams) -> TableView:
   #     table: Table = ImporterHelper.import_table(self.simpson_table_path)
   #     return TableView(table=table.get_data())

   # @view(view_type=TableView,
   #       human_name='UnweightedDistanceIndexTable',
   #       short_description='Table view of the unweighted unifrac distance table'
   #       )
   # def view_as_table_unweighted_unifrac_distance(self, params: ConfigParams) -> TableView:
   #     table: Table = ImporterHelper.import_table(self.unweighted_unifrac_distance_table_path)
   #     return TableView(table=table.get_data())

   # @view(view_type=TableView,
   #       human_name='WeightedDistanceIndexTable',
   #       short_description='Table view of the Weighted unifrac distance table'
   #       )
   # def view_as_table_weighted_unifrac_distance(self, params: ConfigParams) -> TableView:
   #     table: Table = ImporterHelper.import_table(self.weighted_unifrac_distance_table_path)
   #     return TableView(table=table.get_data())

   # @view(view_type=TableView,
   #       human_name='BrayCurtisIndexTable',
   #       short_description='Table view of the Bray-Curtis index table'
   #       )
   # def view_as_table_bray_curtis(self, params: ConfigParams) -> TableView:
   #     table: Table = ImporterHelper.import_table(self.bray_curtis_table_path)
   #     return TableView(table=table.get_data())

   # @view(view_type=TableView,
   #       human_name='chao1IndexTable',
   #       short_description='Table view of the chao1 index table'
   #       )
   # def view_as_table_chao_1(self, params: ConfigParams) -> TableView:
   #     table: Table = ImporterHelper.import_table(self.chao_1_table_path)
   #     return TableView(table=table.get_data())

   # @view(view_type=TableView,
   #       human_name='EvennessIndexTable',
   #       short_description='Table view of the evenness index table'
   #       )
   # def view_as_table_evenness(self, params: ConfigParams) -> TableView:
   #     table: Table = ImporterHelper.import_table(self.evenness_table_path)
   #     return TableView(table=table.get_data())

   # @view(view_type=TableView,
   #       human_name='FaithPdIndexTable',
   #       short_description='Table view of the faith_pd index table'
   #       )
   # def view_as_table_faith_pd(self, params: ConfigParams) -> TableView:
   #     table: Table = ImporterHelper.import_table(self.faith_pd_table_path)
   #     return TableView(table=table.get_data())

   # @view(view_type=TableView,
   #       human_name='FeatureFreqDetailIndexTable',
   #       short_description='Table view of the feature frequrncies detail  table'
   #       )
   # def view_as_table_features_freq(self, params: ConfigParams) -> TableView:
   #     table: Table = ImporterHelper.import_table(self.feature_freq_detail_table_path)
   #     return TableView(table=table.get_data())

   # @view(view_type=TableView,
   #       human_name='InvSimpsonIndexTable',
   #       short_description='Table view of the inverse simpson (i.e, 1/simpson index) index table'
   #       )
   # def view_as_table_inv_simpson(self, params: ConfigParams) -> TableView:
   #     table: Table = ImporterHelper.import_table(self.inv_simpson_table_path)
   #     return TableView(table=table.get_data())

   # @view(view_type=TableView,
   #       human_name='JaccardDistanceIndexTable',
   #       short_description='Table view of the jaccard distance index table'
   #       )
   # def view_as_table_jaccard_distance(self, params: ConfigParams) -> TableView:
   #     table: Table = ImporterHelper.import_table(self.jaccard_distance_table_path)
   #     return TableView(table=table.get_data())

   # @view(view_type=TableView,
   #       human_name='JaccardUnweightedDistanceIndexTable',
   #       short_description='Table view of the jaccard distance (unweighted unifrac version) index table'
   #       )
   # def view_as_table_jaccard_unweighted_unifrac_distance(self, params: ConfigParams) -> TableView:
   #     table: Table = ImporterHelper.import_table(self.jaccard_unweighted_unifrac_distance_table_path)
   #     return TableView(table=table.get_data())
