
from json import dumps, loads
from typing import List

from gws_core import (BrickMigration, File, Folder, ResourceModel, TaskModel,
                      Version, brick_migration)
from gws_omix import FastqFolder


@brick_migration('0.6.0', short_description='Remove old folders')
class Migration060(BrickMigration):

    @classmethod
    def migrate(cls, from_version: Version, to_version: Version) -> None:

        typing_dict = {
            'RESOURCE.gws_ubiome.Qiime2TaxonomyDiversityFolder': Folder.get_typing_name(),
            'RESOURCE.gws_ubiome.Qiime2FeatureFrequencyFolder': Folder.get_typing_name(),
            'RESOURCE.gws_ubiome.Qiime2DifferentialAnalysisResultFolder': Folder.get_typing_name(),
            'RESOURCE.gws_ubiome.Qiime2QualityCheckResultFolder': Folder.get_typing_name(),
            'RESOURCE.gws_ubiome.Qiime2RarefactionAnalysisResultFolder': Folder.get_typing_name(),
            'RESOURCE.gws_ubiome.Qiime2MetadataTableFile': File.get_typing_name(),
            'RESOURCE.gws_ubiome.FastqFolder': FastqFolder.get_typing_name(),
            'RESOURCE.gws_omix.FastaFile': File.get_typing_name()
        }

        for key, value in typing_dict.items():
            ResourceModel.replace_resource_typing_name(key, value)

        # replace the references in the tasks inputs and outputs specs
        tasks_models: List[TaskModel] = list(TaskModel.select())
        for task_model in tasks_models:
            for key, value in typing_dict.items():
                task_model.data = loads(dumps(task_model.data).replace(key, value))

            task_model.save(skip_hook=True)
