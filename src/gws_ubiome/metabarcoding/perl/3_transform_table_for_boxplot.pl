#!/usr/bin/perl

# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

use strict;
use warnings;

# Converting Step 2 output table (*.csv) into a boxplot compatible format

# Original format (input; STDIN) :
#sample-id	depth-10_iter-1	depth-10_iter-2	depth-10_iter-3	...	depth-5000_iter-10	forward-absolute-filepath	reverse-absolute-filepath
#sample_1	3.121928094887363	2.646439344671016	2.9219280948873627	...	5.962283309285255	sample-1_R1_clipped.fastq.gz	sample-1_R2_clipped.fastq.gz
#sample_2	2.9219280948873627	2.6464393446710157	2.6464393446710157	...	5.445730475833346	sample-2_R1_clipped.fastq.gz	sample-2_R2_clipped.fastq.gz
#sample_3	3.321928094887362	3.321928094887362	3.321928094887362	...	6.438190610932343	sample-3_R1_clipped.fastq.gz	sample-3_R2_clipped.fastq.gz


# Transformed table for boxplot (output; STDOUT)
#	10##sample_1	10##sample_2	10##sample_3	...	5000##sample_3
#iter-1	3.121928094887363	2.9219280948873627	3.321928094887362	...	6.436784616613838
#iter-2	2.646439344671016	2.6464393446710157	3.321928094887362	...	6.438190610932343
#iter-3	2.9219280948873627	2.6464393446710157	3.321928094887362	...	6.419673785749065
#										...	
#iter-10	3.121928094887363	3.121928094887363	3.321928094887362	...	6.407408520627716



my@t;
my$cpt=0;
my$col=0;
my$sampleId='';
my%hMatrix;
my%hHeader;
my%hSampleOrder;

while(<STDIN>){
	chomp;
	$cpt++;
	@t=split/,/;
	if($cpt==1){
		$col=0;
		foreach(@t){
			$col++;
			if($col==1){
				next;
			}
			elsif($_=~/.*absolute-filepath.*/){
				next;
			}
			else{
#				my@tDepthId=split("_", $_);
				$hHeader{$col}=$_;
			}
		}
	}
	else{
		$col++;
		my$col2=0;
		foreach(@t){
			$col2++;
			if($col2==1){
				$sampleId=$_;
			}
			elsif($_=~/.*\.gz$/){
				next;
			}
			else{
				my@tDepthId=split("_", $hHeader{$col2});
				my@tDepthNb=split("-",$tDepthId[0]);
				$hSampleOrder{$tDepthNb[1]}{$sampleId}++;
				$hMatrix{$tDepthId[1]}{$tDepthNb[1]}{$sampleId}=$_;
			}
		}
	}
}

# printing header (-> STDOUT)

foreach my$depId ( sort {$a <=> $b} keys %hSampleOrder ){
	foreach my$sampId ( sort keys %{ $hSampleOrder{$depId} } ){
#		print "\t",$depId,'##',$sampId;
		print "\t{\"x-axis\": " , $depId , " , \"sample-id\": \"" , $sampId , "\"}";
	}
}
print "\n";

# printing values (ten iteration = ten lines) (-> STDOUT)

foreach my$iteration ( sort keys %hMatrix ){
	print $iteration;
	foreach my$depth  ( sort {$a <=> $b} keys %{ $hMatrix{$iteration} } ){
			foreach my$sample  ( sort keys %{ $hMatrix{$iteration}{$depth} } ){
				print "\t",$hMatrix{$iteration}{$depth}{$sample};
			}
		}
	print "\n";
}
