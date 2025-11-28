#!/bin/bash

# The first argument is the timeout duration in seconds
# if it is a number
TIMEOUT_SECONDS="$1"
if ! [[ "$TIMEOUT_SECONDS" =~ ^[0-9]+$ ]]; then
    TIMEOUT_SECONDS=0
else
    shift # Removes the first argument, so $@ now contains the original arguments for twee
fi

# if files are given as arguments, read them and convert them to stdin
# keep other arguments as is
# if [ "$#" -gt 0 ]; then
#     HAS_FILES=0
#     ARGS=()
#     TEMP_FILE=$(mktemp)
#     for ARG in "$@"; do
#         if [ -f "$ARG" ]; then
#             HAS_FILES=1
#             cat "$ARG" >> "$TEMP_FILE"
#             echo "" >> "$TEMP_FILE" # add a newline between files
#         else
#             ARGS+=("$ARG")
#         fi
#     done
#     if [ "$HAS_FILES" -eq 1 ]; then
#         exec bash -c "cat '$TEMP_FILE' | $0 $TIMEOUT_SECONDS ${ARGS[*]}"
#         rm "$TEMP_FILE"
#         exit 0
#     fi
# fi

# start a new neuralcoder/twee container for each run
RUN_CMD="docker run --rm -i neuralcoder/twee:latest"
# RUN_CMD="docker run --rm -i neuralcoder/twee:heuristic"

# Execute 'twee' inside the container, but wrapped with the 'timeout' command.
if [ "$TIMEOUT_SECONDS" -eq 0 ]; then
    # If timeout is 0, run without timeout
    exec time $RUN_CMD twee "$@"
else
    echo "Running with timeout of $TIMEOUT_SECONDS seconds..." 
    OUTER_TIMEOUT_SECONDS=$((TIMEOUT_SECONDS + 1))
    exec time $RUN_CMD timeout "$OUTER_TIMEOUT_SECONDS" twee "$@" --max-time "$TIMEOUT_SECONDS"
fi

# ./twee.sh [1] - < file.p