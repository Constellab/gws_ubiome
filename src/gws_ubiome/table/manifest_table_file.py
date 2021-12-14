# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import File, resource_decorator

@resource_decorator("Qiime2ManifestTableFile",
                    human_name="Qiime2ManifestTableFile",
                    short_description="Qiime2 manifest table file")
class Qiime2ManifestTableFile(File):
    ''' Qiime2 manifest table file class '''
    pass