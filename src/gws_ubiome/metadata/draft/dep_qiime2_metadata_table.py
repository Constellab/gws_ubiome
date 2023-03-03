# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List, Type

from gws_core import (BadRequestException, ConfigParams, File, Table,
                      TableExporter, TableImporter, exporter_decorator,
                      importer_decorator, resource_decorator)

from .dep_qiime2_metadata_table_file import Qiime2MetadataTableFile


@resource_decorator("Qiime2MetadataTable", human_name="Qiime2 metadata table",
                    short_description="Qiime2 metadata table", hide=True)
class Qiime2MetadataTable(Table):

    SAMPLE_COLUMN_ID = "sample-id"
    SECOND_LINE_COLUMN_TYPE = "#q2:types"  # q2:types qiime2 param
    ALLOWED_COLUMN_TYPE_CATEGORICAL = "categorical"
    ALLOWED_COLUMN_TYPE_NUMERIC = "numeric"

    def select_by_row_indexes(self, indexes: List[int]) -> 'Qiime2MetadataTable':
        table: Table = super().select_by_row_indexes(indexes)
        table = Qiime2MetadataTable(data=table.get_data())
        return table

    def select_by_column_indexes(self, indexes: List[int]) -> 'Qiime2MetadataTable':
        raise BadRequestException(
            "It is not allowed to selecte columns of a Qiime2MetadataTable. Please consider using a classical Table.")

    def select_by_row_name(self, name_regex: str) -> 'Qiime2MetadataTable':
        table: Table = super().select_by_row_name(name_regex)
        table = Qiime2MetadataTable(data=table.get_data())
        return table

    def select_by_column_name(self, name_regex: str) -> 'Qiime2MetadataTable':
        raise BadRequestException(
            "It is not allowed to selecte columns of a Qiime2MetadataTable. Please consider using a classical Table.")

# ####################################################################
#
# Importer class
#
# ####################################################################


@importer_decorator(unique_name="Qiime2MetadataTableImporter", human_name="Qiime2 metadata table importer",
                    source_type=Qiime2MetadataTableFile,
                    target_type=Qiime2MetadataTable, supported_extensions=Table.ALLOWED_FILE_FORMATS,
                    hide=True)
class Qiime2MetadataTableImporter(TableImporter):

    def import_from_path(
            self, file: File, params: ConfigParams, target_type: Type[Qiime2MetadataTable]) -> Qiime2MetadataTable:
        params["header"] = 0  # -> force parameter
        params["index_column"] = None  # -> force parameter
        csv_table: Qiime2MetadataTable = super().import_from_path(file, params, target_type)
        data = csv_table.get_data()

        is_categorical = data.iloc[0, 1] == target_type.ALLOWED_COLUMN_TYPE_CATEGORICAL
        is_numeric = data.iloc[0, 1] == target_type.ALLOWED_COLUMN_TYPE_NUMERIC

        if not (csv_table.column_exists(target_type.SAMPLE_COLUMN_ID)):
            raise BadRequestException(
                f"Invalid metadata file. The column {target_type.SAMPLE_COLUMN_ID} does not exist")

        if not data.iloc[1, 0] == target_type.SECOND_LINE_COLUMN_TYPE:
            raise BadRequestException(
                f"Invalid metadata file. The column {target_type.SECOND_LINE_COLUMN_TYPE} does not exist")

        if (not is_categorical) and (not is_numeric):
            raise BadRequestException(
                f"Invalid metadata file. Incorrect type in the column {target_type.SECOND_LINE_COLUMN_TYPE}")

        return csv_table


# ####################################################################
#
# Exporter class
#
# ####################################################################

@exporter_decorator(unique_name="Qiime2MetadataTableExporter", human_name="Qiime2 metadata table exporter",
                    source_type=Qiime2MetadataTable, target_type=Qiime2MetadataTableFile, hide=True)
class Qiime2MetadataTableExporter(TableExporter):
    pass
