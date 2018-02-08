#!/bin/bash
#
# Notify of Homebrew updates via Growl on Mac OS X
#
# Author: Chris Streeter http://www.chrisstreeter.com
# Requires: Growl Notify Extra to be installed. Install with
#   brew install growlnotify
#
# Notify of Homebrew updates via Notification Center on Mac OS X
#
# Author: Richard Woeber
# based on the work of Chris Streeter http://www.chrisstreeter.com
#----------------------------------------------------------------------------
# Checks updates at 10am and 10pm. If any, updates.

NAME="homebrew-notifier"
export PATH=/usr/local/bin:/usr/bin:/usr/sbin:/sbin:/bin

BREW=$(which brew)
TERM_NOTIF=$(which terminal-notifier)
NOTIF_ARGS="-sender com.apple.Terminal"

$BREW update 2>&1 > /dev/null
outdated=$($BREW outdated --quiet)

if [ -z "$outdated" ]; then
    if [ -e $TERM_NOTIF ]; then
        # No updates available
        $TERM_NOTIF $NOTIF_ARGS \
        -title "No Homebrew Updates Available" \
        -message "" -timeout 5
    fi
else
    # We've got an outdated formula or more
    # Nofity
    if [ -n "$outdated" ] &&  [ -e $TERM_NOTIF ]; then
        lc=$((`echo "$outdated" | wc -l`))
        updatable=`echo "$outdated" | tail -$lc`
        message=`echo "$outdated" | head -5`
        if [ "$outdated" != "$message" ]; then
            title=$(printf "$lc Homebrew Updates Available")
            message=$(printf "Some of the updatable formulae are:\n$message")
        else
        	  title=$(printf "$lc Homebrew Updates Available")
            message=$(printf "The following formulae are updatable:\n$message")
        fi
        # Send to terminal-notifier
        $TERM_NOTIF $NOTIF_ARGS \
        -title "${title}" \
        -message "${message}" -timeout 5
        # Update - This part is from:
        # http://www.engadget.com/2014/06/11/how-to-keep-homebrew-and-xquartz-updated-automatically/
        ($BREW update  && $BREW upgrade && $BREW doctor) 2>&1 | tee -a "$HOME/Library/Logs/$NAME.log"
        exit 0
    fi
fi
