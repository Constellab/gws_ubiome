
from gws_core import (BoxPlotView, ConfigParams, ConfigSpecs, IntParam,
                      LinePlot2DView, Table, TableImporter, TypingDeprecated,
                      importer_decorator, resource_decorator, view)


@resource_decorator(unique_name="QualityCheckTable", hide=True,
                    deprecated=TypingDeprecated(deprecated_since="0.7.0", deprecated_message="Use Table instead"))
class QualityCheckTable(Table):

    """
    QualityCheckTable class
    """

    @view(view_type=BoxPlotView, human_name='Sequencing quality boxplot',
          short_description='Boxplot of the reads sequencing quality',
          default_view=True)
    def view_as_boxplot(self, params: ConfigParams) -> BoxPlotView:
        bx_view = BoxPlotView()
        data = self.get_data()
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
          specs=ConfigSpecs({"window_size": IntParam(default_value=15)}),
          default_view=False
          )
    def view_as_lineplot(self, params: ConfigParams) -> LinePlot2DView:
        lp_view = LinePlot2DView()
        data = self.get_data()

        # sliding windows
        y = data.iloc[2, :]
        q1 = data.iloc[1, :]
        q3 = data.iloc[3, :]

        mean_median = y.rolling(window=params["window_size"], min_periods=1).mean()
        mean_q1 = q1.rolling(window=params["window_size"], min_periods=1).mean()
        mean_q3 = q3.rolling(window=params["window_size"], min_periods=1).mean()
        lp_view.add_series(
            x=data.columns.values.tolist(),
            y=mean_median.values.tolist(),  # quality median
            name='Median'
        )

        lp_view.add_series(
            x=data.columns.values.tolist(),
            y=mean_q1.values.tolist(),  # quality q1
            name='Q1'
        )

        lp_view.add_series(
            x=data.columns.values.tolist(),
            y=mean_q3.values.tolist(),  # quality q3
            name='Q3'
        )
        lp_view.x_label = "Base position"
        lp_view.y_label = "PHRED score"
        return lp_view


@importer_decorator(unique_name="QualityTableImporter", human_name="Quality Table importer",
                    deprecated=TypingDeprecated(deprecated_since="0.7.0", deprecated_message="Use Table importer instead"),
                    target_type=QualityCheckTable, supported_extensions=Table.ALLOWED_FILE_FORMATS, hide=True)
class QualityTableImporter(TableImporter):
    pass
