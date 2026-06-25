#!/bin/bash

# Determine directory script resides in
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Ensure logs directory exists
mkdir -p logs/evaluations

# Set the run name with current date
RUN_DATE=$(date +'%Y-%m-%d')
RUN_NAME="Weekly Automated Eval - $RUN_DATE"
LOG_FILE="logs/evaluations/run_${RUN_DATE}.log"

echo "=========================================================="
echo "Starting Weekly RAGAS Evaluation Run..."
echo "Run Name: $RUN_NAME"
echo "Log file: $DIR/$LOG_FILE"
echo "Start Time: $(date)"
echo "=========================================================="

# Run the Django evaluation command using the local virtualenv python
.venv/bin/python manage.py run_eval \
  --name "$RUN_NAME" \
  --score-with-ragas \
  "$@" \
  >> "$LOG_FILE" 2>&1

STATUS=$?

echo "=========================================================="
if [ $STATUS -eq 0 ]; then
  echo "SUCCESS: Weekly evaluation finished successfully."
else
  echo "ERROR: Evaluation command failed with exit code $STATUS."
  echo "Check logs at: $DIR/$LOG_FILE"
fi
echo "End Time: $(date)"
echo "=========================================================="
exit $STATUS
