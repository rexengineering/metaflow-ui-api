#!/usr/bin/env zsh
echo "Starting test..."

echo "" > result.log

trap "exit" INT TERM
trap "kill 0" EXIT

repeat $1 do (INTEGRATION_TESTS=1 pytest -m 'integration' -q --tb=short >> result.log) &; sleep 1; done

wait

echo "All finished"
