#!/bin/sh

APP_PATH="/Applications/Vivaldi.app/Contents/Versions/"
VERSION_NAME=`ls ${APP_PATH}`
VIVALDI_PATH="${APP_PATH}${VERSION_NAME}/Vivaldi Framework.framework/Versions/Current/Resources/vivaldi/"

cp -f custom.css "$VIVALDI_PATH/style/custom.css"
cp -f custom.js "$VIVALDI_PATH/custom.js"
cp -f browser.html "$VIVALDI_PATH/browser.html"