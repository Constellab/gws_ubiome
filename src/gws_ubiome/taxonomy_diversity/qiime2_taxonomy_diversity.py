
import os

from gws_core import (ConfigParams, ConfigSpecs, File, Folder, InputSpec,
                      InputSpecs, IntParam, OutputSpec, OutputSpecs,
                      ResourceSet, ShellProxy, StrParam,
                      Table, TableAnnotatorHelper, TableImporter, Task,
                      TaskFileDownloader, TaskInputs, TaskOutputs,
                      task_decorator)

from gws_core.impl.plotly.plotly_resource import PlotlyResource

from ..base_env.qiime2_env_task import Qiime2ShellProxyHelper
import plotly.graph_objects as go


@task_decorator("Qiime2TaxonomyDiversity", human_name="Q2 Taxonomy Diversity",
                short_description="Computing various diversity index and taxonomy assessement of ASVs")
class Qiime2TaxonomyDiversity(Task):
    """
    Qiime2TaxonomyDiversity class.

    This task classifies reads by taxon using a pre-fitted sklearn-based taxonomy classifier. By default, we suggest a pre-fitted Naive Bayes classifier for the database RDP (in version 18).

    **Minimum required configuration:** Digital lab SC2

    **About RDP:**
    Ribosomal Database Project (RDP; http://rdp.cme.msu.edu/) provides the research community with aligned and annotated rRNA gene sequence data.
    """

    DB_LOCATIONS = {
        'RDP-v18.202208':  "https://storage.gra.cloud.ovh.net/v1/AUTH_a0286631d7b24afba3f3cdebed2992aa/opendata/ubiome/qiime2/RDP_OTUs_classifier.taxa_no_space.v18.202208.qza",
        'Silva-v13.8': "https://storage.gra.cloud.ovh.net/v1/AUTH_a0286631d7b24afba3f3cdebed2992aa/opendata/ubiome/qiime2/silva-138-99-nb-classifier.qza",
        'NCBI-16S_rRNA.20220712': "https://storage.gra.cloud.ovh.net/v1/AUTH_a0286631d7b24afba3f3cdebed2992aa/opendata/ubiome/qiime2/ncbi-refseqs-classifier.16S_rRNA.20220712.qza",
        'GreenGenes-v13.8': "https://storage.gra.cloud.ovh.net/v1/AUTH_a0286631d7b24afba3f3cdebed2992aa/opendata/ubiome/qiime2/gg-13-8-99-nb-classifier.qza"
    }

    DB_DESTINATIONS = {
        'RDP-v18.202208': "RDP_OTUs_classifier.taxa_no_space.v18.202208.qza",
        'Silva-v13.8': "silva-138-99-nb-classifier.qza",
        'NCBI-16S_rRNA.20220712': "ncbi-refseqs-classifier.16S_rRNA.20220712.qza",
        'GreenGenes-v13.8': "gg-13-8-99-nb-classifier.qza"
    }

    DB_RDP_LOCATION = "https://storage.gra.cloud.ovh.net/v1/AUTH_a0286631d7b24afba3f3cdebed2992aa/opendata/ubiome/qiime2/RDP_OTUs_classifier.taxa_no_space.v18.202208.qza"
    DB_RDP_DESTINATION = "RDP_OTUs_classifier.taxa_no_space.v18.202208.qza"

    # Diversity output files
    DIVERSITY_PATHS = {
        "Alpha Diversity - Shannon": "shannon_vector.qza.diversity_metrics.alpha-diversity.tsv",
        "Alpha Diversity - Chao1": "chao1.qza.diversity_metrics.alpha-diversity.tsv",
        "Alpha Diversity - Evenness": "evenness_vector.qza.diversity_metrics.alpha-diversity.tsv",
        "Alpha Diversity - Faith pd": "faith_pd_vector.qza.diversity_metrics.alpha-diversity.tsv",
        "Alpha Diversity - Observed features": "observed_features_vector.qza.diversity_metrics.alpha-diversity.tsv",
        "Alpha Diversity - Simpson": "simpson.qza.diversity_metrics.alpha-diversity.tsv",
        "Alpha Diversity - Inv Simpson": "invSimpson.tab.tsv",
        "Beta Diversity - Bray Curtis": "bray_curtis_distance_matrix.qza.diversity_metrics.distance-matrix.tsv",
        "Beta Diversity - Jaccard distance": "jaccard_distance_matrix.qza.diversity_metrics.distance-matrix.tsv",
        "Beta Diversity - Jaccard unweighted unifrac": "jaccard_unweighted_unifrac_distance_matrix.qza.diversity_metrics.distance-matrix.tsv",
        "Beta Diversity - Weighted unifrac": "weighted_unifrac_distance_matrix.qza.diversity_metrics.distance-matrix.tsv",
        "Beta Diversity - Unweighted unifrac": "unweighted_unifrac_distance_matrix.qza.diversity_metrics.distance-matrix.tsv"
    }

    # Taxo stacked barplot
    TAXO_PATHS = {
        "1_Kingdom": "gg.taxa-bar-plots.qzv.diversity_metrics.level-1.csv.tsv.parsed.tsv",
        "2_Phylum": "gg.taxa-bar-plots.qzv.diversity_metrics.level-2.csv.tsv.parsed.tsv",
        "3_Class": "gg.taxa-bar-plots.qzv.diversity_metrics.level-3.csv.tsv.parsed.tsv",
        "4_Order": "gg.taxa-bar-plots.qzv.diversity_metrics.level-4.csv.tsv.parsed.tsv",
        "5_Family": "gg.taxa-bar-plots.qzv.diversity_metrics.level-5.csv.tsv.parsed.tsv",
        "6_Genus": "gg.taxa-bar-plots.qzv.diversity_metrics.level-6.csv.tsv.parsed.tsv",
        "7_Species": "gg.taxa-bar-plots.qzv.diversity_metrics.level-7.csv.tsv.parsed.tsv",
    }

    FEATURE_TABLES_PATH = {
        "ASV_features_count": "asv_table.csv"
    }
    input_specs: InputSpecs = InputSpecs({
        'rarefaction_analysis_result_folder':
        InputSpec(
            Folder,
            short_description="Feature freq. folder",
            human_name="feature_freq_folder")})
    output_specs: OutputSpecs = OutputSpecs({
        'diversity_tables': OutputSpec(ResourceSet),
        'taxonomy_tables': OutputSpec(ResourceSet),
        'result_folder': OutputSpec(Folder)
    })
    config_specs: ConfigSpecs = ConfigSpecs({
        "rarefaction_plateau_value":
        IntParam(
            min_value=20,
            short_description="Depth of coverage when reaching the plateau of the curve on the previous step"),
        "taxonomic_affiliation_database":
        StrParam(allowed_values=["RDP-v18.202208", "Silva-v13.8", "NCBI-16S_rRNA.20220712", "GreenGenes-v13.8"], default_value="RDP-v18.202208",
                 short_description="Database for taxonomic affiliation"),  # TO DO: add ram related options for "RDP", "Silva", , "NCBI-16S"
        "threads": IntParam(default_value=2, min_value=2, short_description="Number of threads")
    })

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        qiime2_folder: Folder = inputs["rarefaction_analysis_result_folder"]
        plateau_val = params["rarefaction_plateau_value"]
        db_taxo = params["taxonomic_affiliation_database"]
        script_file_dir = os.path.dirname(os.path.realpath(__file__))
        qiime2_folder_path = qiime2_folder.path

        shell_proxy = Qiime2ShellProxyHelper.create_proxy(
            self.message_dispatcher)

        if not db_taxo in self.DB_LOCATIONS or not db_taxo in self.DB_DESTINATIONS:
            raise Exception("Unknown taxonomic affiliation database")

        # create the file_downloader from a task.
        file_downloader = TaskFileDownloader(
            Qiime2TaxonomyDiversity.get_brick_name(),
            self.message_dispatcher)

        # download a file
        file_path = file_downloader.download_file_if_missing(
            self.DB_LOCATIONS[db_taxo], self.DB_DESTINATIONS[db_taxo])
        return self.run_cmd_lines(shell_proxy,
                                  script_file_dir,
                                  qiime2_folder_path,
                                  plateau_val,
                                  file_path,
                                  params
                                  )

    def run_cmd_lines(self, shell_proxy: ShellProxy,
                      script_file_dir: str,
                      qiime2_folder_path: str,
                      plateau_val: int,
                      db_name: str,
                      params: ConfigParams) -> TaskOutputs:

        # This script create Qiime2 core diversity metrics based on clustering
        cmd_1 = [
            "bash",
            os.path.join(script_file_dir,
                         "./sh/1_qiime2_diversity_indexes.sh"),
            qiime2_folder_path,
            plateau_val
        ]
        self.log_info_message("Creating Qiime2 core diversity indexes")
        res = shell_proxy.run(cmd_1)
        if res != 0:
            raise Exception(
                "Core diversity indexes geenration did not finished")
        self.update_progress_value(16, "Done")

        # This script perform Qiime2 taxonomix assignment using pre-trained taxonomic DB

        cmd_2 = [
            "bash",
            os.path.join(script_file_dir,
                         "./sh/2_qiime2_taxonomic_assignment.sh"),
            qiime2_folder_path,
            db_name
        ]
        self.log_info_message(
            "Performing Qiime2 taxonomic assignment with pre-trained model")
        res = shell_proxy.run(cmd_2)
        if res != 0:
            raise Exception("Taxonomic assignment step did not finished")
        self.update_progress_value(32, "Done")

        # This script perform extra diversity assessment via qiime2
        cmd_3 = [
            "bash",
            os.path.join(script_file_dir,
                         "./sh/3_qiime2_extra_diversity_indexes.sh"),
            qiime2_folder_path,
            shell_proxy.working_dir
        ]
        self.log_info_message("Calculating Qiime2 extra diversity indexes")
        res = shell_proxy.run(cmd_3)
        self.update_progress_value(48, "Done")

        # Converting Qiime2 barplot output compatible with constellab front
        cmd_4 = [
            "bash",
            os.path.join(script_file_dir,
                         "./sh/4_barplot_output_formating.sh"),
            qiime2_folder_path,
            os.path.join(script_file_dir,
                         "./perl/4_parse_qiime2_taxa_table.pl"),
            shell_proxy.working_dir
        ]
        self.log_info_message(
            "Converting Qiime2 taxonomic barplot for visualisation")
        res = shell_proxy.run(cmd_4)
        if res != 0:
            raise Exception("Barplot convertion did not finished")
        self.update_progress_value(68, "Done")

        # Getting Qiime2 ASV output files
        cmd_5 = [
            "bash",
            os.path.join(script_file_dir,
                         "./sh/5_qiime2_ASV_output_files_generation.sh"),
            shell_proxy.working_dir
        ]
        self.log_info_message("Qiime2 ASV output file generation")
        res = shell_proxy.run(cmd_5)
        if res != 0:
            raise Exception("ASV output file generation did not finished")
        self.update_progress_value(84, "Done")

        # Saving output files in the final output result folder Folder
        cmd_6 = [
            "bash",
            os.path.join(script_file_dir,
                         "./sh/6_qiime2_save_extra_output_files.sh"),
            qiime2_folder_path,
            shell_proxy.working_dir
        ]
        self.log_info_message("Moving files in the output directory")
        res = shell_proxy.run(cmd_6)
        if res != 0:
            raise Exception("Moving files did not finished")
        self.update_progress_value(100, "Done")

        # Output object creation and Table annotation

        result_folder = Folder(os.path.join(
            shell_proxy.working_dir, "taxonomy_and_diversity"))

        #  Importing Metadata table
        path = os.path.join(result_folder.path,
                            "raw_files", "gws_metadata.csv")
        metadata_table: Table = TableImporter.call(
            File(path=path), {'delimiter': 'tab'})

        # Create ressource set containing diversity tables
        diversity_resource_table_set: ResourceSet = ResourceSet()
        diversity_resource_table_set.name = "Set of diversity tables (alpha and beta diversity) compute from features count table (ASVs or OTUs)"

        # Parcourir les éléments de DIVERSITY_PATHS
        for key, value in self.DIVERSITY_PATHS.items():
            path = os.path.join(shell_proxy.working_dir,
                                "taxonomy_and_diversity", "table_files", value)

            # Si la clé est égale à "Alpha Diversity - Faith pd", ajustez le traitement de la colonne Faith PD
            if key == "Alpha Diversity - Faith pd":
                # Lisez le contenu du fichier pour déterminer sa structure
                with open(path, 'r') as file:
                    first_line = file.readline().strip()  # Lire la première ligne du fichier
                    # Si la première ligne commence par '#SampleID', la structure est différente
                    if first_line.startswith('#SampleID'):
                        table: Table = TableImporter.call(
                            File(path=path),
                            {'delimiter': 'tab', "index_column": 0, 'header': -1, 'comment': '#'})
                        raw_table_columns = ["faith_pd"]
                        table.set_all_column_names(raw_table_columns)
                    else:
                        table: Table = TableImporter.call(
                            File(path=path), {'delimiter': 'tab', "index_column": 0})
            else:
                table: Table = TableImporter.call(
                    File(path=path), {'delimiter': 'tab', "index_column": 0})

            table_annotated = TableAnnotatorHelper.annotate_rows(
                table, metadata_table, use_table_row_names_as_ref=True)
            table_annotated.name = key

            # Ajouter le tableau à la ressource set
            diversity_resource_table_set.add_resource(table_annotated)

        # Create ressource set containing Taxonomy table with a forced customed view (TaxonomyTable; stacked barplot view)

        taxo_resource_table_set: ResourceSet = ResourceSet()
        taxo_resource_table_set.name = "Set of taxonomic tables (7 levels)"
        for key, value in self.TAXO_PATHS.items():
            path = os.path.join(shell_proxy.working_dir,
                                "taxonomy_and_diversity", "table_files", value)
            table = TableImporter.call(
                File(path=path), {'delimiter': 'tab', "index_column": 0})
            table_annotated = TableAnnotatorHelper.annotate_rows(
                table, metadata_table, use_table_row_names_as_ref=True)
            table_annotated.name = key
            table_annotated_bar_plot = self.plotly_bar_plot(table_annotated)
            table_annotated_bar_plot.name = key + "_stacked_barplot"

            taxo_resource_table_set.add_resource(table_annotated)
            taxo_resource_table_set.add_resource(table_annotated_bar_plot)

        for key, value in self.FEATURE_TABLES_PATH.items():
            #  Importing Metadata table
            path = os.path.join(result_folder.path,
                                "raw_files", "asv_dict.csv")
            asv_metadata_table: Table = TableImporter.call(
                File(path=path), {'delimiter': 'tab'})

            asv_table_path = os.path.join(
                result_folder.path, "table_files", value)
            asv_table = TableImporter.call(File(path=asv_table_path), {
                'delimiter': 'tab', "index_column": 0})
            t_asv = asv_table.transpose()
            table_annotated = TableAnnotatorHelper.annotate_rows(
                t_asv, metadata_table, use_table_row_names_as_ref=True)
            table_annotated = TableAnnotatorHelper.annotate_columns(
                t_asv, asv_metadata_table, use_table_column_names_as_ref=True)
            table_annotated.name = key
            taxo_resource_table_set.add_resource(table_annotated)

        return {
            'result_folder': result_folder,
            'diversity_tables': diversity_resource_table_set,
            'taxonomy_tables': taxo_resource_table_set
        }

    def plotly_bar_plot(self, table: Table) -> PlotlyResource:
        """
        Create a plotly stacked bar plot from a table, normalizing y to [0, 1].
        :param table: The table to plot
        :return: A PlotlyResource containing the bar plot
        """
        table_data = table.transpose().get_data()
        tdata = table_data.T

        fig = go.Figure()

        colors = go.Figure().layout.template.layout.sunburstcolorway or [
            "#636EFA", "#EF553B", "#00CC96", "#AB63FA", "#FFA15A",
            "#19D3F3", "#FF6692", "#B6E880", "#FF97FF", "#FECB52"
        ]
        color_count = len(colors)
        x_tick_labels = tdata.index.to_list()

        # Normalize each column so that the sum for each sample (row) is 1
        norm_tdata = tdata.div(tdata.sum(axis=1), axis=0).fillna(0)

        for i in range(0, norm_tdata.shape[1]):
            if isinstance(norm_tdata.iat[0, i], str):
                continue
            y = norm_tdata.iloc[:, i].values.tolist()
            color = colors[i % color_count]
            fig.add_trace(go.Bar(
                x=x_tick_labels,
                y=y,
                name=norm_tdata.columns[i],
                marker_color=color,
                hovertemplate=f'{norm_tdata.columns[i]} : %{{y}}<extra></extra>'
            ))

        fig.update_layout(
            barmode='stack',
            xaxis_title="Samples",
            yaxis_title="Feature count",
            xaxis=dict(
                tickmode='array',
                tickvals=x_tick_labels,
                ticktext=x_tick_labels,
                title=dict(
                    text="Samples",
                    standoff=20  # Add margin above x-axis title
                )
            ),
            yaxis=dict(range=[0, 1])
        )
        return PlotlyResource(fig)
