# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
from typing import List
import pandas
from pandas import DataFrame
from gws_core import BoolRField, Table, resource_decorator, BadRequestException, ResourceExporter, ResourceImporter, File, ConfigParams, import_from_path, importer_decorator, exporter_decorator, TableImporter

#SAMPLE_COLUMN_ID = "sample-id"
#ABSOLUTE_FILE_PATH_COLUMN_NAME = "absolute-filepath"
#FORWARD_ABSOLUTE_FILE_PATH_COLUMN_NAME = "forward-absolute-filepath"
#REVERSE_ABSOLUTE_FILE_PATH_COLUMN_NAME = "reverse-absolute-filepath"

@resource_decorator("Qiime2ManifestTable", human_name="Qiime2ManifestTable", short_description="Qiime2 manifest table")
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

    @classmethod
    @import_from_path(specs={
        **TableImporter.config_specs
    })
    #def import_from_path(cls,  file: File, params: ConfigParams) -> 'Qiime2ManifestTable':
    def import_from_path(self, file: File, params: ConfigParams) -> 'Qiime2ManifestTable':
        """
        Import from a repository

        Additional parameters

        :param file: The file to import
        :type file: `File`
        :param params: The config params
        :type params: `ConfigParams`
        :returns: the parsed manifest table
        :rtype: Qiime2ManifestTable
        """

        params["header"] = 0
        params["index_columns"] = []
        test=file.read()
        print(test)
        csv_table: Table = super().import_from_path(file, params)

        if not csv_table.column_exists(self.SAMPLE_COLUMN_ID):
            raise BadRequestException(
                f"Invalid manifest file. The column {self.SAMPLE_COLUMN_ID} does not exist")

        is_single_end_file = csv_table.column_exists(self.ABSOLUTE_FILE_PATH_COLUMN_NAME)
        is_paired_end_file = csv_table.column_exists(self.FORWARD_ABSOLUTE_FILE_PATH_COLUMN_NAME) and \
                             csv_table.column_exists(self.REVERSE_ABSOLUTE_FILE_PATH_COLUMN_NAME)

        if (not is_single_end_file) and (not is_paired_end_file):
            raise BadRequestException(
                f"Invalid manifest file. Either a single-end or paired-end file is expected. Check column names.")

        if is_single_end_file and is_paired_end_file:
            raise BadRequestException(
                f"Invalid manifest file. Either a single-end or paired-end file is expected. Check column names.")

        return csv_table

    def select_by_row_indexes(self, indexes: List[int]) -> 'ManifestTable':
        table: Table = super().select_by_row_indexes(indexes)
        table = ManifestTable(data=table.get_data())
        return table

    def select_by_column_indexes(self, indexes: List[int]) -> 'ManifestTable':
        table: Table = super().select_by_column_indexes(indexes)
        table = ManifestTable(data=table.get_data())
        return table

    def select_by_row_name(self, name_regex: str) -> 'ManifestTable':
        table: Table = super().select_by_row_name(name_regex)
        table = ManifestTable(data=table.get_data())
        return table

    def select_by_column_name(self, name_regex: str) -> 'ManifestTable':
        table: Table = super().select_by_column_name(name_regex)
        table = ManifestTable(data=table.get_data())
        return table

# ####################################################################
#
# Importer class
#
# ####################################################################

@importer_decorator(unique_name="Qiime2ManifestTableImporter", resource_type=Qiime2ManifestTable)
class Qiime2ManifestTableImporter(ResourceImporter):
    pass

# ####################################################################
#
# Exporter class
#
# ####################################################################

@exporter_decorator(unique_name="TableExporter", resource_type=Qiime2ManifestTable)
class Qiime2ManifestTableExporter(ResourceExporter):
    pass