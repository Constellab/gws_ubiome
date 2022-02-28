#!/usr/bin/perl

# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
use strict;
use warnings;

# convert file header to only keep last taxa level in qiime2 taxa indexation (step 4; greengenes nomenclature) 
#ex:
# index	k__Bacteria;p__OD1;c__;o__;f__;g__;s__	k__Bacteria;p__Bacteroidetes;c__Bacteroidia;o__Bacteroidales;f__Bacteroidaceae;g__Bacteroides;s__uniformis
# -->
# index	p__OD1	s__uniformis


my$line=0;
my$kept_name="";

open(File,"$ARGV[0]");

while(<File>){
	chomp;
	my@t=split/\t/;
	$line++;
	if($line==1){
		my$col=0;
		print "#complete-taxa-",$_,"\n";
		foreach(@t){
			$col++;
			if($col==1){
				print $_;
			}
			else{
				$kept_name="";
				my@t_all_tax=split(";", $_);
				#print $t_all_tax[4],"\n";
				foreach(@t_all_tax){
					if($_=~/^.*__.*$/){
						#print $_,"\n";
						my@t_level_taxo=split("__", $_);
							if($t_level_taxo[1]){
								#print $t_level_taxo[1],"\n";
								$kept_name=$_;
							}
							else{
								next;
							}
					} 
					elsif($_=~/^forward-.*$/ or $_=~/^reverse-.*$/){
						$kept_name=$_;
					}
					else{
						next;
					}
				}
			print "\t",$kept_name ;
			}
		}
		print "\n";
	}
	else{
		print $_,"\n";
	}
}

close(File);