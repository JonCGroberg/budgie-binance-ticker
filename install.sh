#!/bin/bash

PLUGIN_DIR="/usr/lib/budgie-desktop/plugins"

# Pre-install checks
if [ $(id -u) = 0 ]
then
    echo "FAIL: Please run this script as your normal user (not using sudo)."
    exit 1
fi

if [ ! -d "$PLUGIN_DIR" ]
then
    echo "FAIL: The Budgie plugin directory does not exist: $PLUGIN_DIR"
    exit 1
fi

function fail() {
    echo "FAIL: Installation failed. Please note any errors above."
    exit 1
}

# Actual installation
echo "Installing budgie-binanceticker to $PLUGIN_DIR"

sudo rm -rf "${PLUGIN_DIR}/binanceticker " || fail
sudo cp -r ./src/binanceticker "${PLUGIN_DIR}/" || fail
sudo chmod -R 644 "${PLUGIN_DIR}/binanceticker/binanceticker.py" || fail

# restart the panel
budgie-panel --replace &

echo "Done. You should be able to add the applet to your panel now."
