import os
import re
import sys
import time
from datetime import datetime
from datetime import timedelta
from collections import OrderedDict

import praw
import mechanicalsoup
import requests
import html2text
from readability import Document
from newspaper import Article
from unidecode import unidecode

import Antiblockdomains
import tweepy



# Export your reddit mod username and password as REDDIT_USERNAME and
# REDDIT_PASSWORD as environment variables respectively.
# Run as follows: python3 awkwardmod.py

# adding for testing something

mercury_web_parser_key = os.environ['MERCURY_API_KEY']
mercury_api_url = 'https://mercury.postlight.com/parser?url={}'


# Twitter API Authenticatin using Oauth

auth = tweepy.OAuthHandler(os.environ['twitter_consumer_key'], os.environ['twitter_consumer_key_secret'])
auth.set_access_token(os.environ['twitter_access_token'], os.environ['twitter_access_token_secret'])
api = tweepy.API(auth)


# BEGIN TITLE VARS
delay_base_min = 1
ignored = []
not_flaied = []
flairchecked = []
last_purged = datetime.now()
purge_interval_min = 60
TwitterKeyword='awkmodtweetthis'
# END TITLE VARS

# BEGIN AUTO-FLAIR VARS
ask_flairs = ['[Askindia]', '[Askindia]', '[Ask]', '[AS]', '[Help]']
spo_flairs = ['[Sports]', '[Sports]', '[SP]']
tec_flairs = ['[Science/Technology]', '[Science Technology]', '[TECH]', '[TE]']
foo_flairs = ['[Food]', '[Food]', '[FO]']
npo_flairs = ['[Casual]', '[Non-Political]', '[NP]']
pol_flairs = ['[Politics]', '[Politics]', '[P]']
red_flairs = ['[[R]eddiquette]', '[Reddiquette]', '[R]']
all_flairs = [ask_flairs, spo_flairs, tec_flairs, foo_flairs, npo_flairs,
              pol_flairs, red_flairs]
# END AUTO-FLAIR VARS

# BEGIN FLAIR VARS
time_until_message = 1 * 60
time_until_remove = 10 * 60
h_time_until_remove = str(timedelta(seconds=time_until_remove))
max_retries = 3
no_flair = OrderedDict()
anti_anti_ad_block_domains = Antiblockdomains.anti_anti_ad_block_domains
# END FLAIR VARS

'''--------------Messages-------------------'''
footer_message = ("\n\n>**What is a Flair?**\n\n>A flair basically categorizes"
                  " your post in one of the pre-existing categories on "
                  "/r/india. Once you make a submission, you'll notice a red "
                  "button which says *Flair your post* . Click on it and "
                  "choose a flair according to the submission's theme, then "
                  "hit Save.\n\n>* If you want a civil and focused discussion "
                  "with NO off-topic comments, choose \"[R]ediquette\". We do "
                  "not allow trolling and other unnecessary behaviour in [R] "
                  "threads.\n* If you are posting from a handheld device, "
                  "append [NP] for non-political, [P] for political and [R] to"
                  " the title of the post and our bot will flair it "
                  "accordingly.\n* **Example**: "
                  "http://i.imgur.com/FKs9uVI.png\n\n---\n\n"
                  "^(I am just a bot and cannot reply to your queries. Send a)"
                  " [^*modmail*](http://www.reddit.com/message/compose?"
                  "to=%2Fr%2Findia&subject=Flair+Bot) ^(if you have any "
                  "doubts.)")

add_flair_message = ("Your post does not have any flair and will soon be "
                     "removed if it remains so.\n\nPlease add flair to your "
                     "post. If you do not add flair within **{}**, you will "
                     "have to resubmit your post. ".format(
                         h_time_until_remove, footer_message))

remove_post_message = ("Your post does not have any flair after the allotted "
                       "{} and has therefore been removed. Feel free to "
                       "resubmit it and remember to flair it once it is "
                       "posted.".format(h_time_until_remove, footer_message))

anti_anti_ad_block_header = ("^This ^article ^is ^adblocker ^unfriendly, "
                             "^following ^is ^the ^text ^of ^the ^article. "
                             "\n\n ______ ")

anti_anti_ad_block_footer = ("\n\n ______ \n ^I ^am ^just ^a ^bot, ^I ^cannot "
                             "^reply ^to ^your ^queries. ^Send ^a "
                             "^[*modmail*](http://www.reddit.com/message/"
                             "compose?to=%2Fr%2Findia&subject=Anti+Anti+Ad+"
                             "Block+Bot) ^if ^you ^have ^any ^queries. ^Please"
                             " ^provide ^a ^link ^to ^your ^submission. ^We "
                             "^would ^not ^be ^able ^to ^help ^you ^without "
                             "^a ^link.")


'''-----------------Messages Over------------'''


def get_browser():
    br = mechanicalsoup.Browser()
    return br


def ndtv_anti_ad_block_text(article):
    doc = Document(article.html)
    text_maker = html2text.HTML2Text()
    text_maker.ignore_links = True
    text_maker.ignore_images = True
    return text_maker.handle(doc.summary())


def get_anti_ad_block_text(article, article_data, for_ndtv):
    article_title = "\n**{article_data['title']}** \n\n ______ "
    response = "{header}{title}\n{body}{footer}"
    if for_ndtv:
        article_body = ndtv_anti_ad_block_text(article)
    else:
        article_body = article.text
    return response.format(
        header=anti_anti_ad_block_header, title=article_title,
        body=article_body, footer=anti_anti_ad_block_footer)


def anti_anti_ad_block(article_data, post):
    try:
        domain = article_data['domain']
        if domain in anti_anti_ad_block_domains:
            article = Article(post.url)
            article.download()
            article.parse()

            if domain in ('www.ndtv.com', 'www.newslaundry.com'):
                anti_ad_block_text = get_anti_ad_block_text(
                    article=article, article_data=article_data, for_ndtv=True)
                post.reply(anti_ad_block_text)
                print("Posted Anti Ad Block Comment for {0.shortlink} of "
                      "{0.author}".format(post))
            else:
                anti_ad_block_text = get_anti_ad_block_text(
                    article=article, article_data=article_data, for_ndtv=True)
                if len(anti_ad_block_text) < 10000:
                    et_times = "Get instant notifications from Economic Times"
                    if et_times not in anti_ad_block_text:
                        post.reply(anti_ad_block_text)
                        print("Posted Anti Ad Block Comment for {0.shortlink}"
                              " of {0.author}".format(post))
                    else:
                        print("Not Posting Anti Ad Block Comment for "
                              "{0.shortlink} of {0.author} as economic times "
                              "has derped".format(post))
                else:
                    print("Could not post Anti Ad Block Comment for "
                          "{0.shortlink} of {0.author} because of comment"
                          "length".format(post))
    except Exception as e:
        print("Error from Mercuty on {0.shortlink} of {0.author}".format(post))
        ignored.append(post.id)
        pass


def get_article_data(post):
    try:
        request_header = {'content-type': 'application/json',
                          'x-api-key': mercury_web_parser_key}
        r = requests.get(mercury_api_url.format(post.url),
                         headers=request_header)
        if r.status_code == requests.codes.ok:
            article_data = r.json()
            # print(article_data) Uncommet this to check mercury 404
            return article_data
        else:
            print("Mercury Web Parser Failed for {0.shortlink} of "
                  "{0.author} ".format(post))
            print("Status Code", r.status_code)
            ignored.append(post.id)
    except Exception as e:
        print('Could not fetch data for the article {}'.format(
            sys.exc_info()[-1].tb_lineno), type(e), e)
        print("RESET", "due to", e)
        ignored.append(post.id)


def original_title_check(post, article_data):
    # Below websites titles are usually different than actual title
    ignore_title_check_domains = ['newslaundry.com', 'ETtech.com']
    # No point in checking title with twitter
    ignore_twitter = ['twitter.com']

    try:
        article_title = article_data['title']
        content_check = 'content' in article_data

        # Ignore Twitter links and non English articles for automated checks
        # due to English Title rules
        if content_check and (
            article_data['domain'] not in ignore_title_check_domains) and (
                article_data['domain'] not in ignore_twitter):
            # Article title will always be a subset of Reddit Post Title. This
            # is to take care of mobile flairs like [P], [NP] etc.
            # Striping [],apostrophe from title and article title while
            # original title check
            post.title = re.sub('[\[\]\']', '', post.title)
            article_title = re.sub('[\[\]\']', '', article_title)

            if unidecode(article_title.lower()) in unidecode(
                    post.title.lower()):
                post.mod.approve()
                print("Approved {0.shortlink} of {0.author}'s".format(post))
            else:
                report_reason = "Title Mismatch.Original Title: {}".format(
                    unidecode(article_title))
                # print (report_reason)
                if len(report_reason) > 100:
                    post.report("Title may not match. Please check and "
                                "approve.")
                else:
                    post.report(report_reason)
                print("Reported {0.shortlink} of {0.author}'s for title "
                      "mismatch".format(post))
                print("OP's Reddit Post Title- ", unidecode(post.title))
                print("Original Article Title- ", unidecode(article_title))

        if article_data['domain'] in ignore_title_check_domains:
            post.report('Bot can not help, check title and approve.')

    except Exception as e:
        print("Error on line {}".format(
            sys.exc_info()[-1].tb_lineno), type(e), e)
        print("Ignored", post.shortlink, "due to", e)
        ignored.append(post.id)


def auto_flair(post):
    if (post.link_flair_text is None and post.banned_by is not None):
        for flairs in all_flairs:
            for flair in flairs:
                if flair.lower() in post.title.lower():
                    flair_text = flairs[0][1:-1]
                    post.mod.flair(text=flair_text)
                    print("Flaired", post.shortlink, "as", flairs[0])
                    return True
    return False


def flair_check(post, r):
    if (auto_flair(post) is True):
        return
    # If message has no flair
    if (post.link_flair_text is None and str(post.subreddit) == 'india'):
        if((time.time() - post.created_utc) > time_until_message) and (
                post.id not in no_flair.values()):
            final_add_flair_message = add_flair_message.format(
                post_url=post.shortlink)
            print("Sent Message to : {}".format(post.author))
            print("for above post {0.shortlink}".format(post))
            r.redditor(post.author.name).message(
                post.shortlink, final_add_flair_message)
            # comment = post.reply(final_add_flair_message)
            # comment.mod.distinguish(sticky=True)
            no_flair[post.shortlink] = post.id
            # flairchecked_comment.append(comment.id)
            # flaiedchecked_post.append(post.id)
        no_flair_timeout_check(post)


def no_flair_timeout_check(post):
    if(str(post.subreddit) == 'india'):
        if((time.time() - post.created_utc) > time_until_remove):
            final_remove_post_message = remove_post_message.format(
                post_url=post.shortlink)
            comment = post.reply(final_remove_post_message)
            comment.mod.distinguish(sticky=True)
            post.mod.remove()
            print("Removed {0.shortlink} of {0.author}s for no flair".format(
                post))
            for k in list(no_flair.keys()):
                if no_flair[k] == post.id:
                    print("Popped the post")
                    no_flair.pop(k)
    else:
        ignored.append(post.id)


def basic_post_check(post):
    return post.is_self is False and post.secure_media is None and (
        post.banned_by is None) and post.link_flair_text is not None and (
        post.id not in ignored) and post.num_reports == 0

            
def tweetthisbot(comment):
    parent_post=comment.submission()
	tweet_message= parent_post.title + parent_post.shortlink
	parent_post.is_self is True or (parent_post.is_self is False and post.secure_media is not None)
		print (tweet_message)	
	else:
		media_url = parent_post.url
		tweet_message= 
while True:
    r = praw.Reddit(client_id=os.environ['client_id'],
                    client_secret=os.environ['client_secret'],
                    password=os.environ['REDDIT_PASSWORD'],
                    user_agent=os.environ['useragent'],
                    username=os.environ['REDDIT_USERNAME'])
    print("Logged In as ", r.user.me())
    subreddit = r.subreddit('india+gstindia')
    print("Found list of submissions")
    try:
        while True:
            if (datetime.now() - last_purged).seconds > (
                    purge_interval_min * 60):
                del ignored[:]
                print("Purged ignored", ignored)
                last_purged = datetime.now()
            print("Checking the new submissions since the last run!")
            unmoderated = [x for x in subreddit.mod.unmoderated(limit=None)]

            for post in unmoderated:
                if (post.is_self is False and post.id not in ignored and (
                        post.secure_media is None) and (
                            post.subreddit == 'gstindia')):
                    article_data = get_article_data(post)
                    if article_data is not None:
                        anti_anti_ad_block(article_data, post)
                        ignored.append(post.id)
                        post.mod.approve()
                        continue
                    else:
                        ignored.append(post.id)
                else:
                    if basic_post_check(post):
                        article_data = get_article_data(post)
                        print('init title check')
                        if article_data is not None:
                            anti_anti_ad_block(article_data, post)
                            # Language check Code is commented out as we are
                            # getting a lot of false positives
                            if 'title' in article_data:
                                # Perform Title check only if Mercury API
                                # returns 'title'
                                original_title_check(post, article_data)
                    flair_check(post, r)
            
            #New twitter code 
            for comment in r.subreddit('subreddit').stream.comments():
                if TwitterKeyword in comment.body and comment.author == 'root_su':
                    tweetthisbot(comment)
                                        
            time.sleep(delay_base_min * 60)
    except Exception as e:
        print('Error on line {}'.format(
            sys.exc_info()[-1].tb_lineno), type(e), e)
        print("RESET due to: ", e)
        time.sleep(delay_base_min * 60)
