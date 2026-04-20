import os

from gws_core import BaseTestCase, File, PlotlyResource, ResourceSet, TaskRunner
from gws_ubiome import Ggpicrust2FunctionalAnalysis

TESTDATA = os.path.abspath(os.path.join(os.path.dirname(__file__), "testdata"))


class TestGgpicrust2Visualization(BaseTestCase):

    def test_visualization_linda(self):
        """Ggpicrust2FunctionalAnalysis runs on mini KO abundance + metadata (LinDA method)."""
        self.print("Test Ggpicrust2FunctionalAnalysis: mini_ko_abundance.tsv + mini_metadata_ggpicrust.tsv")

        ko_file = os.path.join(TESTDATA, "mini_ko_abundance.tsv")
        meta_file = os.path.join(TESTDATA, "mini_metadata_ggpicrust.tsv")

        if not os.path.exists(ko_file) or not os.path.exists(meta_file):
            self.skipTest("ggpicrust2 testdata not found (mini_ko_abundance.tsv / mini_metadata_ggpicrust.tsv)")

        outputs = TaskRunner(
            task_type=Ggpicrust2FunctionalAnalysis,
            inputs={
                "ko_abundance_file": File(ko_file),
                "metadata_file": File(meta_file),
            },
            params={
                "DA_method": "LinDA",
                "Samples_column_name": "sample-id",
                "Reference_column": "group",
                "Reference_group": "control",
                "Round_digit": False,
                "PCA_component": False,
            },
        ).run()

        self.assertIn("resource_set", outputs)
        rs: ResourceSet = outputs["resource_set"]
        self.assertIsNotNone(rs)
        self.print(f"ggpicrust2 resource_set keys: {list(rs.get_resources().keys())}")

        self.assertIn("plotly_result", outputs)
        pca: PlotlyResource = outputs["plotly_result"]
        self.assertIsNotNone(pca)
        self.print("ggpicrust2 plotly_result: OK")
