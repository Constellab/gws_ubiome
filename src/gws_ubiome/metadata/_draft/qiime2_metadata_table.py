# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
from typing import List, Type

from gws_core import (BadRequestException, ConfigParams, File, MetadataTable,
                      MetadataTableImporter, Table, TableExporter,
                      TableImporter, exporter_decorator, importer_decorator,
                      resource_decorator)


@resource_decorator("Qiime2MetadataTable", human_name="Qiime2 metadata table",
                    short_description="Qiime2 manifest table")
class Qiime2MetadataFile(File):

    ''' Qiime2 metadata table file class '''

    def check_resource(self):
        """You can redefine this method to define custom logic to check this resource.
        If there is a problem with the resource, return a string that define the error, otherwise return None
        This method is called on output resources of a task. If there is an error returned, the task will be set to error and next proceses will not be run.
        It is also call when uploading a resource (usually for files or folder), if there is an error returned, the resource will not be uploaded
        """
        metadata_table = MetadataTableImporter.call(File(self.path), {'delimiter': 'tab'})

        return metadata_table


