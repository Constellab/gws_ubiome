import os

from gws_core import MessageDispatcher, PipShellProxy


class FunfunShellProxyHelper():
    ENV_DIR_NAME = "FunfunShellProxy"
    ENV_FILE_PATH = os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        "./env_files/Funfun_env.txt"
    )

    @classmethod
    def create_proxy(cls, message_dispatcher: MessageDispatcher = None):
        return PipShellProxy(env_file_path=cls.ENV_FILE_PATH, env_name=cls.ENV_DIR_NAME,
                             message_dispatcher=message_dispatcher)
