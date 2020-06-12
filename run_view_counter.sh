#!/bin/bash
python view_counter.py |& rotatelogs -n 1 ./view_counter.log 1M
