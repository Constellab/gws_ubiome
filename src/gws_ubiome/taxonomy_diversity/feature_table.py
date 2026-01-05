
from gws_core import (
    ConfigParams,
    StackedBarPlotView,
    Table,
    TypingDeprecated,
    resource_decorator,
    view,
)


@resource_decorator(unique_name="FeatureTable", hide=False,
                    deprecated=TypingDeprecated(deprecated_since="0.7.0", deprecated_message="Use Table instead"))
class FeatureTable(Table):
    """
    FeatureTable class
    """
    @view(view_type=StackedBarPlotView, human_name='Feature stacked barplot',
          short_description='Feature stacked barplots',
          default_view=False)
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
