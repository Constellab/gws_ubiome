# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import File, resource_decorator

@resource_decorator("Qiime2MetadataTableFile",
                    human_name="Qiime2MetadataTableFile",
                    short_description="Qiime2 metadata table file")
class Qiime2MetadataTableFile(File):
    ''' Qiime2 metadata table file class '''
    pass