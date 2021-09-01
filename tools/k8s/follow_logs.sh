#!/usr/bin/env bash
POD=`kubectl get po | grep -v Termin | grep prism-api | cut -d ' ' -f1`
echo $POD
kubectl logs $POD -f
