# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
from json import loads
from typing import Type, Union

from gws_core import (BarPlotView, BoxPlotView, ConfigParams, File, Folder,
                      FSNode, IntParam, LinePlot2DView, MultiViews, Resource,
                      StackedBarPlotView, StrParam, StrRField, Table,
                      TableExporter, TableImporter, exporter_decorator,
                      importer_decorator, resource_decorator, view)
from gws_core.extra import TableBoxPlotView, TableView
from numpy import nanquantile
from pandas import DataFrame


@resource_decorator(unique_name="RarefactionTable", hide=True)
class RarefactionTable(Table):

    """
    RarefactionTable class
    """

    # @view(view_type=BoxPlotView, human_name='Rarefaction boxplot',
    #       short_description='Boxplot of the rarefaction table',
    #       specs={"type": StrParam(allowed_values=["rarefaction_shannon", "rarefaction_observed"])})
    # def view_as_boxplot(self, params: ConfigParams) -> BoxPlotView:
    #     type_ = params["type"]
    #     table: Table = self._load_table(type_=type_)

    #     bx_view = BoxPlotView()
    #     data = table.get_data()
    #     bx_view.add_data(data=data)
    #     bx_view.x_label = "depth"
    #     bx_view.y_label = "shannon index" if type_ == "rarefaction_shannon" else "observed features value"
    #     return bx_view

    @view(view_type=LinePlot2DView, human_name='Rarefaction lineplot',
          short_description='Lineplot of the rarefaction table',
          specs={})
    def view_as_lineplot(self, params: ConfigParams) -> LinePlot2DView:
        # type_ = params["type"]
        # table: Table = self._load_table(type_=type_)
        # table = table.select_numeric_columns(drop_na='all')

        lp_view = LinePlot2DView()
        #table = self.get_data()

        #data = table.get_data()
        column_tags = self.get_column_tags()
        all_sample_ids = list(set([tag["sample-id"] for tag in column_tags]))

        for sample_id in all_sample_ids:
            sample_table = self.select_by_column_tags([{"sample-id": sample_id}])
            sample_column_tags = sample_table.get_column_tags()
            positions = [float(tag["depth"]) for tag in sample_column_tags]

            sample_data = sample_table.get_data()
            quantile = nanquantile(sample_data.to_numpy(), q=[0.25, 0.5, 0.75], axis=0)
            median = quantile[1, :].tolist()
            lp_view.add_series(x=positions, y=median, name=sample_id, tags=sample_column_tags)

        lp_view.x_label = "depth"
        # lp_view.y_label = "shannon index" if type_ == "rarefaction_shannon" else "observed features value"
        return lp_view


@importer_decorator(unique_name="RarefactionTableImporter", human_name="Rarefaction Table importer",
                    target_type=RarefactionTable, supported_extensions=Table.ALLOWED_FILE_FORMATS, hide=True)
class RarefactionTableImporter(TableImporter):
    async def import_from_path(self, source: FSNode, params: ConfigParams, target_type: Type[Resource]) -> Resource:
        rarefaction_table: RarefactionTable = await super().import_from_path(source, params, target_type)

        dataframe: DataFrame = rarefaction_table.get_data()

        column_tags = []
        for column_name in dataframe:
            try:
                tags = loads(column_name)
            except:
                tags = {}
            column_tags.append(tags)

        rarefaction_table.set_column_tags(column_tags)
        return rarefaction_table