for f in *.bz2 ;do bzcat < "$f" | pigz -9 -c > "${f%.*}.gz" ;done 
rm *.bz2 ;