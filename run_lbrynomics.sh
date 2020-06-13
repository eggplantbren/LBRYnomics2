#!/bin/bash
python main.py |& rotatelogs -n 1 ./lbrynomics.log 1M
