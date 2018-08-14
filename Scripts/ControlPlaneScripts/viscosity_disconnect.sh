#!/bin/bash
osascript -e 'tell application "Viscosity" to disconnectall'

osascript <<'END'
tell application "Scroll Reverser"
	set enabled to true
end tell
END