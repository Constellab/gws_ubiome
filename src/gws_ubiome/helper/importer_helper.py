# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws_core import ConfigParams, File, Table, TableImporter


class ImporterHelper:

    @staticmethod
    def import_table(file_path, params=None) -> Table:
        if params is None:
            params = ConfigParams({})
        return TableImporter.call(
            file=File(path=file_path),
            params=params
        )
