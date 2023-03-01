fq_folder=$1
threads=$2
last_chocoplan_db_dir=$3
last_chocoplan_db_name=$4

cd $fq_folder;

for i in *.gz ;do echo "Mapping "$i ; metaphlan $i --bowtie2db $last_chocoplan_db_dir -x $last_chocoplan_db_name --bowtie2out $i.metagenome.bowtie2.bz2 --nproc $threads --input_type fastq --unknown_estimation -o ../metaphlan_output.$i.txt ; echo "DONE: Mapping "$i ;done

cd ..

echo "start merging abundance"

merge_metaphlan_tables.py metaphlan_output.*.txt > merged_abundance_table.$last_chocoplan_db_name.txt

echo "##### DONE ######"

#################
# Before use
#################

# Get Chocophlan db and make the bowtie index

# https://github.com/biobakery/MetaPhlAn/wiki/MetaPhlAn-3.0 <- db link
#echo "install metaphlan index"
#conda create -n metaPH
#conda activate metaPH
#conda install -c bioconda metaphlan

##create bowtie index, because depo. don't work
# nohup bowtie2-build --threads 2 --offrate 1 mpa_v30_CHOCOPhlAn_201901.fna mpa_v30_CHOCOPhlAn_201901 &
#tar -zcvf chocophlan_mpa_v30_201901.tar.gz mpa_v30_CHOCOPhlAn_201901/

#echo "DONE: install metaphlan index"
#Starting from version 3, MetaPhlAn can estimate the fraction of the metagenome composed by unknown microbes. 
#The relative abundance profile is scaled according to the percentage of reads mapping to a known clade.


