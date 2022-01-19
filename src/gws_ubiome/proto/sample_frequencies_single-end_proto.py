# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import (ConfigParams, ProcessSpec, Protocol, Sink, Source,
                      protocol_decorator)

from ..metabarcoding.qiime2_sample_frequencies_single_end import \
    Qiime2SampleFrequenciesSE


@protocol_decorator("Qiime2SampleFrequenciesSingleProto")
class Qiime2SampleFrequenciesSingleProto(Protocol):

    def configure_protocol(self, config_params: ConfigParams) -> None:

        input_folder_source: ProcessSpec = self.add_process(Source, 'quality_check_result_folder_source')
        qiime2_sample_freq: ProcessSpec = self.add_process(Qiime2SampleFrequenciesSE, 'qiime2_sample_freq')
        result_folder_sink: ProcessSpec = self.add_process(Sink, 'result_folder_sink')

        self.add_connectors([
            (input_folder_source >> "resource", qiime2_sample_freq << "quality_check_result_folder"),
            (qiime2_sample_freq >> "result_folder", result_folder_sink << "resource")
        ])