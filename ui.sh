#!/bin/sh
# Avvia la UI di Brandes con il Python di Homebrew (Tk >= 8.6).
# Il python3 di sistema usa Tk 8.5, che su macOS non gestisce bene i click.
cd "$(dirname "$0")"
exec /opt/homebrew/bin/python3.14 gui/brandes_ui.py "$@"
