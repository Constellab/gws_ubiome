import copy

import numpy as np
from gws_core import (BoolParam, BoxPlotView, ConfigParams, ConfigSpecs,
                      StackedBarPlotView, StrParam, Table, TableUnfolderHelper,
                      TypingDeprecated, resource_decorator, view)


@resource_decorator(unique_name="TaxonomyTable", hide=True,
                    deprecated=TypingDeprecated(deprecated_since="0.7.0", deprecated_message="Use Table instead"))
class TaxonomyTable(Table):
    """
    TaxonomyTable class
    """

    @view(view_type=StackedBarPlotView, human_name='Taxonomy stacked barplot',
          short_description='Stacked barplots of the taxonomic composition',
          default_view=False)
    def view_as_taxo_stacked_bar_plot(self, params: ConfigParams) -> StackedBarPlotView:

        s_view = StackedBarPlotView()
        data = self.get_data()

        s_view.normalize = True
        for i in range(0, data.shape[1]):
            if isinstance(data.iat[0, i], str):
                continue
            y = data.iloc[:, i].values.tolist()
            s_view.add_series(y=y, name=data.columns[i])
        s_view.x_tick_labels = data.index.to_list()
        s_view.y_label = "Absolute Values (raw count)"
        s_view.x_label = "Samples"

        return s_view

    @view(view_type=StackedBarPlotView, human_name='Taxonomy stacked barplot normalised (TSS)',
          short_description='Normalised stacked barplots of the taxonomic composition',
          default_view=True)
    def view_as_noramlised_taxo_stacked_bar_plot(self, params: ConfigParams) -> StackedBarPlotView:

        s_view = StackedBarPlotView(normalize=True)
        data = self.get_data()

        for i in range(0, data.shape[1]):
            if isinstance(data.iat[0, i], str):
                continue
            y = data.iloc[:, i].values.tolist()
            s_view.add_series(y=y, name=data.columns[i])
        s_view.x_tick_labels = data.index.to_list()
        s_view.y_label = "Values (%)"
        s_view.x_label = "Samples"
        return s_view

    @view(view_type=BoxPlotView, human_name='Boxplot view for row tags',
          short_description='Grouping boxplot according to a row tag',
          specs=ConfigSpecs({"Metadata_tag": StrParam(),
                             "Normalize": BoolParam(default_value=False),
                             "Log10": BoolParam(default_value=False)}),
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
        lp_view.y_label = "Count values"
        lp_view.x_label = "Samples"
        return lp_view
