#!/bin/zsh
/usr/local/bin/exiftool -overwrite_original -Title="$KMVAR_title" -Author="$KMVAR_authors" -Subject="$KMVAR_subject" -Keywords="$KMVAR_keywords" "$KMVAR_path"
