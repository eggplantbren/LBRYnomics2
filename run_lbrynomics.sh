#!/bin/bash
python main.py |& rotatelogs -n 1 ./main.log 1M &
sleep 10
python top_500.py |& rotatelogs -n 1 ./top_500.log 1M &
sleep 10
python view_crawler.py |& rotatelogs -n 1 ./view_crawler.log 1M &

