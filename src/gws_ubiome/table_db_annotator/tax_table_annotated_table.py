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
from gws_ubiome import TaxonomyTable


@resource_decorator(unique_name="TaxonomyTableTagged", hide=True)
class TaxonomyTableTagged(TaxonomyTable):

    """
    TaxonomyTableTagged class
    """

    @view(view_type=StackedBarPlotView, human_name='Stacked Bar Plot View with col tags',
          short_description='Grouping boxplot according to a tag',
          specs={"Metadata_tag": StrParam(),
                 "Normalize": BoolParam(default_value=False),
                 "Log10": BoolParam(default_value=False)},
          default_view=False)
    def view_as_grouped_boxplots(self, params: ConfigParams) -> StackedBarPlotView:
        lp_view = StackedBarPlotView()

        table_to_unfold: Table = None
        if params.get("Normalize"):
            dataframe = self.get_data()
            normalize_dataframe = dataframe.div(dataframe.sum(axis=1), axis=0)
            table_to_unfold = self._create_sub_table(normalize_dataframe, copy.deepcopy(self._meta))
        else:
            table_to_unfold = self

        # unfolding using "metadata_tag"
        unfold_table = TableUnfolderHelper.unfold_cols_by_tags(
            table_to_unfold, keys=[params.get("Metadata_tag")],
            tag_key_column_name="row_name")

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


@importer_decorator(unique_name="TaxonomyTableTaggedImporter", human_name="Taxonomy Table importer",
                    target_type=TaxonomyTableTagged, supported_extensions=Table.ALLOWED_FILE_FORMATS, hide=True)
class TaxonomyTableTaggedImporter(TableImporter):
    pass
