# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os

from gws_core import (BarPlotView, BoxPlotView, ConfigParams, File, Folder,
                      IntParam, LinePlot2DView, MultiViews, StackedBarPlotView,
                      StrParam, StrRField, Table, TableImporter,
                      resource_decorator, view)
from gws_core.extra import TableBoxPlotView, TableView


class QualityCheckTable(Table):

    """
    QualityCheckTable class
    """

    @view(view_type=BoxPlotView, human_name='Sequencing quality boxplot',
          short_description='Boxplot of the reads sequencing quality',
          specs={"type": StrParam(
              allowed_values=["forward_reads", "reverse_reads"],
              default_value="forward_reads")},
          default_view=True)
    def view_as_boxplot(self, params: ConfigParams) -> BoxPlotView:
        type_ = params["type"]
        table: Table
        if type_ == "forward_reads":
            file_path = self.get_sub_path("forward_boxplot.csv")
        elif type_ == "reverse_reads":
            file_path = self.get_sub_path("reverse_boxplot.csv")

        table = TableImporter.call(File(path=file_path), {'delimiter': 'tab', "index_column": 0})
        bx_view = BoxPlotView()
        data = table.get_data()
        bx_view.add_series(
            x=data.columns.values.tolist(),
            median=data.iloc[2, :].values.tolist(),  # quality median
            q1=data.iloc[1, :].values.tolist(),
            q3=data.iloc[3, :].values.tolist(),
            min=data.iloc[0, :].values.tolist(),
            max=data.iloc[4, :].values.tolist(),
            lower_whisker=data.iloc[0, :].values.tolist(),
            upper_whisker=data.iloc[4, :].values.tolist()
        )
        bx_view.x_label = "Base position"
        bx_view.y_label = "PHRED score"
        return bx_view

    @view(view_type=LinePlot2DView, human_name='Quality line plot',
          short_description='Line plots of the reads sequencing quality',
          specs={"type": StrParam(allowed_values=["forward_reads", "reverse_reads"], default_value="forward_reads"),
                 "window_size": IntParam(default_value=15)},
          default_view=False
          )
    def view_as_lineplot(self, params: ConfigParams) -> LinePlot2DView:
        type_ = params["type"]
        table: Table
        if type_ == "forward_reads":
            file_path = self.get_sub_path("forward_boxplot.csv")
        elif type_ == "reverse_reads":
            file_path = self.get_sub_path("reverse_boxplot.csv")

        table = TableImporter.call(File(path=file_path), {'delimiter': 'tab', "index_column": 0})
        lp_view = LinePlot2DView()
        data = table.get_data()

        # sliding windows
        y = data.iloc[2, :]
        q1 = data.iloc[1, :]
        q3 = data.iloc[3, :]

        mean_median = y.rolling(window=params["window_size"], min_periods=1).mean()
        mean_q1 = q1.rolling(window=params["window_size"], min_periods=1).mean()
        mean_q3 = q3.rolling(window=params["window_size"], min_periods=1).mean()
        lp_view.add_series(
            x=data.columns.values.tolist(),
            y=mean_median.values.tolist()  # quality median
        )

        lp_view.add_series(
            x=data.columns.values.tolist(),
            y=mean_q1.values.tolist()  # quality median
        )

        lp_view.add_series(
            x=data.columns.values.tolist(),
            y=mean_q3.values.tolist()  # quality median
        )
        lp_view.x_label = "Base position"
        lp_view.y_label = "PHRED score"
        return lp_view
