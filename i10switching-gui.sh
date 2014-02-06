#!/bin/bash
# Simple script to run i10 knobs.

PYTHON=dls-python2.7
DIR=$(dirname $(readlink -f $0))

$PYTHON ${DIR}/i10knobs.py
