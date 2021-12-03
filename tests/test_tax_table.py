
import os

from gws_core import Settings, TaskRunner, File
from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_gena import ECTableImporter

class TestTaxTable(BaseTestCaseUsingFullBiotaDB):

    async def test_importer(self):
        settings = Settings.retrieve()
        data_dir = settings.get_variable("gws_ubiome:testdata_dir")

        # run trainer
        tester = TaskRunner(
            params = { },
            inputs = {"file": File(path=os.path.join(data_dir, "./tax_table.csv"))},
            task_type = ECTableImporter
        )
        outputs = await tester.run()
        ds = outputs['resource']

        self.assertEqual(ds.get_data().iloc[0,0], "4.1.1.28")
        self.assertEqual(ds.get_data().iloc[2,0], "1.14.17.1")
        print(ds)
