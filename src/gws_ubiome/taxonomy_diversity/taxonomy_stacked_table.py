# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import (BarPlotView, ConfigParams, File, IntParam,
                      StackedBarPlotView, Table, TableImporter,
                      importer_decorator, resource_decorator, view)


@resource_decorator(unique_name="TaxonomyTable", hide=True)
class TaxonomyTable(Table):

    """
    TaxonomyTable class
    """

    @view(view_type=StackedBarPlotView, human_name='Taxonomy stacked barplot',
          short_description='Stacked barplots of the taxonomic composition',
          specs={})
    def view_as_taxo_stacked_bar_plot(self, params: ConfigParams) -> StackedBarPlotView:

        s_view = StackedBarPlotView()
        data = self.get_data()

        s_view.normalize = True
        for i in range(1, data.shape[1]):
            if isinstance(data.iat[0, i], str):
                continue
            y = data.iloc[:, i].values.tolist()
            s_view.add_series(y=y, name=data.columns[i])
        s_view.x_tick_labels = data.iloc[:, 0].values.tolist()
        return s_view


@importer_decorator(unique_name="TaxonomyTableImporter", human_name="Taxonomy Table importer",
                    target_type=TaxonomyTable, supported_extensions=Table.ALLOWED_FILE_FORMATS, hide=True)
class TaxonomyTableImporter(TableImporter):
    pass
