#!/bin/bash

#virtualenv venv

. venv/bin/activate

#pip install flask
#pip install tweepy

python crawler.py $1 $2
