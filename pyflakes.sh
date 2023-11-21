#!/bin/bash

echo "============================================================"
echo "== pyflakes =="
pyflakes src/julienne tests | grep -v "tests/data"
