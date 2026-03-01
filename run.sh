#!/bin/bash
# Convenient script to run TranscribeAI from the root directory

# Set project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# Ensure the sub-script is executable
chmod +x scripts/run_local.sh

# Execute the run script
exec ./scripts/run_local.sh
