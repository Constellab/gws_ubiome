
import os

from gws_core import (ConfigParams, File, Folder, InputSpec, InputSpecs,
                      OutputSpec, OutputSpecs, ResourceSet, ShellProxy,
                      Table, TableAnnotatorHelper,
                      TableImporter, Task, TaskInputs, TaskOutputs,
                      task_decorator)
from gws_core.impl.plotly.plotly_resource import PlotlyResource

from ..base_env.qiime2_env_task import Qiime2ShellProxyHelper

import plotly.graph_objects as go


@task_decorator("Qiime2TableDbAnnotator", human_name="Qiime2 taxa composition annotator",
                short_description="Performs Qiime2 taxa composition annotator with a given db")
class Qiime2TableDbAnnotator(Task):
    """
    Qiime2TableDbAnnotator class.

    [Mandatory]:
        - taxa table coming from qiime2 taxa compo :
            Expcted format (included in the qiime2 diversity folder output object):
                index	k__Bacteria;p__Fi;c__Clo;o__Clostri;f__toto;g__gege;s__titi
                sample_1    1205
                sample_2    1705

        - metadata file must follow specific nomenclature (columns are tab separated):

            Expected format :
                # tax_id	annotation_info
                bact_1  0
                bact_2  1
                bact_3  Variable;toto_1:0;others:1


    """
    TAGGING_TABLE = "taxa_found.for_tags.tsv"
    TAX_LEVEL_DICT = {
        "k": "1",
        "p": "2",
        "c": "3",
        "o": "4",
        "f": "5",
        "g": "6",
        "s": "7",
    }
    input_specs: InputSpecs = InputSpecs({
        'diversity_folder': InputSpec(Folder, human_name="Diversity_qiime2_folder"),
        'annotation_table': InputSpec(File, short_description="Annotation table: taxa<tabulation>info", human_name="Annotation_table")})
    output_specs: OutputSpecs = OutputSpecs({
        'relative_abundance_table': OutputSpec(Table, human_name="Relative_Abundance_Annotated_Table"),
        'relative_abundance_plotly_resource': OutputSpec(PlotlyResource, human_name="Relative_Abundance_Annotated_Plotly_Resource"),
        'absolute_abundance_table': OutputSpec(Table, human_name="Absolute_Abundance_Annotated_Table"),
        'absolute_abundance_plotly_resource': OutputSpec(PlotlyResource, human_name="Absolute_Abundance_Annotated_Plotly_Resource")
    })

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        # get options, I/O variables
        diversity_input_folder: Folder = inputs["diversity_folder"]
        metadata_table = inputs["annotation_table"]

        script_file_dir = os.path.dirname(os.path.realpath(__file__))
        shell_proxy = Qiime2ShellProxyHelper.create_proxy(self.message_dispatcher)

        # perform ANCOM analysis

        outputs = self.run_cmd(shell_proxy,
                               diversity_input_folder,
                               metadata_table,
                               script_file_dir,
                               params
                               )

        return outputs

    def run_cmd(self, shell_proxy: ShellProxy,
                diversity_input_folder: Folder,
                metadata_table: File,
                script_file_dir: str,
                params: ConfigParams) -> TaskOutputs:

        taxa_db_type = "GreenGenes"
        taxa_file_path = os.path.join(diversity_input_folder.path, "table_files")

        cmd = [
            "bash",
            os.path.join(script_file_dir, "./sh/all_taxa.sh"),
            metadata_table.path,
            taxa_file_path,
            os.path.join(script_file_dir, "./perl/taxa_annot_all.pl"),
            os.path.join(script_file_dir, "./perl/ratio_calc.pl"),
            taxa_db_type
        ]
        shell_proxy.run(cmd)

        path = os.path.join(diversity_input_folder.path, "raw_files", "gws_metadata.csv")
        sample_metadata_table = TableImporter.call(File(path=path), {'delimiter': 'tab'})
        #  Dictionary table containing corresponding taxa in both files
        annotated_tables_set: ResourceSet = ResourceSet()
        annotated_tables_set.name = "Set of tables"  # taxa_merged_files.relative.tsv

        tag_file_path = os.path.join(shell_proxy.working_dir, "taxa_found.for_tags.tsv")
        metadata_table = TableImporter.call(File(path=tag_file_path), {'delimiter': 'tab'})

        tag_file_relative_path = os.path.join(shell_proxy.working_dir, "taxa_found.for_tags.relative.tsv")
        metadata_relative_table = TableImporter.call(File(path=tag_file_relative_path), {'delimiter': 'tab'})

        taxa_dict_path = os.path.join(shell_proxy.working_dir, "taxa_found.tsv")
        taxa_relative_dict_path = os.path.join(shell_proxy.working_dir, "taxa_found.relative.tsv")

        taxa_dict_table = TableImporter.call(
            File(path=taxa_dict_path),
            {'delimiter': 'tab', "index_column": 0})

        taxa_relative_dict_table = TableImporter.call(
            File(path=taxa_relative_dict_path),
            {'delimiter': 'tab', "index_column": 0})

        # file to use to add tag

        table_annotated_col = TableAnnotatorHelper.annotate_columns(
            taxa_dict_table, metadata_table, use_table_column_names_as_ref=True)
        table_relative_annotated_col = TableAnnotatorHelper.annotate_columns(
            taxa_relative_dict_table, metadata_relative_table, use_table_column_names_as_ref=True)
        table_absolute_abundance_annotated = TableAnnotatorHelper.annotate_rows(
            table_annotated_col, sample_metadata_table, use_table_row_names_as_ref=True)
        table_relative_abundance_annotated = TableAnnotatorHelper.annotate_rows(
            table_relative_annotated_col, sample_metadata_table, use_table_row_names_as_ref=True)

        table_absolute_abundance_annotated.name = "Annotated taxa composition table (absolute count)"
        table_relative_abundance_annotated.name = "Annotated taxa composition table (relative count)"

        relative_abundance_plotly_resource = self.stackedbarplot_plotly(table_relative_abundance_annotated)
        absolute_abundance_plotly_resource = self.stackedbarplot_plotly(table_absolute_abundance_annotated)

        return {
            'relative_abundance_table': table_relative_abundance_annotated,
            'relative_abundance_plotly_resource': relative_abundance_plotly_resource,
            'absolute_abundance_table': table_absolute_abundance_annotated,
            'absolute_abundance_plotly_resource': absolute_abundance_plotly_resource
        }

    def stackedbarplot_plotly(self, table: Table) -> PlotlyResource:

        annotated_table: Table = table
        initialdf = annotated_table.get_data()

        # Normalize each row so values sum to 1 (if sum > 0)
        normalized_df = initialdf.copy()
        for idx, row in initialdf.iterrows():
            row_sum = row[row.apply(lambda x: isinstance(x, (int, float)))].sum()
            if row_sum > 0:
                normalized_df.loc[idx] = row.apply(lambda x: x / row_sum if isinstance(x, (int, float)) else x)
            else:
                normalized_df.loc[idx] = row

        fig = go.Figure()

        colors = go.Figure().layout.template.layout.sunburstcolorway or [
            "#636EFA", "#EF553B", "#00CC96", "#AB63FA", "#FFA15A",
            "#19D3F3", "#FF6692", "#B6E880", "#FF97FF", "#FECB52"
        ]
        color_count = len(colors)
        x_tick_labels = normalized_df.index.to_list()

        for i in range(0, normalized_df.shape[1]):
            if isinstance(normalized_df.iat[0, i], str):
                continue
            y = normalized_df.iloc[:, i].values.tolist()
            fig.add_trace(
                go.Bar(
                    x=x_tick_labels, y=y, name=normalized_df.columns[i],
                    marker_color=colors[i % color_count]))

        fig.update_layout(
            barmode='stack',
            xaxis=dict(tickmode='array', tickvals=x_tick_labels, ticktext=x_tick_labels),
            yaxis=dict(range=[0, 1])
        )

        return PlotlyResource(fig)
