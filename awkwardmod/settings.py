import os
import datetime
from datetime import timedelta

REDDIT_CLIENT_ID = os.environ['client_id'],
REDDIT_CLIENT_SECRET = os.environ['client_secret'],
REDDIT_USERNAME = os.environ['REDDIT_USERNAME']
REDDIT_PASSWORD = os.environ['REDDIT_PASSWORD'],
BOT_USER_AGENT = os.environ['useragent'],
MERCURY_WEB_PARSER_KEY = os.environ['MERCURY_API_KEY']

ANTI_ANTI_AD_BLOCK_DOMAINS = ['www.google.com', 'www.yahoo.com']
MERCURY_API_URL = 'https://mercury.postlight.com/parser?url={}'
DELAY_BASE_MIN = 1
LAST_PURGED = datetime.now()
PURGE_INTERVAL_MIN = 60
TIME_UNTIL_MESSAGE = 1 * 60
TIME_UNTIL_REMOVE = 10 * 60
H_TIME_UNTIL_REMOVE = str(timedelta(seconds=TIME_UNTIL_REMOVE))

ask_flairs = ['[Askindia]', '[Askindia]', '[Ask]', '[AS]', '[Help]']
spo_flairs = ['[Sports]', '[Sports]', '[SP]']
tec_flairs = ['[Science/Technology]', '[Science Technology]', '[TECH]', '[TE]']
foo_flairs = ['[Food]', '[Food]', '[FO]']
npo_flairs = ['[Casual]', '[Non-Political]', '[NP]']
pol_flairs = ['[Politics]', '[Politics]', '[P]']
red_flairs = ['[[R]eddiquette]', '[Reddiquette]', '[R]']
ALL_FLAIRS = [ask_flairs, spo_flairs, tec_flairs, foo_flairs, npo_flairs,
              pol_flairs, red_flairs]
