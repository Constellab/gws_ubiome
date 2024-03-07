# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import (BoxPlotView, ConfigParams, Table, TableImporter,
                      importer_decorator, resource_decorator, view , PlotlyResource)

import plotly.graph_objects as go

@resource_decorator(unique_name="FeatureFrequencyTable", hide=True)
class FeatureFrequencyTable(Table):
    """
    FeatureFrequencyTable class
    """

    @view(view_type=PlotlyResource, human_name='Feature Frequency metric boxplots',
          short_description='Clustering metric boxplots for percentage of input : merged, passed filter and non-chimeric',
          specs={},
          default_view=True)
    def view_as_boxplot(self, feature_table , path) -> PlotlyResource:
        fig = go.Figure()

        my_column_passed_filter = self.get_column_data('percentage of input passed filter')
        my_column_merged = self.get_column_data('percentage of input merged')
        my_column_non_chimeric = self.get_column_data('percentage of input non-chimeric')

        fig.add_trace(go.Box(y=my_column_passed_filter, name="1 - passed filter"))
        fig.add_trace(go.Box(y=my_column_merged, name="2 - merged"))
        fig.add_trace(go.Box(y=my_column_non_chimeric, name="3 - non-chimeric"))

        fig.update_layout(
            title='Denoising Metrics Boxplots',
            xaxis_title='Metrics',
            yaxis_title='Values (%)'
        )

        plotly_resource = PlotlyResource(fig)
        plotly_resource.name = "Denoising Metrics Boxplots"

        return plotly_resource

@importer_decorator(unique_name="FeatureFrequencyTableImporter", human_name="Feature Frequency Table importer",
                    target_type=FeatureFrequencyTable, supported_extensions=Table.ALLOWED_FILE_FORMATS, hide=True)
class FeatureFrequencyTableImporter(TableImporter):
    pass



@resource_decorator(unique_name="FeatureFrequencyTableSe", hide=True)
class FeatureFrequencyTableSe(Table):
    """
    FeatureFrequencyTableSe class
    """

    @view(view_type=PlotlyResource, human_name='Feature Frequency metric boxplots',
          short_description='Clustering metric boxplots for percentage of input : merged, passed filter and non-chimeric',
          specs={},
          default_view=True)
    def view_as_boxplot(self, feature_table , path) -> PlotlyResource:
        fig = go.Figure()

        my_column_passed_filter = self.get_column_data('percentage of input passed filter')
        my_column_non_chimeric = self.get_column_data('percentage of input non-chimeric')

        fig.add_trace(go.Box(y=my_column_passed_filter, name="1 - passed filter"))
        fig.add_trace(go.Box(y=my_column_non_chimeric, name="2 - non-chimeric"))

        fig.update_layout(
            title='Denoising Metrics Boxplots',
            xaxis_title='Metrics',
            yaxis_title='Values (%)'
        )

        plotly_resource = PlotlyResource(fig)
        plotly_resource.name = "Denoising Metrics Boxplots"

        return plotly_resource

@importer_decorator(unique_name="FeatureFrequencyTableSeImporter", human_name="Feature Frequency Table SE importer",
                    target_type=FeatureFrequencyTableSe, supported_extensions=Table.ALLOWED_FILE_FORMATS, hide=True)
class FeatureFrequencyTableSeImporter(TableImporter):
    pass
