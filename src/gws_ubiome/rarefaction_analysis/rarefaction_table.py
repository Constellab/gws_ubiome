
from json import loads

from gws_core import (
    ConfigParams,
    FSNode,
    LinePlot2DView,
    Resource,
    Table,
    TableImporter,
    TypingDeprecated,
    importer_decorator,
    resource_decorator,
    view,
)
from numpy import nanquantile
from pandas import DataFrame


@resource_decorator(unique_name="RarefactionTable", hide=True,
                    deprecated=TypingDeprecated(deprecated_since="0.7.0", deprecated_message="Use Table instead"))
class RarefactionTable(Table):

    """
    RarefactionTable class
    """

    @view(view_type=LinePlot2DView, human_name='Rarefaction lineplot',
          short_description='Lineplot of the rarefaction table',
          default_view=True)
    def view_as_lineplot(self, params: ConfigParams) -> LinePlot2DView:
        lp_view = LinePlot2DView()
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
        lp_view.x_label = "Count depth"
        lp_view.y_label = "Index value"
#        lp_view.y_label = "Shannon index" if self.get_default_name() == "rarefaction_shannon" else "Observed features value"

        return lp_view


@importer_decorator(unique_name="RarefactionTableImporter", human_name="Rarefaction Table importer",
                    target_type=Table, supported_extensions=Table.ALLOWED_FILE_FORMATS, hide=True)
class RarefactionTableImporter(TableImporter):

    def import_from_path(self, source: FSNode, params: ConfigParams, target_type: type[Resource]) -> Table:
        rarefaction_table: Table = super().import_from_path(source, params, target_type)

        dataframe: DataFrame = rarefaction_table.get_data()

        column_tags = []
        for column_name in dataframe:
            try:
                tags = loads(column_name)
            except:
                tags = {}
            column_tags.append(tags)

        rarefaction_table.set_all_column_tags(column_tags)
        return rarefaction_table
