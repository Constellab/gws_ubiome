# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import (ConfigParams, ProcessSpec, Protocol, Sink, Source,
                      protocol_decorator)

from ..metabarcoding.qiime2_taxonomy_diversity import Qiime2TaxonomyDiversity


@protocol_decorator("Qiime2TaxonomyDiversityProto")
class Qiime2TaxoProto(Protocol):

    def configure_protocol(self, config_params: ConfigParams) -> None:

        input_folder_source: ProcessSpec = self.add_process(Source, 'rarefaction_result_folder_source')
        qiime2_taxo_diversity: ProcessSpec = self.add_process(Qiime2TaxonomyDiversity, 'qiime2_taxonomy')
        result_folder_sink: ProcessSpec = self.add_process(Sink, 'result_folder_sink')

        self.add_connectors([
            (input_folder_source >> "resource", qiime2_taxo_diversity << "rarefaction_result_folder"),
            (qiime2_taxo_diversity >> "result_folder", result_folder_sink << "resource")
        ])
