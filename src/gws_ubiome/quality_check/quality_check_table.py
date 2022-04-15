# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import (BoxPlotView, ConfigParams, File, IntParam,
                      LinePlot2DView, Table, TableExporter, TableImporter,
                      exporter_decorator, importer_decorator,
                      resource_decorator, view)


@resource_decorator(unique_name="QualityCheckTable", hide=True)
class QualityCheckTable(Table):

    """
    QualityCheckTable class
    """

    # def check_resource(self) -> Union[str, None]:
    #     """You can redefine this method to define custom logic to check this resource.
    #     If there is a problem with the resource, return a string that define the error, otherwise return None
    #     This method is called on output resources of a task. If there is an error returned, the task will be set to error and next proceses will not be run.
    #     It is also call when uploading a resource (usually for files or folder), if there is an error returned, the resource will not be uploaded
    #     """

    #     from gws_core import Table, TableExporter, TableImporter
    #     try:
    #         _: Table = QualityTableImporter.call(self)
    #         return None
    #     except Exception as err:
    #         return f" The table file is not valid. Error: {err}"

    @view(view_type=BoxPlotView, human_name='Sequencing quality boxplot',
          short_description='Boxplot of the reads sequencing quality',
          specs={},
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
          specs={"window_size": IntParam(default_value=15)},
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
                    target_type=QualityCheckTable, supported_extensions=Table.ALLOWED_FILE_FORMATS, hide=True)
class QualityTableImporter(TableImporter):
    pass


# @exporter_decorator(unique_name="Qiime2MetadataTableExporter", human_name="Qiime2 metadata table exporter",
#                     source_type=QualityCheckTable, target_type=QualityCheckTable)
# class QualityTableExporter(TableExporter):
#     pass