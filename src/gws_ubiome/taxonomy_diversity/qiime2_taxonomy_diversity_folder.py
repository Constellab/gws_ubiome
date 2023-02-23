# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import Folder, resource_decorator


@resource_decorator("Qiime2TaxonomyDiversityFolder",
                    human_name="Qiime2 taxonomy diversity folder",
                    short_description="Folder containing all extracted Qiime2 taxonomy diversity tables", hide=True)
class Qiime2TaxonomyDiversityFolder(Folder):
    ''' Qiime2TaxonomyDiversityFolder Folder file class '''
