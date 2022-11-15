use strict;
use warnings;

# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


# Inputs
my$annotationDb=$ARGV[0];
my$rawTableToAnnotate=$ARGV[1];
my$sequenceDb=$ARGV[2];

my%hAnnotationTable;
my$tagId;

# create annotationDb dictionnary

# db tabulated file format (1 header begining with "#" + two columns):
#	#tax_id	info
#	genus_1	0
#	genus_2	1
#	genus_3	Variable;species_A:0;others:1

open(Db,"$annotationDb");

while(<Db>){
	chomp;
	my@tax=split/\t/;
	# get information for variable information
	if($tax[1]=~/.*Variable;([^\s]+)/){
		$hAnnotationTable{$tax[0]}="_".$1;
	}
	# get tag name
	elsif($_=~/^#[^\t]+\t([^\t])/){
		$tagId=$1;
	}
	else{
		if($tax[1]=~/^([^\s]+)/){
			$hAnnotationTable{$tax[0]}="_".$1;
		}
	}
}

close(Db);

# printing rawTableToAnnotate annotated with annotationDb dictionnary

open(File,"$rawTableToAnnotate");


while(<File>){
	chomp;
	my@tax=split/\t/;
	#specifying use DB for sequence taxa affiliation and printing results 
	if($sequenceDb eq "GreenGenes"){
		if($_=~/^index\t.*/){
			my@li=split/\t/;
			my$header="";
			foreach(@li){
				chomp;
				# getting the taxa name from the qiime2 output table and requesting the annotationDb dictionnary
				if($_=~/^[^_]{1}\_\_([^;]+)$/){
					if($hAnnotationTable{$1}){
						$header.="\t".$1."#tag:".$hAnnotationTable{$1};
					}
					else{
						$header.="\t".$1."#tag:_nan";
					}
				}
				elsif($_=~/^[^_]{1}\_\_$/){
					$header.="\t".$_."#tag:_nan";
				}
				elsif($_=~/^\_\_$/){
					$header.="\t".$_."#tag:_nan";
				}
				elsif($_=~/^index$/){
					$header.=$_;
				}
				else{
					$header.="\t".$_."#tag:_nan";   # Unorthodox greengenes taxa ids are taken into account
				}
			}
			print $header."\n";
		}
		# TO BE DONE: Adding other db taxa comparison --> elsif(FOR OTHERS DB, e.g Silva, rdp...){}
		else{
			print $_,"\n";
		}
	}
}

close(File);

