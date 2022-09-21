

  #!/usr/bin/bash

# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

#Step 2, qiime2
## paired-end project

qiime_dir=$1
trcF=$2
trcR=$3
threads=$4
trm=$5


qiime dada2 denoise-paired --i-demultiplexed-seqs $qiime_dir/demux.qza --p-trunc-len-f $trcF --p-trunc-len-r $trcR --p-trim-left-f $trm --p-trim-left-r $trm --p-n-threads $threads --o-table table.qza --o-representative-sequences rep-seqs.qza --o-denoising-stats denoising-stats.qza

qiime feature-table summarize --i-table table.qza --o-visualization feature-table.qzv --m-sample-metadata-file $qiime_dir/qiime2_manifest.csv

mkdir sample_freq_details ;
unzip feature-table.qzv -d tmp_dir ;

cat tmp_dir/*/data/sample-frequency-detail.csv | tr ',' '\t' > ./sample_freq_details/sample-frequency-detail.tsv;

unzip denoising-stats.qza -d tmp_dir_2
cat tmp_dir_2/*/data/stats.tsv | grep -v "^#" > ./sample_freq_details/denoising-stats.tsv ;

unzip rep-seqs.qza -d tmp_dir_3
cat tmp_dir_3/*/data/dna-sequences.fasta > ./sample_freq_details/ASV-sequences.fasta ;


mv rep-seqs.qza ./sample_freq_details ;
mv table.qza ./sample_freq_details ;
cp $qiime_dir/demux.qza ./sample_freq_details ;


cp $qiime_dir/qiime2_manifest.csv ./sample_freq_details ;
cp $qiime_dir/gws_metadata.csv  ./sample_freq_details ;
cp $qiime_dir/qiime2_metadata.csv ./sample_freq_details ;
