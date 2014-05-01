#!/bin/bash

if [ "$1" = "setup" ]; then
  virtualenv venv
  . venv/bin/activate
  echo "SETTING UP"
  git clone git://github.com/joshthecoder/tweepy.git
  cd tweepy
  python setup.py install

  python crawler.py $2 $3
else 
  python crawler.py $1 $2
fi
