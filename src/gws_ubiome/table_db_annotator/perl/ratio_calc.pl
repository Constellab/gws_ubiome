use strict;
use warnings;


my $cpt;
my $cpt2;
my $total;
my %h;
my %hTotal;
my $sample;
my @t;

# row ratio computing

while(<STDIN>){ # use standard input comming from first argument
    chomp;
    $cpt++; 
    if($cpt==1){ 
        print $_,"\n"; # Print the file header (aka first line)
    }
    else{
        @t=split/\t/; # Split the current line
        $total=0;
        $cpt2=0;
        foreach(@t){ # Going through the array containing the current line 
            $cpt2++;
            if($cpt2==1){
                $sample=$_ ; # Store the ID name (aka first position of the current array)
            }
            else{
                $total+=$_; # Compute row total value
                $h{$sample}{$cpt2}=$_; # keep current value (aka current array postion)
            }
        }
        $hTotal{$sample}=$total; # store total row value
    }
}

# Print the ratio foreach line

foreach my$s ( sort keys %h ){
    print $s; # first: row ID
    foreach my$k ( sort {$a <=> $b} keys %{$h{$s}} ){
        print "\t",$h{$s}{$k}/$hTotal{$s}; # then all the ratio values for the current line
    }
    print "\n"; # next line
}

