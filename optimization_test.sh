#!/usr/bin/env zsh
echo "Starting test..."

echo "" > result.log

trap "exit" INT TERM
trap "kill 0" EXIT

repeat 100 do (python optimization_individual.py >> result.log) &; sleep 1; done

wait

echo "All finished"
