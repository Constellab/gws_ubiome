# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Union

from gws_core import File, resource_decorator


@resource_decorator("Qiime2MetadataTableFile",
                    human_name="Qiime2 metadata table file",
                    short_description="Qiime2 metadata table file", hide=True)
class Qiime2MetadataTableFile(File):
    ''' Qiime2 metadata table file class '''

    def check_resource(self) -> Union[str, None]:
        """You can redefine this method to define custom logic to check this resource.
        If there is a problem with the resource, return a string that define the error, otherwise return None
        This method is called on output resources of a task. If there is an error returned, the task will be set to error and next proceses will not be run.
        It is also call when uploading a resource (usually for files or folder), if there is an error returned, the resource will not be uploaded
        """

        # from .qiime2_metadata_table import (Qiime2MetadataTable,
        #                                     Qiime2MetadataTableImporter)
        # try:
        #     _: Qiime2MetadataTable = Qiime2MetadataTableImporter.call(self)
        #     return None
        # except Exception as err:
        return f"Cannot upload the manifest file. The file is not valid. Error: {err}"
