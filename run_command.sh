#!/usr/bin/env bash
POD=`kubectl get po | grep -v Termin | grep prism-api | cut -d ' ' -f1`
echo $POD
kubectl exec $POD -- bash -c "source activate prism-api && python -m prism_api $1"
