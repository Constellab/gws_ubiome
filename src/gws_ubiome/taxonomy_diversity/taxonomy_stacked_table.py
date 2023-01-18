# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
import copy

import numpy as np
from gws_core import (BarPlotView, BoolParam, BoxPlotView, ConfigParams, File,
                      IntParam, StackedBarPlotView, StrParam, Table,
                      TableImporter, TableUnfolderHelper, TableView, TagsParam,
                      importer_decorator, resource_decorator, view)


@resource_decorator(unique_name="TaxonomyTable", hide=True)
class TaxonomyTable(Table):

    """
    TaxonomyTable class
    """

    @view(view_type=StackedBarPlotView, human_name='Taxonomy stacked barplot',
          short_description='Stacked barplots of the taxonomic composition',
          specs={}, default_view=False)
    def view_as_taxo_stacked_bar_plot(self, params: ConfigParams) -> StackedBarPlotView:

        s_view = StackedBarPlotView()
        data = self.get_data()

        s_view.normalize = True
        for i in range(0, data.shape[1]):
            if isinstance(data.iat[0, i], str):
                continue
            y = data.iloc[:, i].values.tolist()
            s_view.add_series(y=y, name=data.columns[i])
        s_view.x_tick_labels = data.index.to_list()  # data.iloc[:, 0].values.tolist()
        return s_view

    @view(view_type=StackedBarPlotView, human_name='Taxonomy stacked barplot normalised (TSS)',
          short_description='Normalised stacked barplots of the taxonomic composition',
          specs={}, default_view=True)
    def view_as_noramlised_taxo_stacked_bar_plot(self, params: ConfigParams) -> StackedBarPlotView:

        s_view = StackedBarPlotView(normalize=True)
        data = self.get_data()

        for i in range(0, data.shape[1]):
            if isinstance(data.iat[0, i], str):
                continue
            y = data.iloc[:, i].values.tolist()
            s_view.add_series(y=y, name=data.columns[i])
        s_view.x_tick_labels = data.index.to_list()  # data.iloc[:, 0].values.tolist()

        return s_view

    # @view(view_type=StackedBarPlotView, human_name='Stackedbarplot column tags',
    #       short_description='Grouping Stacked bar plot view with column tags',
    #       specs={"Metadata_tag": StrParam()
    #              },
    #       default_view=False)
    # def view_as_grouped_stackedbarplot(self, params: ConfigParams) -> StackedBarPlotView:

    #     s_view = StackedBarPlotView(normalize=True)
    #     dataframe = self.get_data()
    #     normalize_dataframe = dataframe.div(dataframe.sum(axis=1), axis=0)
    #     table_to_unfold = self._create_sub_table(normalize_dataframe, copy.deepcopy(self._meta))

    #     # unfolding using "metadata_tag"
    #     unfold_table = TableUnfolderHelper.unfold_column_by_tags(
    #         table_to_unfold, keys=[params.get("Metadata_tag")],
    #         tag_key_row_name="row_name")

    #     # then matrix transposition
    #     all_tags = table_to_unfold.get_available_columns_tags()

    #     for i in range(0, data.shape[1]):
    #         if isinstance(data.iat[0, i], str):
    #             continue
    #         y = data.iloc[:, i].values.tolist()
    #         s_view.add_series(y=y, name=data.columns[i])
    #     s_view.x_tick_labels = data.index.to_list()  # data.iloc[:, 0].values.tolist()

    #     return s_view

    @view(view_type=BoxPlotView, human_name='Boxplot view for row tags',
          short_description='Grouping boxplot according to a row tag',
          specs={"Metadata_tag": StrParam(),
                 "Normalize": BoolParam(default_value=False),
                 "Log10": BoolParam(default_value=False)},
          default_view=False)
    def view_as_grouped_boxplots(self, params: ConfigParams) -> BoxPlotView:
        lp_view = BoxPlotView()

        table_to_unfold: Table = None
        if params.get("Normalize"):
            dataframe = self.get_data()
            normalize_dataframe = dataframe.div(dataframe.sum(axis=1), axis=0)
            table_to_unfold = self._create_sub_table(normalize_dataframe, copy.deepcopy(self._meta))
        else:
            table_to_unfold = self

        # unfolding using "metadata_tag"
        unfold_table = TableUnfolderHelper.unfold_rows_by_tags(
            table_to_unfold, keys=[params.get("Metadata_tag")],
            tag_key_column_name="column_name")

        # then matrix transposition
        all_tags = table_to_unfold.get_available_row_tags()
        # for value in tag_values:
        for value in all_tags.get(params.get("Metadata_tag"), []):
            sub_table = unfold_table.select_by_column_tags([{params.get("Metadata_tag"): value}])
            initialdf = sub_table.get_data()
            # log10 transformation of each values
            if params.get("Log10"):
                dataframe = np.log10(initialdf.replace(0, np.nan))
            else:
                dataframe = initialdf
            # one serie per tag value containing each species values
            lp_view.add_data_from_dataframe(dataframe, value, sub_table.get_column_tags())

        lp_view.x_tick_labels = self.column_names

        return lp_view


@importer_decorator(unique_name="TaxonomyTableImporter", human_name="Taxonomy Table importer",
                    target_type=TaxonomyTable, supported_extensions=Table.ALLOWED_FILE_FORMATS, hide=True)
class TaxonomyTableImporter(TableImporter):
    pass
