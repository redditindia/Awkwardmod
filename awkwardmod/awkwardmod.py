import re
import sys
import time
from datetime import datetime
from collections import OrderedDict
from perspective import Perspective

	
import praw
import requests
import html2text
from readability import Document
from newspaper import Article
from unidecode import unidecode

from messages import (anti_anti_ad_block_footer, anti_anti_ad_block_header,
                      add_flair_message, remove_post_message)
from settings import (ANTI_ANTI_AD_BLOCK_DOMAINS, DELAY_BASE_MIN, ALL_FLAIRS,
                      TIME_UNTIL_REMOVE, TIME_UNTIL_MESSAGE, MERCURY_API_URL,
                      PURGE_INTERVAL_MIN, LAST_PURGED, MERCURY_WEB_PARSER_KEY,
                      REDDIT_USERNAME, REDDIT_PASSWORD, BOT_USER_AGENT,
                      REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET,PERSPECTIVE_API_KEY)

IGNORED = []
NO_FLAIR = OrderedDict()


# Extracts the content from NDTV and Newslaundry sites for anti ad block
# comment. It is used by `get_anti_ad_block_text`.
def ndtv_anti_ad_block_text(article):
    doc = Document(article.html)
    text_maker = html2text.HTML2Text()
    text_maker.ignore_links = True
    text_maker.ignore_images = True
    return text_maker.handle(doc.summary())


# Constructs the comment with the content from ANTI_ANTI_AD_BLOCK_DOMAINS
# submissions
def get_anti_ad_block_text(article, article_data, for_ndtv):
    article_title = F"\n**{article_data['title']}** \n\n ______ "
    response = "{header}{title}\n{body}{footer}"
    if for_ndtv:
        article_body = ndtv_anti_ad_block_text(article)
    else:
        article_body = article.text
    return response.format(
        header=anti_anti_ad_block_header, title=article_title,
        body=article_body, footer=anti_anti_ad_block_footer)


# If the submission's link belongs to any of the domains in
# ANTI_ANTI_AD_BLOCK_DOMAINS, then extracts the data from the link and posts
# as a comment
def anti_anti_ad_block(article_data, post):
    try:
        domain = article_data['domain']
        if domain in ANTI_ANTI_AD_BLOCK_DOMAINS:
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
        IGNORED.append(post.id)
        pass


# Uses https://mercury.postlight.com to extract the data from the article
def get_article_data(post):
    try:
        request_header = {'content-type': 'application/json',
                          'x-api-key': MERCURY_WEB_PARSER_KEY}
        r = requests.get(MERCURY_API_URL.format(post.url),
                         headers=request_header)
        if r.status_code == requests.codes.ok:
            article_data = r.json()
            # print(article_data) Uncommet this to check mercury 404
            return article_data
        else:
            print("Mercury Web Parser Failed for {0.shortlink} of "
                  "{0.author} ".format(post))
            print("Status Code", r.status_code)
            IGNORED.append(post.id)
    except Exception as e:
        print('Could not fetch data for the article {}'.format(
            sys.exc_info()[-1].tb_lineno), type(e), e)
        print("RESET", "due to", e)
        IGNORED.append(post.id)


# Checks if the submission title matches with the link's title, if not reports
# the submission
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
        IGNORED.append(post.id)


# Checks if the post can be auto flaired by checking flair mentions in the
# post title like '[NP]', [Ask] etc
def auto_flair(post):
    if (post.link_flair_text is None and post.banned_by is not None):
        for flairs in ALL_FLAIRS:
            for flair in flairs:
                if flair.lower() in post.title.lower():
                    flair_text = flairs[0][1:-1]
                    post.mod.flair(text=flair_text)
                    print("Flaired", post.shortlink, "as", flairs[0])
                    return True
    return False


# Checks if a post can be auto flaired using `auto_flair` function, if not
# messages the OP to flair the post within TIME_UNTIL_REMOVE seconds
def flair_check(post, r):
    if (auto_flair(post) is True):
        return
    # If message has no flair, warn OP to add a flair
    if (post.link_flair_text is None and str(post.subreddit) == 'india'):
        if((time.time() - post.created_utc) > TIME_UNTIL_MESSAGE) and (
                post.id not in NO_FLAIR.values()):
            final_add_flair_message = add_flair_message.format(
                post_url=post.shortlink)
            print("Sent Message to : {}".format(post.author))
            print("for above post {0.shortlink}".format(post))
            r.redditor(post.author.name).message(
                post.shortlink, final_add_flair_message)
            NO_FLAIR[post.shortlink] = post.id
        no_flair_timeout_check(post)


# Checks if OP has added a flair to the post, if not and if `TIME_UNTIL_REMOVE`
# has elapsed, removes the post
def no_flair_timeout_check(post):
    if(str(post.subreddit) == 'india'):
        if((time.time() - post.created_utc) > TIME_UNTIL_REMOVE):
            final_remove_post_message = remove_post_message.format(
                post_url=post.shortlink)
            comment = post.reply(final_remove_post_message)
            comment.mod.distinguish(sticky=True)
            post.mod.remove()
            print("Removed {0.shortlink} of {0.author}s for no flair".format(
                post))
            for k in list(NO_FLAIR.keys()):
                if NO_FLAIR[k] == post.id:
                    print("Popped the post")
                    NO_FLAIR.pop(k)
    else:
        IGNORED.append(post.id)


# Checks if the post requires moderation by bot or not
def basic_post_check(post):
    return post.is_self is False and post.secure_media is None and (
        post.banned_by is None) and post.link_flair_text is not None and (
        post.id not in IGNORED) and post.num_reports == 0


while True:
    r = praw.Reddit(client_id=REDDIT_CLIENT_ID, password=REDDIT_PASSWORD,
                    client_secret=REDDIT_CLIENT_SECRET,
                    user_agent=BOT_USER_AGENT, username=REDDIT_USERNAME)
    print("Logged In as ", r.user.me())
	perspective_api = Perspective(PPERSPECTIVE_API_KEY)
    print("Logged In Perspective")
    subreddit = r.subreddit('india+gstindia')
    print("Found list of submissions")
    try:
        while True:
            if (datetime.now() - LAST_PURGED).seconds > (
                    PURGE_INTERVAL_MIN * 60):
                del IGNORED[:]
                print("Purged ignored", IGNORED)
                LAST_PURGED = datetime.now()
            print("Checking the new submissions and reported comments since the last run!")
            unmoderated = [x for x in subreddit.mod.unmoderated(limit=None)]
            
            for post in unmoderated:
                if (post.is_self is False and post.id not in IGNORED and (
                        post.secure_media is None) and (
                            post.subreddit == 'gstindia')):
                    article_data = get_article_data(post)
                    if article_data is not None:
                        anti_anti_ad_block(article_data, post)
                        IGNORED.append(post.id)
                        post.mod.approve()
                        continue
                    else:
                        IGNORED.append(post.id)
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
            
            #Checking modqueue comments and their toxicity
            comments  = [x for x in r.subreddit('india').mod.modqueue(only= 'comments', limit=None)]
            for comment in comments:
                if comment.id not in IGNORED:
                    toxicity_score = perspective_api.score(comment.body, tests=["TOXICITY"])
                    if toxicity_score > 0.8:
                        comment.report("Comment is likely to be toxic")
                        print("Reported {0.shortlink} of {0.author}'s".format(comment))
                        IGNORED.append(comment.id)
                    else:
                        IGNORED.append(comment.id)
        
            time.sleep(DELAY_BASE_MIN * 60)
    except Exception as e:
        print('Error on line {}'.format(
            sys.exc_info()[-1].tb_lineno), type(e), e)
        print("RESET due to: ", e)
        time.sleep(DELAY_BASE_MIN * 60)
