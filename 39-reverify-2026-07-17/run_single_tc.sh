#!/bin/bash
# Run a single TC and save results
# Usage: run_single_tc.sh <tc_name> <python_script>
set -e
TC_NAME="$1"
PY_SCRIPT="$2"
RUN_DIR="/workspace/tc-reverify/runs/${TC_NAME}_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$RUN_DIR"
echo "=== $TC_NAME ===" | tee -a "/workspace/tc-reverify/logs/main.log"
echo "Script: $PY_SCRIPT" | tee -a "/workspace/tc-reverify/logs/main.log"
cd "$(dirname "$PY_SCRIPT")"
LOG_FILE="$RUN_DIR/output.log"
START_TIME=$(date +%s)
timeout 300 python3 "$(basename "$PY_SCRIPT")" 2>&1 | tee "$LOG_FILE" | tail -8
END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))
echo "Elapsed: ${ELAPSED}s" | tee -a "/workspace/tc-reverify/logs/main.log"
echo
