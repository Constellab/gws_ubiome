# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json
import os
import time

import pandas
from gws_core import (BaseTestCase, File, Folder, GTest, Settings, TaskRunner,
                      ViewTester, IExperiment, ExperimentRunService, Experiment, ExperimentStatus)
from gws_ubiome import (FastqFolder, Qiime2ManifestTableFile,
                        Qiime2QualityCheck, Qiime2QualityCheckResultFolder)


class TestQiime2QualityCheck(BaseTestCase):

    async def test_importer(self):
        experiment: IExperiment = IExperiment()
        protocol = experiment.get_protocol()
        protocol.add_process(Qiime2QualityCheck, 'check')

#        await experiment.run()



        ExperimentRunService.create_cli_process_for_experiment(
            experiment=experiment._experiment)

        waiting_count = 0
        experiment3: Experiment = Experiment.get_by_id_and_check(experiment._experiment.id)
        while experiment3.status != ExperimentStatus.SUCCESS:
            print("Waiting 3 secs the experiment to finish ...")
            time.sleep(3)
            if waiting_count == 100:
                raise Exception("The experiment is not finished")
            experiment3.refresh()  # reload from DB
            waiting_count += 1


        result = Experiment.get_by_id_and_check(experiment._experiment.id).protocol_model.get_process('check').outputs.get_resource_model('result_folder').get_resource()

        print('HEllo')



