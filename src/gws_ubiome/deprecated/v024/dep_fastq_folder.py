# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List, Union

from gws_core import File, Folder, Shell, ShellProxy, resource_decorator


@resource_decorator("FastqFolder",
                    human_name="Depreciated Fastq folder",
                    short_description="Folder containing fastq files", hide=False, deprecated_since='0.2.5',
                    deprecated_message='Please use Omix fastq folder')
class FastqFolder(Folder):
    ''' Fastq Folder file class '''

    def check_resource(self) -> Union[str, None]:
        """You can redefine this method to define custom logic to check this resource.
        If there is a problem with the resource, return a string that define the error, otherwise return None
        This method is called on output resources of a task. If there is an error returned, the task will be set to error and next proceses will not be run.
        It is also call when uploading a resource (usually for files or folder), if there is an error returned, the resource will not be uploaded
        """

        files: List[str] = self.list_dir()
        bz2_exists = False
        for file in files:
            if file.endswith('.bz2'):
                bz2_exists = True
                break

        if bz2_exists:
            cmd = ["for f in *.bz2 ;do bzcat < \"$f\" | pigz -9 -c >\"${f%.*}.gz\" ;done ; rm *.bz2 ;"]
#            cmd = [ "parallel --dry-run 'bzcat < {} | pigz -9 -c > {.}.gz' ::: *bz2 > tmp.sh ; bash tmp.sh ; rm tmp.sh ; rm *.bz2 ;" ]
            shell_proxy = ShellProxy(Shell)
            try:
                shell_proxy.run(cmd, cwd=self.path, shell_mode=True)
                return None
            except Exception as err:
                return f"Cannot upload the folder. Error message: {err}"
        else:
            return None
