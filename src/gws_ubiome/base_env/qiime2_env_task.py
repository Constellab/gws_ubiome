# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
from gws_core import task_decorator, CondaEnvShell

@task_decorator("Qiime2EnvTask", hide=True)
class Qiime2EnvTask(CondaEnvShell):
    unique_env_name = "Qiime2EnvTask"
    env_file_path = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), 
        "./env_files/qiime2-2021.11-py38-linux-conda.yml"
    )
