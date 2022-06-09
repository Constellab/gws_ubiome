# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
from typing import List, Type

from gws_core import (BadRequestException, ConfigParams, File, Table,
                      TableExporter, TableImporter, exporter_decorator,
                      importer_decorator, resource_decorator)
from pandas import DataFrame

from .qiime2_manifest_table_file import Qiime2ManifestTableFile


@resource_decorator("Qiime2ManifestTable", human_name="Qiime2 manifest table",
                    short_description="Qiime2 manifest table")
class Qiime2ManifestTable(Table):

    SAMPLE_COLUMN_ID = "sample-id"
    ABSOLUTE_FILE_PATH_COLUMN_NAME = "absolute-filepath"
    FORWARD_ABSOLUTE_FILE_PATH_COLUMN_NAME = "forward-absolute-filepath"
    REVERSE_ABSOLUTE_FILE_PATH_COLUMN_NAME = "reverse-absolute-filepath"

    def _export_for_task(self, abs_file_dir, abs_output_dir) -> str:
        abs_file_dir = abs_file_dir.rstrip('/')
        abs_output_dir = abs_output_dir.rstrip('/')
        data: DataFrame = self._data.copy(deep=True)
        is_single_end_file = self.column_exists(self.ABSOLUTE_FILE_PATH_COLUMN_NAME)
        if is_single_end_file:
            col = self.ABSOLUTE_FILE_PATH_COLUMN_NAME
            data[col] = abs_file_dir + "/" + data[col]
        else:
            col = self.FORWARD_ABSOLUTE_FILE_PATH_COLUMN_NAME
            data[col] = abs_file_dir + "/" + data[col]

            col = self.REVERSE_ABSOLUTE_FILE_PATH_COLUMN_NAME
            data[col] = abs_file_dir + "/" + data[col]

        output_file = os.path.join(abs_output_dir, "./manifest.csv")
        data.to_csv(output_file, index=False, header=True, sep="\t")
        return output_file

    def select_by_row_indexes(self, indexes: List[int]) -> 'Qiime2ManifestTable':
        table: Table = super().select_by_row_indexes(indexes)
        table = Qiime2ManifestTable(data=table.get_data())
        return table

    def select_by_column_indexes(self, indexes: List[int]) -> 'Qiime2ManifestTable':
        raise BadRequestException(
            "It is not allowed to selecte columns of a Qiime2ManifestTable. Please consider using a classical Table.")

    def select_by_row_name(self, name_regex: str) -> 'Qiime2ManifestTable':
        table: Table = super().select_by_row_name(name_regex)
        table = Qiime2ManifestTable(data=table.get_data())
        return table

    def select_by_column_name(self, name_regex: str) -> 'Qiime2ManifestTable':
        raise BadRequestException(
            "It is not allowed to selecte columns of a Qiime2ManifestTable. Please consider using a classical Table.")

# ####################################################################
#
# Importer class
#
# ####################################################################


@importer_decorator(unique_name="Qiime2ManifestTableImporter", human_name="Qiime2 manifest table importer",
                    source_type=Qiime2ManifestTableFile, target_type=Qiime2ManifestTable, hide=True,
                    supported_extensions=Table.ALLOWED_FILE_FORMATS)
class Qiime2ManifestTableImporter(TableImporter):

    async def import_from_path(self, file: File, params: ConfigParams, target_type: Type[Qiime2ManifestTable]) -> Qiime2ManifestTable:
        params["header"] = 0  # -> force parameter
        params["index_columns"] = []  # -> force parameter

        csv_table: Qiime2ManifestTable = await super().import_from_path(file, params, target_type)

        if not csv_table.column_exists(target_type.SAMPLE_COLUMN_ID):
            raise BadRequestException(
                f"Invalid manifest file. The column {target_type.SAMPLE_COLUMN_ID} does not exist")

        is_single_end_file = csv_table.column_exists(target_type.ABSOLUTE_FILE_PATH_COLUMN_NAME)
        is_paired_end_file = csv_table.column_exists(target_type.FORWARD_ABSOLUTE_FILE_PATH_COLUMN_NAME) and \
            csv_table.column_exists(target_type.REVERSE_ABSOLUTE_FILE_PATH_COLUMN_NAME)

        if (not is_single_end_file) and (not is_paired_end_file):
            raise BadRequestException(
                "Invalid manifest file. Either a single-end or paired-end file is expected. Check column names.")

        if is_single_end_file and is_paired_end_file:
            raise BadRequestException(
                "Invalid manifest file. Either a single-end or paired-end file is expected. Check column names.")

        return csv_table


# ####################################################################
#
# Exporter class
#
# ####################################################################

@exporter_decorator(unique_name="Qiime2ManifestTableExporter", human_name="Qiime2 manifest table exporter",
                    source_type=Qiime2ManifestTable, target_type=Qiime2ManifestTableFile)
class Qiime2ManifestTableExporter(TableExporter):
    pass
