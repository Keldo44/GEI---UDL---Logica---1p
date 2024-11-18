#!/usr/bin/env bash

input_dir="$1"

if [ -z "$input_dir" ]; then
    echo "Error: No instances directory provided."
    echo "Usage: $0 <instances-directory>"
    exit 1
fi

# Check if the argument is a valid directory
if [ ! -d "$input_dir" ]; then
    echo "Error: '$input_dir' is not a valid directory."
    exit 2
fi

TIME_LIMIT_S=100
MEM_LIMIT_GB=20
SCRIPT="ship_find.py"

CHECKS=(
    "Check fixed cells"
    "Check no ships touch each other"
    "Check all ships are placed somewhere"
    "Check no ships overlap"
    "Check row constraints"
    "Check column constraints"
)

declare -A err_counters
for check in "${CHECKS[@]}"; do
    err_counters["$check"]=0
done
err_counters["unsolved"]=0
num_ok=0

mapfile -t sf_files < <(find "$input_dir" -type f -name "*.sf")

echo "Executing ${#sf_files[@]} instances..."

for file in "${sf_files[@]}"; do
    output=$(ulimit -m $((MEM_LIMIT_GB * 1024 * 1024)); \
        timeout ${TIME_LIMIT_S} python3 "${SCRIPT}" \
            "${file}" --verify --visualization quiet)
    # Check if the instance has been solved
    if [[ ! "${output}" =~ "Has solution? True" ]]; then
        echo "- No solution found in ${file}"
        ((err_counters["unsolved"]++))
        continue
    fi
    is_valid=0
    for check in "${CHECKS[@]}"; do
        if [[ "${output}" =~ "${check}: ERROR" ]]; then
            echo "- ${file} failed check ${check}"
            ((err_counters["${check}"]++))
            is_valid=1
        fi
    done
    if [[ $is_valid -eq 0 ]]; then
        ((num_ok++))
    fi
done

echo ""
echo "SUMMARY"
echo "======="
echo "Tested ${#sf_files[@]} instances"
echo "Num OK: ${num_ok}"
echo "Num unsolved: ${err_counters[unsolved]}"

for check in "${CHECKS[@]}"; do
	count="${err_counters[$check]}"
	echo "${check} -> ${count} instances with errors"
done

