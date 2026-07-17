#!/bin/bash
BATCH_NAME="$1"
MAX_CONCURRENT="${2:-4}"
shift 2
RESULTS_DIR="/workspace/tc-reverify/runs/${BATCH_NAME}_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$RESULTS_DIR"
echo "Batch: $BATCH_NAME" | tee -a "/workspace/tc-reverify/logs/main.log"

JOBS=()
for arg in "$@"; do
  IFS=':' read -r name script <<< "$arg"
  JOBS+=("$name:$script")
done

PIDS=()
NAMES=()
LOGS=()
for job in "${JOBS[@]}"; do
  IFS=':' read -r name script <<< "$job"
  LOG_FILE="$RESULTS_DIR/${name}.log"
  SCRIPT_DIR=$(dirname "$script")
  SCRIPT_BASE=$(basename "$script")
  (
    cd "$SCRIPT_DIR"
    echo "Starting $name at $(date)" > "$LOG_FILE"
    if [[ "$script" == *.sh ]]; then
      timeout 600 bash "$SCRIPT_BASE" >> "$LOG_FILE" 2>&1
    else
      timeout 600 python3 "$SCRIPT_BASE" >> "$LOG_FILE" 2>&1
    fi
    echo "Exit: $?" >> "$LOG_FILE"
  ) &
  PIDS+=($!)
  NAMES+=("$name")
  LOGS+=("$LOG_FILE")
done

for i in "${!PIDS[@]}"; do
  wait "${PIDS[$i]}"
  echo "[${NAMES[$i]}] done" | tee -a "/workspace/tc-reverify/logs/main.log"
done

echo
echo "=== Summary ===" | tee -a "/workspace/tc-reverify/logs/main.log"
for i in "${!NAMES[@]}"; do
  name="${NAMES[$i]}"
  log="${LOGS[$i]}"
  passed=$(grep -c "✅" "$log" 2>/dev/null)
  failed=$(grep -c "❌" "$log" 2>/dev/null)
  last=$(tail -3 "$log" | head -1)
  echo "  $name: $passed✅ $failed❌ | $last" | tee -a "/workspace/tc-reverify/logs/main.log"
done
