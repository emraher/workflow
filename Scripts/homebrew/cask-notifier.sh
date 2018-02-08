#!/bin/bash
#
# Notify of Homebrew Cask updates via Notification Center on Mac OS X
#
# Requires homebrew-cask-upgrade (https://github.com/emraher/homebrew-cask-upgrade)
#
# If not installed run:
#
# brew tap emraher/cask-upgrade
#
#----------------------------------------------------------------------------
# Checks updates at 10:01am and 10:01pm. If any, updates.

NAME="cask-notifier"
export PATH=/usr/local/bin:/usr/bin:/usr/sbin:/sbin:/bin

BREW=$(which brew)
TERM_NOTIF=$(which terminal-notifier)
NOTIF_ARGS="-sender com.apple.Terminal"

outdated=$($BREW cu --list)

if [ -z "$outdated" ]; then
    if [ -e $TERM_NOTIF ]; then
        $TERM_NOTIF $NOTIF_ARGS \
        -title "No Homebrew Cask Upgrades Available" \
        -message ""
    fi
else
    if [ -n "$outdated" ] &&  [ -e $TERM_NOTIF ]; then
        lc=$((`echo "$outdated" | wc -l`))
        message=`echo "$outdated" | head -2`
        title=$(printf "$lc Cask Upgrades Available. Update?")
        message=$(printf "Some of the upgradable casks are:\n$message ...")

        ANSWER="$("$TERM_NOTIF" "$NOTIF_ARGS" -title "${title}" -message "${message}" -closeLabel "No" -actions Yes -json | jq .activationType,.activationValue)"

        stringarray=($ANSWER)
        type=${stringarray[0]}
        value=${stringarray[1]}
                case $type in
                    \"contentsClicked\")
                ;;
                **)
                case $value in
                    \"No\") ANSWER="No"
                ;;
                    \"Yes\") ANSWER="Yes"
                ;;
                **)
                esac
                ;;
                esac

                    if [ "$ANSWER" = "Yes" ]; then
                        $TERM_NOTIF $NOTIF_ARGS -title "Upgrading..." -message "" -timeout 3
                        $BREW cu --no-brew-update --all --yes --quiet --cleanup
                        tee -a "$HOME/Library/Logs/$NAME.log"
                        LOG="$("$TERM_NOTIF" "$NOTIF_ARGS" -title "Upgraded!" -message "Want to see the log file?" -closeLabel "No" -actions Yes -timeout 5 -json | jq .activationType,.activationValue)"
                        stringarray=($LOG)
                        type=${stringarray[0]}
                        value=${stringarray[1]}
                                case $type in
                                    \"contentsClicked\")
                                ;;
                                **)
                                case $value in
                                    \"No\") LOG="No"
                                ;;
                                    \"Yes\") LOG="Yes"
                                ;;
                                **)
                                esac
                                ;;
                                esac
                                    if [ "$LOG" = "Yes" ]; then
                                        sublime "$HOME/Library/Logs/$NAME.log"
                                    fi
                        exit 0
                    else
                        $TERM_NOTIF $NOTIF_ARGS -title "Won't be upgrading." -message "" -timeout 3
                    fi
    fi
fi
