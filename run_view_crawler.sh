#!/bin/bash
python view_crawler.py #|& rotatelogs -n 1 ./view_crawler.log 1M
