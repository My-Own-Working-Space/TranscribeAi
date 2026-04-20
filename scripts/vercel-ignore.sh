#!/bin/bash

# ──────────────────────────────────────────────────────────────────────
#  Vercel Ignored Build Step Script
#  Exit Code 0: SKIP the build (Cancel deployment)
#  Exit Code 1: PROCEED with build
# ──────────────────────────────────────────────────────────────────────

echo "Checking if we should build on Vercel..."

# In this project, we want to IGNORE all builds on Vercel because 
# the production app is hosted on Render via Docker.
# This ensures Vercel doesn't waste build minutes or overwrite old versions.

echo "Vercel build ignored. The app is hosted on Render."
exit 0
