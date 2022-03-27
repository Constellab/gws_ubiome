# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Union

from gws_core import File, resource_decorator


@resource_decorator("Qiime2ManifestTableFile",
                    human_name="Qiime2 manifest table file",
                    short_description="Qiime2 manifest table file", hide=True)
class Qiime2ManifestTableFile(File):
    ''' Qiime2 manifest table file class '''

    def check_resource(self) -> Union[str, None]:
        """You can redefine this method to define custom logic to check this resource.
        If there is a problem with the resource, return a string that define the error, otherwise return None
        This method is called on output resources of a task. If there is an error returned, the task will be set to error and next proceses will not be run.
        It is also call when uploading a resource (usually for files or folder), if there is an error returned, the resource will not be uploaded
        """

        from .qiime2_manifest_table import (Qiime2ManifestTable,
                                            Qiime2ManifestTableImporter)
        try:
            _: Qiime2ManifestTable = Qiime2ManifestTableImporter.call(self)
            return None
        except Exception as err:
            return f"Cannot upload the manifest file. The file is not valid. Error: {err}"
