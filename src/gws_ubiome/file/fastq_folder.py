# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import File, resource_decorator, Folder

@resource_decorator("FastqFolder",
                    human_name="FastqFolder",
                    short_description="FastqFolder", hide=True)
class FastqFolder(Folder):
    ''' Fastq Folder file class '''
    pass
