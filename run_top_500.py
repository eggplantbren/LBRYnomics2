#!/bin/bash
python top_500.py |& rotatelogs -n 1 ./top_500.log 1M
