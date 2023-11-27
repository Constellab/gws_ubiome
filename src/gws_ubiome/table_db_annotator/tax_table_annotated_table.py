# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import (ConfigParams, StackedBarPlotView, StrParam, Table,
                      TableImporter, TableTagAggregatorHelper,
                      importer_decorator, resource_decorator, view)


@resource_decorator(unique_name="TaxonomyTableTagged", hide=True)
class TaxonomyTableTagged(Table):

    """
    TaxonomyTableTagged class
    """

    @view(view_type=StackedBarPlotView, human_name='Stacked Bar Plot View with column tags',
          short_description='Grouping boxplot according to a column tag',
          specs={"Metadata_tag": StrParam()})
    def view_as_grouped_stackedbarplot(self, params: ConfigParams) -> StackedBarPlotView:

        s_view = StackedBarPlotView(normalize=True)
        annotated_table: Table = None
        annotated_table = self
        table_tagged = TableTagAggregatorHelper.aggregate_by_column_tags(
            annotated_table, keys=[params.get("Metadata_tag")], func="sum")
        initialdf = table_tagged.get_data()

        for i in range(0, initialdf.shape[1]):
            if isinstance(initialdf.iat[0, i], str):
                continue
            y = initialdf.iloc[:, i].values.tolist()
            s_view.add_series(y=y, name=initialdf.columns[i])
        s_view.x_tick_labels = initialdf.index.to_list()

        return s_view


@importer_decorator(unique_name="TaxonomyTableTaggedImporter", human_name="Taxonomy Table importer",
                    target_type=TaxonomyTableTagged, supported_extensions=Table.ALLOWED_FILE_FORMATS, hide=True)
class TaxonomyTableTaggedImporter(TableImporter):
    pass
