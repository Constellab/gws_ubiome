# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
import copy

import numpy as np
from gws_core import (ConfigParams, StackedBarPlotView, Table, TableImporter,
                      importer_decorator, resource_decorator, view)


@resource_decorator(unique_name="FeatureTable", hide=False)
class FeatureTable(Table):
    """
    FeatureTable class
    """
    @view(view_type=StackedBarPlotView, human_name='Feature stacked barplot',
          short_description='Feature stacked barplots',
          specs={}, default_view=False)
    def view_as_noramlised_taxo_stacked_bar_plot(self, params: ConfigParams) -> StackedBarPlotView:
        s_view = StackedBarPlotView(normalize=True)
        data = self.get_data()
        tdata = data.T
        for i in range(0, tdata.shape[1]):
            if isinstance(tdata.iat[0, i], str):
                continue
            y = tdata.iloc[:, i].values.tolist()
            s_view.add_series(y=y, name=tdata.columns[i])
        s_view.x_tick_labels = tdata.index.to_list()
        s_view.y_label = "Feature count"
        s_view.x_label = "Samples"
        return s_view


@importer_decorator(unique_name="FeatureTableImporter", human_name="Feature Table importer",
                    target_type=FeatureTable, supported_extensions=Table.ALLOWED_FILE_FORMATS, hide=True)
class FeatureTableImporter(TableImporter):
    pass
