#!/bin/bash
# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

# Pre-installation script executed before server installation

apt-get -y update
apt-get -y install jq unzip

CURRENT_FILE_DIR=$(dirname "$0")

pulldata () {
    source_url=$1
    dest_target=$2
    if [[ "$3" == "-d" ]] || [[ "$4" == "-d" ]]; then
        is_dir="1"
    else
        is_dir="0"
    fi

    if [[ "$3" == "-z" ]] || [[ "$4" == "-z" ]]; then
        is_zipped="1"
    else
        is_zipped="0"
    fi

    if [[ $UPDATE_GIT_BRICKS == "1" ]]; then
        if [ ! -d "$dest_target" ]; then
            rm -rf "$dest_target"
        fi
    fi
    
    dest_base_dir=$(dirname "$dest_target")

    if [[ ! -d "$dest_target" ]] && [[ ! -f "$dest_target" ]]; then
        if [ ! -d "$dest_base_dir" ]; then
            mkdir -p $dest_base_dir
        fi
        echo "Pulling ${source_url} ..."
        if [[ "$is_zipped" == "1" ]]; then
            curl "$source_url" -o "${dest_target}.zip"
            
            echo "Decompressing ${dest_target}.zip ..."
            if [[ "$is_dir" == "1" ]]; then
                unzip -q "${dest_target}.zip" -d "${dest_base_dir}"
            else
                unzip -q "${dest_target}.zip" "${dest_target}"
            fi

            rm -f "${dest_target}.zip"
        else
            echo $dest_target 
            curl "$source_url" -o "${dest_target}"
        fi
    fi
}

# Pull large testdata
source_url=`jq '.variables."gws_ubiome:large_testdata_url"' ${CURRENT_FILE_DIR}/../settings.json | sed -e 's/^"//' -e 's/"$//'`
dest_target=`jq '.variables."gws_ubiome:large_testdata_dir"' ${CURRENT_FILE_DIR}/../settings.json | sed -e 's/^"//' -e 's/"$//'`
pulldata "$source_url" "$dest_target" -d -z

# Pull Greengeens Ref data
source_url=`jq '.variables."gws_ubiome:greengenes_ref_url"' ${CURRENT_FILE_DIR}/../settings.json | sed -e 's/^"//' -e 's/"$//'`
dest_target=`jq '.variables."gws_ubiome:greengenes_ref_file"' ${CURRENT_FILE_DIR}/../settings.json | sed -e 's/^"//' -e 's/"$//'`
pulldata "$source_url" "$dest_target"

# Pull Greengeens Classifier
source_url=`jq '.variables."gws_ubiome:greengenes_classifier_url"' ${CURRENT_FILE_DIR}/../settings.json | sed -e 's/^"//' -e 's/"$//'`
dest_target=`jq '.variables."gws_ubiome:greengenes_classifier_file"' ${CURRENT_FILE_DIR}/../settings.json | sed -e 's/^"//' -e 's/"$//'`
pulldata "$source_url" "$dest_target"