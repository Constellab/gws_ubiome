# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import (BoxPlotView, ConfigParams, File, IntParam,
                      LinePlot2DView, Table, TableExporter, TableImporter,
                      exporter_decorator, importer_decorator,
                      resource_decorator, view)


@resource_decorator(unique_name="FeatureFrequencyTable", hide=True)
class FeatureFrequencyTable(Table):

    """
    FeatureFrequencyTable class
    """

    @view(view_type=BoxPlotView, human_name='Feature Frequency metric boxplots',
          short_description='Clustering metric boxplots for percentage of input : merged, passed filter and non-chimeric',
          specs={},
          default_view=True)
    def view_as_boxplot(self, params: ConfigParams) -> BoxPlotView:
        bx_view = BoxPlotView()
        #data = self.get_data()
        my_column = self.get_column_data('1 - percentage of input merged')
        bx_view.add_data(my_column, name="merged")
        my_column = self.get_column_data('2 - percentage of input passed filter')
        bx_view.add_data(my_column, name="passed filter")
        my_column = self.get_column_data('3 - percentage of input non-chimeric')
        bx_view.add_data(my_column, name="non-chimeric")

        bx_view.y_label = "Values (%)"
        bx_view.x_label = "Metrics"

        return bx_view


@importer_decorator(unique_name="FeatureFrequencyTableImporter", human_name="Feature Frequency Table importer",
                    target_type=FeatureFrequencyTable, supported_extensions=Table.ALLOWED_FILE_FORMATS, hide=True)
class FeatureFrequencyTableImporter(TableImporter):
    pass
