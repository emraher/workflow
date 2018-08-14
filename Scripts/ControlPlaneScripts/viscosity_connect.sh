#!/bin/bash
osascript -e 'tell application "Viscosity" to connect "Dedicated"'

osascript <<'END'
tell application "Scroll Reverser"
	set enabled to false
end tell
END