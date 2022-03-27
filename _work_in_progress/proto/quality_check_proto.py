# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import (ConfigParams, ProcessSpec, Protocol, Sink, Source,
                      protocol_decorator)

from ..metabarcoding.qiime2_quality_check import Qiime2QualityCheck


@protocol_decorator("Qiime2QualityCheckProto")
class Qiime2QualityCheckProto(Protocol):

    def configure_protocol(self, config_params: ConfigParams) -> None:

        fastq_folder_source: ProcessSpec = self.add_process(Source, 'fastq_folder_source')
        manifest_table_file_source: ProcessSpec = self.add_process(Source, 'manifest_table_file_source')
        qiime2_quality_check: ProcessSpec = self.add_process(Qiime2QualityCheck, 'qiime2_quality_check')
        result_folder_sink: ProcessSpec = self.add_process(Sink, 'result_folder_sink')

        self.add_connectors([
            (fastq_folder_source >> "resource", qiime2_quality_check << "fastq_folder"),
            (manifest_table_file_source >> "resource", qiime2_quality_check << "manifest_table_file"),
            (qiime2_quality_check >> "result_folder", result_folder_sink << "resource")
        ])
