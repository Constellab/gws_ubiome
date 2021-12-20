# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List

from gws_core import (BadRequestException, StrRField, Table,
                      TableAggregatorHelper, TableFilterHelper,
                      resource_decorator)
from pandas import DataFrame


@resource_decorator("TaxTable", human_name="TaxTable", short_description="Taxonomy table")
class TaxTable(Table):

    DEFAULT_TAX_LEVEL_COLUMN = "tax_level"
    DEFAULT_TAXON_COLUMN = "taxon"
    DEFAULT_RANK_ID_COLUMN = "rank_id"

    tax_level_column: str = StrRField(default_value=DEFAULT_TAX_LEVEL_COLUMN)
    taxon_column: str = StrRField(default_value=DEFAULT_TAXON_COLUMN)
    rank_id_column: str = StrRField(default_value=DEFAULT_RANK_ID_COLUMN)

    def _get_data_filtered_by_tax_level(self, tax_level) -> DataFrame:
        data = self._data[self.tax_level_column == tax_level]
        return data

    # -- S --

    def select_by_row_indexes(self, indexes: List[int]) -> 'TaxTable':
        table = super().select_by_row_indexes(indexes)
        table = TaxTable(data=table.get_data())
        table.tax_level_column = self.tax_level_column
        return table

    def select_by_column_indexes(self, indexes: List[int]) -> 'TaxTable':
        table = super().select_by_column_indexes(indexes)
        table = TaxTable(data=table.get_data())
        table.tax_level_column = self.tax_level_column
        return table

    def select_by_row_name(self, name_regex: str) -> 'TaxTable':
        table = super().select_by_row_name(name_regex)
        table = TaxTable(data=table.get_data())
        table.tax_level_column = self.tax_level_column
        return table

    def select_by_column_name(self, name_regex: str) -> 'TaxTable':
        table = super().select_by_column_name(name_regex)
        table = TaxTable(data=table.get_data())
        table.tax_level_column = self.tax_level_column
        return table
