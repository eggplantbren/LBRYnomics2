#!/bin/bash
python main.py |& rotatelogs -n 1 ./logfile 1M
