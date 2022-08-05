# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
from zipfile import ZipFile


class Zip:
    """
    Zip class
    """

    @staticmethod
    def unzip(zipfile_path, output_path: str = None) -> str:
        """
        Unzip a file.

        :param zipfile_path: Path of the file to unzip
        :param zipfile_path: `str`
        """

        print(f"Extracting {zipfile_path} ...")
        try:
            with ZipFile(zipfile_path, 'r') as zip_obj:
                if not output_path:
                    output_path = os.path.dirname(zipfile_path)
                if not os.path.exists(output_path):
                    os.makedirs(output_path)
                zip_obj.extractall(output_path)
            print("Extraction finished.")
            return output_path
        except Exception as err:
            print(f"Error: cannot extract {zipfile_path}.\nError message: {err}")
            return None
