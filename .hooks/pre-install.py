# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os

from utils._requests import Requests
from utils._settings import Settings
from utils._zip import Zip

# **********************************************************
#
# /!\ DO NOT ALTER THIS SECTION
#
# **********************************************************

__cdir__ = os.path.dirname(os.path.realpath(__file__))
DATA_PATH = "/data"


def current_brick_path() -> str:
    """ Get the current brick path """
    return os.path.abspath(os.path.join(__cdir__, '../../'))


def current_brick_name() -> str:
    """ Get the current brick name """
    return read_settings()["name"]


def read_settings() -> dict:
    """ Read the settings file of the current brick """
    return Settings.read()


def unzip(zipfile_path, output_path: str = None) -> str:
    """ Unzip a file and return the destination path """
    return Zip.unzip(zipfile_path, output_path)


def download(url: str, dest_path: str) -> str:
    """ Download a file from a remote url """
    return Requests.download(url, dest_path)


# **********************************************************
#
# UPDATE FUCNTION call_hook() TO ADD YOUR HOOK
#
# **********************************************************
def call_hook():
    """ Call hook """

    settings = read_settings()

    # Pull large testdata & unzip
    url = settings["variables"]["gws_ubiome:large_testdata_url"]
    dest_path = settings["variables"]["gws_ubiome:large_testdata_dir"]
    download(url, dest_path + ".zip")
    if unzip(dest_path + ".zip"):
        os.remove(dest_path + ".zip")

    # # Pull Greengeens Ref data
    # url = settings["variables"]["gws_ubiome:greengenes_ref_url"]
    # dest_path = settings["variables"]["gws_ubiome:greengenes_ref_file"]
    # download(url, dest_path)

    # # Pull Greengeens Classifier
    # url = settings["variables"]["gws_ubiome:greengenes_classifier_url"]
    # dest_path = settings["variables"]["gws_ubiome:greengenes_classifier_file"]
    # download(url, dest_path)

    # # Pull NCBI-16s Classifier
    # url = settings["variables"]["gws_ubiome:ncbi_16s_classifier_url"]
    # dest_path = settings["variables"]["gws_ubiome:ncbi_16s_classifier_file"]
    # download(url, dest_path)
    # Other tasks ...


if __name__ == "__main__":
    call_hook()
