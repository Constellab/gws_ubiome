# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List
from pandas import DataFrame
from gws_core import Table, resource_decorator, BadRequestException, TableAggregatorHelper, TableFilterHelper, StrRField

EC_TABLE_DEFAULT_TAX_LEVEL_COLUMN = "tax_level"
EC_TABLE_DEFAULT_TAXON_COLUMN = "taxon"
EC_TABLE_DEFAULT_RANK_ID_COLUMN = "rank_id"

@resource_decorator("TaxTable", human_name="TaxTable", short_description="Taxonomy table")
class TaxTable(Table):
    
    DEFAULT_TAX_LEVEL_COLUMN = EC_TABLE_DEFAULT_TAX_LEVEL_COLUMN
    EC_TABLE_DEFAULT_TAXON_COLUMN = EC_TABLE_DEFAULT_TAXON_COLUMN
    EC_TABLE_DEFAULT_RANK_ID_COLUMN = EC_TABLE_DEFAULT_RANK_ID_COLUMN

    tax_level_column: str = StrRField(default_value=DEFAULT_TAX_LEVEL_COLUMN)
    taxon_column: str = StrRField(default_value=EC_TABLE_DEFAULT_TAXON_COLUMN)
    rank_id_column: str = StrRField(default_value=EC_TABLE_DEFAULT_RANK_ID_COLUMN)

    def _get_data_filtered_by_tax_level(self, tax_level) -> DataFrame:
        data = self._data[ self.tax_level_column == tax_level ]
        return data

    # def _get_data_aggregated_by_level(self, tax_level) -> DataFrame:
    #     level_data: DataFrame = self._data[ self.tax_level_column == tax_level ]
    #     level_rank_ids: List[str] = level_data.loc[ :,self.rank_id_column ].tolist()
    #     level_taxa: List[str] = level_data.loc[ :,self.taxon_column ].tolist()

    #     data_sum = DataFrame()
    #     for i, level_taxon in enumerate(level_taxa):
    #         level_rank_id = level_rank_ids[i]
    #         tf = self._data.loc[ :,self.rank_id_column ].str.startswith(level_rank_id)
    #         lower_level_data: DataFrame = self._data.loc[tf, :]
    #         level_data_sum = lower_level_data.sum(skipna=True)
    #         level_data_sum.index[0] = level_taxon
    #         level_data_sum.loc[level_taxon, self.taxon_column] = level_taxon

    #         data_sum = pandas.concat([data_sum, level_data_sum])

    #     return data_sum
    
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