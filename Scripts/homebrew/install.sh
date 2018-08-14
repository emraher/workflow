#!/bin/sh

BASE_URL=https://raw.githubusercontent.com/emraher/workflow/master/Scripts/homebrew
NOTIFIER_PATH=/usr/local/bin
BREW_SCRIPT=$NOTIFIER_PATH/homebrew-notifier.sh
CASK_SCRIPT=$NOTIFIER_PATH/cask-notifier.sh
LAUNCHAGENTS_PATH=$HOME/Library/LaunchAgents
BREW_PLIST=$LAUNCHAGENTS_PATH/homebrew-notifier.plist
CASK_PLIST=$LAUNCHAGENTS_PATH/cask-notifier.plist

brew list | grep -q "terminal-notifier" || brew install terminal-notifier
mkdir -p "$NOTIFIER_PATH"
curl -fsS $BASE_URL/homebrew-notifier.sh > "$BREW_SCRIPT"
chmod +x "$BREW_SCRIPT"

mkdir -p "$LAUNCHAGENTS_PATH"
curl -fsS $BASE_URL/homebrew-notifier.plist > "$BREW_PLIST"
chmod +x "$BREW_PLIST" # Not sure if needed.


brew tap | grep -q "emraher/cask-upgrade" || brew tap emraher/cask-upgrade
curl -fsS $BASE_URL/cask-notifier.sh > "$CASK_SCRIPT"
chmod +x "$BREW_SCRIPT"
curl -fsS $BASE_URL/cask-notifier.plist > "$CASK_PLIST"
chmod +x "$CASK_PLIST" # Not sure if needed.

echo
echo "Notifier installed. You'll be notified of brew updates at 10am and 10pm every day."
echo "Checking for updates right now..."
$NOTIFIER_SCRIPT
