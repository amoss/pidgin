#!/usr/bin/env bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

for file in $SCRIPT_DIR/*.pidg; do
  while read line; do
    input=${line%|*}
    output=${line#*| }
    result=$(python3 $SCRIPT_DIR/../bootstrap/interpreter.py -i "$input")
    if [[ "$output" == "$result" ]]; then
      echo "Passed on $input"
    else
      echo "Failed on $input"
      echo "Expected $output"
      echo "Produced $result"
      echo
    fi
  done <$file
done
