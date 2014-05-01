from flask import Flask, request, jsonify
import flask 
import tweepy
import urllib
import sys
import time
import os
import json
import httplib
app = Flask(__name__)

# The following variables are related to connecting to oAuth
CONSUMER_TOKEN = 'mfrKQGGLFKVrNpcEQFcyRxipb'
CONSUMER_SECRET = '7uxrXOX9Kr4VKameUMUsoGnBWnCxGV5Mw8InH84YpX3puVkVoY'
CALLBACK_URL = 'http://127.0.0.1:5000/verify'
session = dict()
db = dict()
tweets_data = []

# Check if user wants a specific number of tweets, else set NUM_TWEETS to a default val
if len(sys.argv) > 1:
  NUM_TWEETS = int(sys.argv[1])
else:
  NUM_TWEETS = 10
if len(sys.argv) > 2:
  DIR_NAME = str(sys.argv[2])
else:
  DIR_NAME = "tweet_data"

# Create a Stream Listener to catch Tweets from twitter
class CustomStreamListener(tweepy.StreamListener):
  def __init__(self, api=None):
    super(CustomStreamListener, self).__init__()
    # Create counter to keep track of num tweets seen
    self.num_tweets = 0
  def on_status(self, status):
    # Store relevant info about tweet, increment counter, and break if counter exceeds NUM_TWEETs
    tweet = {
      'profile_image' : status.author.profile_image_url_https,
      'text' : status.text,
      'screen_name' : status.author.screen_name,
      'date' : str(status.created_at),
      'urls' : status.author.url,
      'geo' : status.coordinates}

    self.num_tweets = self.num_tweets + 1
    tweets_data.append(tweet)
    if self.num_tweets < NUM_TWEETS:
      return True
    else:
      return False

def has_url():
  # parse the text of each tweet to see if it contains a URL
  for t in range(NUM_TWEETS) :
    if ("http" in tweets_data[t]['text']):
      text = tweets_data[t]['text']
      url = text[text.find("http"):]
      possible_urls = url.split(" ")
      valid_urls =[]
      for u in range(len(possible_urls)) :
        if ("http" in possible_urls[u]) :
          valid_urls.append(possible_urls[u])
      tweets_data[t]['urls'] = valid_urls

def get_titles():
  # iterate through tweets, if they have urls, download the page then search the page
  # for a title and save the title to the tweet data
  for t in range(NUM_TWEETS) :
    urls = tweets_data[t]['urls']
    titles = []
    if urls != None:
      for u in range(len(urls)):
        try:
          encoded = urls[0].decode("utf-8") #Twitter gives links in unicode 
          webpage = urllib.urlopen(encoded)
          contents = webpage.read()
          if "<title>" in contents:
            titles.append(contents[contents.find("<title>"):contents.find("</title>")][7:])
        # some links collected may be invalid and will cause errors
        # these pages should not be downloaded
        except UnicodeEncodeError:
          pass
        except UnicodeDecodeError:
          pass
        except IOError:
          pass
        except httplib.InvalidURL:
          pass
        tweets_data[t]['titles'] = titles

@app.route("/")
def send_token():
  auth = tweepy.OAuthHandler(CONSUMER_TOKEN, CONSUMER_SECRET, CALLBACK_URL)
  try: 
    # get the request tokens
    redirect_url= auth.get_authorization_url()
    session['request_token']= (auth.request_token.key,
    auth.request_token.secret)
  except tweepy.TweepError:
    print 'Error! Failed to get request token'
  return flask.redirect(redirect_url)

@app.route("/verify")
def get_verification():
  # get the verifier key from the request url
  verifier= request.args['oauth_verifier']

  auth = tweepy.OAuthHandler(CONSUMER_TOKEN, CONSUMER_SECRET)
  token = session['request_token']
  del session['request_token']

  auth.set_request_token(token[0], token[1])

  try:
    auth.get_access_token(verifier)
  except tweepy.TweepError:
    print 'Error! Failed to get access token.'

  # Use Tweepy to access Twitter
  api = tweepy.API(auth)
  streaming_api = tweepy.streaming.Stream(auth,  CustomStreamListener())

  # store in a db
  db['streaming_api']=streaming_api
  db['access_token_key']=auth.access_token.key
  db['access_token_secret']=auth.access_token.secret
  return flask.redirect(flask.url_for('start'))

@app.route("/start")
def start():
  # auth done, app logic can begin
  streaming_api = db['streaming_api']
  start_time = time.time()
  print "Getting Tweets"
  streaming_api.filter(track=['com'])
  print "took ", time.time() - start_time, "s"
  start_time = time.time()
  print "Getting urls"
  has_url()
  print "took ", time.time() - start_time, "s"
  start_time = time.time()
  print "Crawling for titles"
  get_titles()
  print "took", time.time() - start_time, "s"
  start_time = time.time()
  print "JSONify and write to files"
  if not os.path.exists(DIR_NAME):
    os.makedirs(DIR_NAME)
  tweets_in_file = 0
  num_files = 0
  save_path = DIR_NAME + '/'
  name_of_file = 'tweets_'
  wave_of_tweets = ""
  tweets_file = None
  for i in range (len(tweets_data)):
    try:
      wave_of_tweets += json.dumps(tweets_data[i])
    except UnicodeDecodeError:
      pass
    tweets_in_file += 1
    if (tweets_in_file % 12000 == 0):
      num_files += 1
      complete_name = os.path.join(save_path + name_of_file + str(num_files) + ".txt")
      tweets_file = open(complete_name, 'w')
      tweets_file.write(wave_of_tweets)
      tweets_file.close()
      tweets_in_file = 0
      wave_of_tweets = ""
  if tweets_in_file != 0:
    num_files += 1
    complete_name = os.path.join(save_path + name_of_file + str(num_files) + ".txt")
    tweets_file = open(complete_name, 'w')
    tweets_file.write(wave_of_tweets)
    tweets_file.close()
    tweets_in_file = 0
    wave_of_tweets = ""

  print "took ", time.time() - start_time, "s"

  return "Thank you"

if __name__ == "__main__":
  app.run(debug=True)
