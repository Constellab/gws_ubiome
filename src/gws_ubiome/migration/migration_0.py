# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import (BrickMigration, Folder, ResourceModel, Version,
                      brick_migration)


@brick_migration('0.6.0', short_description='Remove old folders')
class Migration060(BrickMigration):

    @classmethod
    def migrate(cls, from_version: Version, to_version: Version) -> None:

        ResourceModel.replace_resource_typing_name(
            'RESOURCE.gws_ubiome.Qiime2TaxonomyDiversityFolder', Folder._typing_name)
        ResourceModel.replace_resource_typing_name(
            'RESOURCE.gws_ubiome.Qiime2FeatureFrequencyFolder', Folder._typing_name)
