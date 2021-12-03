# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import File, resource_decorator

@resource_decorator("MetadataFile",
                    human_name="MetadataFile",
                    short_description="Metadata File")
class MetadataFile(File):
    ''' Metadata file class '''
