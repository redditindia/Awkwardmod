import os
import re
import pprint
import sys
import time
import signal
import atexit
import Antiblockdomains
from datetime import datetime
from datetime import timedelta
from collections import OrderedDict

from unidecode import unidecode
import langdetect
import praw
from newspaper import Article
import mechanicalsoup
import requests
import html2text
from readability import Document
from langdetect import detect_langs
from praw.models import Comment


#Export youer reddit mod username and password as REDDIT_USERNAME and REDDIT_PASSWORD respectively.
#Run as follows: python3 awkwardmod.py

#adding for testing something

mercury_web_parser_key = os.environ['MERCURY_API_KEY']
mercury_api_url = 'https://mercury.postlight.com/parser?url=%s'

print("BEGIN")
def exit_handler():
	print("END")
atexit.register(exit_handler)

def get_browser():
	br = mechanicalsoup.Browser()
	return br

#BEGIN TITLE VARS
delay_base_min = 1
ignored = list()
not_flaied = list()
flairchecked = list()
last_purged = datetime.now()
purge_interval_min = 60

#END TITLE VARS

#BEGIN AUTO-FLAIR VARS
ask_flairs = ['[Askindia]', '[Askindia]', '[Ask]', '[AS]', '[Help]']
spo_flairs = ['[Sports]', '[Sports]', '[SP]']
tec_flairs = ['[Science/Technology]', '[Science Technology]', '[TECH]', '[TE]']
foo_flairs = ['[Food]', '[Food]', '[FO]']
npo_flairs = ['[Casual]', '[Non-Political]', '[NP]']
pol_flairs = ['[Politics]', '[Politics]', '[P]']
red_flairs = ['[[R]eddiquette]', '[Reddiquette]', '[R]']
all_flairs = [ask_flairs, spo_flairs, tec_flairs, foo_flairs, npo_flairs, pol_flairs, red_flairs]
#END AUTO-FLAIR VARS

#BEGIN FLAIR VARS
time_until_message = 1 * 60
time_until_remove = 10 * 60
h_time_until_remove = str(timedelta(seconds=time_until_remove))
max_retries = 3
no_flair = OrderedDict()
anti_anti_ad_block_domains = Antiblockdomains.anti_anti_ad_block_domains
#END FLAIR VARS

'''----------------------------------Messages---------------------------------------------------------------'''
footer_message = ("\n\n"
				  ">**What is a Flair?**\n\n"
				  ">A flair basically categorizes your post in one of the pre-existing categories on /r/india. Once you make a submission, you'll notice a red button which says *Flair your post* . Click on it and choose a flair according to the submission's theme, then hit Save.\n\n"
				  ">* If you want a civil and focused discussion with NO off-topic comments, choose \"[R]ediquette\". We do not allow trolling and other unnecessary behaviour in [R] threads.\n"
				  "* If you are posting from a handheld device, append [NP] for non-political, [P] for political and [R] to the title of the post and our bot will flair it accordingly.\n"
				  "* **Example**: http://i.imgur.com/FKs9uVI.png\n\n"
				  "---\n\n"
				  "^(I am just a bot and cannot reply to your queries. Send a) [^*modmail*](http://www.reddit.com/message/compose?to=%2Fr%2Findia&subject=Flair+Bot) ^(if you have any doubts.)")
add_flair_message = ("Your post does not have any flair and will soon be removed if it remains so.\n\n"
					 "Please add flair to your post. "
					 "If you do not add flair within **" + h_time_until_remove + "**, you will have to resubmit your post. "
					 "" + footer_message)
remove_post_message = ("Your post does not have any flair after the allotted "+ h_time_until_remove + " and has therefore been removed."
					   "Feel free to resubmit it and remember to flair it once it is posted."
					   "" + footer_message)


title_mismatch_message = ''' Unfortunately, your submission breaks the rules and has been removed. 
> All links (articles, images or infographics) should contain its original title (and/or subtitle). An original title (and/or subtitle) is the one given by the content creator. If a submission which has no title, you should make a self post with an accurate description of the content. Refer : https://www.reddit.com/r/india/wiki/rules#wiki_original_title 
\n\n 
If this was an error, please report this submission (not the comment) via the report button. I am just a bot and cannot reply to your queries. Send a [*modmail*](http://www.reddit.com/message/compose?to=%2Fr%2Findia&subject=Title+Bot) if you have any doubts. Please provide a link to your submission. We would not be able to help you without a link. '''


not_english_title_message = ''' Unfortunately, your submission breaks the rules and has been removed. 
> This subreddit requires all submissions and their titles to be in English. Please resubmit using a translated title. Refer : https://www.reddit.com/r/india/wiki/rules#wiki_submission_language
\n\n 
If this was an error, please report this submission (not the comment) via the report button. I am just a bot and cannot reply to your queries. Send a [*modmail*](http://www.reddit.com/message/compose?to=%2Fr%2Findia&subject=Title+Language+Bot) if you have any doubts. Please provide a link to your submission. We would not be able to help you without a link.
'''

not_english_article_message = ''' Unfortunately, your submission breaks the rules and has been removed. 
> This subreddit requires all submissions and their titles to be in English. Please provide a translation of the article in the comments, and send a message to the moderators to re-approve the submission. Refer : https://www.reddit.com/r/india/wiki/rules#wiki_submission_language
\n\n 
If this was an error, please report this submission (not the comment) via the report button. I am just a bot and cannot reply to your queries. Send a [*modmail*](http://www.reddit.com/message/compose?to=%2Fr%2Findia&subject=Article+Language+Bot) if you have any doubts. Please provide a link to your submission. We would not be able to help you without a link.'''

anti_anti_ad_block_header = '''^This ^article ^is ^adblocker ^unfriendly, ^following ^is ^the ^text ^of ^the ^article. \n\n ______ '''

anti_anti_ad_block_footer = '''\n\n ______ \n ^I ^am ^just ^a ^bot, ^I ^cannot ^reply ^to ^your ^queries. ^Send ^a ^[*modmail*](http://www.reddit.com/message/compose?to=%2Fr%2Findia&subject=Anti+Anti+Ad+Block+Bot) ^if ^you ^have ^any ^queries. ^Please ^provide ^a ^link ^to ^your ^submission. ^We ^would ^not ^be ^able ^to ^help ^you ^without ^a ^link.'''


'''----------------------------------Messages Over----------------------------------------------------------'''
					   

''' Takes Text as input and ignores unicode characters to get nearest ASCII format'''


def normalize_unicode(text):
	return unicodedata.normalize('NFKD', text).encode('ascii','ignore').decode('utf-8')


def title_check(post):
	#Approve when a title match can be confirmed.
	if (post.is_self is False and post.secure_media is None and post.banned_by is None and \
		post.link_flair_text is not None and post.id not in ignored and post.num_reports == 0):
		try:
			real_title_1 = ''
			try:
				a = Article(post.url)
				a.download()
				a.parse()
				real_title_1 = re.sub(r'[^\w]', '', a.title).lower()
			except Exception as e:
				print("ERROR", e, "while using newspaper")
			real_title_2 = ''
			real_title_3 = ''
			try:
				soup = get_browser().get(post.url, timeout=15).soup
				real_title_2 = soup.title.text
				real_title_2 = re.sub(r'[^\w]', '', real_title_2).lower()
				real_title_3 = str(soup.h1)
				real_title_3 = re.sub(r'[^\w]', '', re.sub(r'<.*?>', '', real_title_3)).lower()
				real_s_title = str(soup.h1.nextSibling).strip()
				if not real_s_title:
					real_s_title = str(soup.h1.nextSibling.nextSibling).strip()
				real_s_title = re.sub(r'[^\w]', '', re.sub(r'<.*?>', '', real_s_title)).lower()
				real_title_3 = real_title_3 + real_s_title
			except Exception as e:
				print("ERROR", e, "while using BeautifulSoup")
			post_title_1 = re.sub(r'[^\w]', '', post.title).lower()
			post_title_2 = re.sub(r'[^\w]', '', re.sub(r'\[.*?\]', '', post.title)).lower()
			if (post_title_1 in real_title_1 or post_title_2 in real_title_1 or \
				post_title_1 in real_title_2 or post_title_2 in real_title_2 or \
				post_title_1 in real_title_3 or post_title_2 in real_title_3):
				#new praw 4.4.0 doc
				post.mod.approve()
				print("Approved {0.shortlink} of {0.author}'s".format(post))
			else:
				print("DEBUG", real_title_1, real_title_2, real_title_3, post_title_1, post_title_2)
				raise Exception('title mismatch')
		except Exception as e:
			print((traceback.format_exc()))
			ignored.append(post.id)


def ndtv_anti_ad_block_text(article):
	doc = Document(article.html)
	text_maker = html2text.HTML2Text()
	text_maker.ignore_links = True	
	text_maker.ignore_images = True	
	return text_maker.handle(doc.summary())

	
def anti_anti_ad_block(article_data, post):
	try:
		content = article_data['content']
		domain = article_data['domain']
		
		if domain in anti_anti_ad_block_domains :
			article = Article(post.url)
			article.download()
			article.parse()
			article_title = '''\n**%s** \n\n ______ '''%(article_data['title'])

			if domain in ('www.ndtv.com','www.newslaundry.com') :
				anti_ad_block_text = anti_anti_ad_block_header + article_title + '\n' + ndtv_anti_ad_block_text(article) + anti_anti_ad_block_footer
				comment = post.reply(anti_ad_block_text)
				print("Posted Anti Ad Block Comment for {0.shortlink} of {0.author}".format(post))	 
			else : 
				anti_ad_block_text = anti_anti_ad_block_header + article_title + '\n' + article.text + anti_anti_ad_block_footer
				if len(anti_ad_block_text) < 10000:
					if "Get instant notifications from Economic Times" not in anti_ad_block_text:
						comment = post.reply(anti_ad_block_text)
						print("Posted Anti Ad Block Comment for {0.shortlink} of {0.author}".format(post))	 
					else:
						print("Not Posting Anti Ad Block Comment for {0.shortlink} of {0.author} as economic times has derped".format(post))
				else:
					print("Could not post Anti Ad Block Comment for {0.shortlink} of {0.author} because of comment length".format(post))	 
	except Exception as e:
		print("Error from Mercuty on {0.shortlink} of {0.author}".format(post))	
		ignored.append(post.id)
		pass

def get_article_data(post):
	
	try:
		request_header = {'content-type': 'application/json', 'x-api-key': mercury_web_parser_key}

		r = requests.get(mercury_api_url%post.url, headers=request_header)
		if r.status_code == requests.codes.ok :
			article_data = r.json()
			#print(article_data) Uncommet this to check mercury 404
			return article_data

		else : 
			print("Mercury Web Parser Failed for {0.shortlink} of {0.author} ".format(post))
			print ("Status Code", r.status_code)
			ignored.append(post.id)
	except Exception as e:
		print('Could not fetch data for the article {}'.format(sys.exc_info()[-1].tb_lineno), type(e), e)
		print("RESET", "due to", e)
		ignored.append(post.id)
	

''' Returns True if Text is in English with a Probability >= 0.8'''

def language_check(text):
	top_lang = detect_langs(text)[0]
	return (top_lang.lang == 'en' and top_lang.prob >= 0.7, top_lang.lang, top_lang.prob)
  

''' Check if Title in English and if not remove the post'''
''' This method is not in use for now as we are getting multiple false positive'''

def check_post_title_language(post):
	if (post.is_self is False and post.secure_media is None and post.banned_by is None and \
		post.link_flair_text is not None and post.id not in ignored and post.num_reports == 0):

		(title_lang_check, title_lang, title_prob) = language_check(post.title)

		if not title_lang_check :
			#praw.4.4.0 code
			post.mod.remove(spam=False)
			comment = post.reply(not_english_title_message)
			#comment.mod.distinguish(sticky=True)
			r.subreddit('india').flair.set('Not in English')
			print("Removed {0.shortlink} of {0.author}'s for Title not in English".format(post))	 
			
		return (title_lang_check, title_lang, title_prob)


''' Check if Article in English and if not remove the post asking for a translation '''

def check_article_language(article_data):
	(article_en_check, article_lang, article_prob) = language_check(article_data['content'])

	if not article_en_check:

		post.mod.remove(spam=False)
		comment = post.reply(not_english_article_message)
		#comment.mod.distinguish(sticky=True)
		r.subreddit('india').flair.select('Not in English')
		print("Removed {0.shortlink} of {0.author}'s for Article Content not in English".format(post))  
		print("English Check, Language, Probability", (article_en_check, article_lang, article_prob))		  
		
	return (article_en_check, article_lang, article_prob)



''' Approve when a Title Match is Confirmed 
	Mercury Web Parser API : https://mercury.postlight.com/web-parser/
	Newspaper3k : https://github.com/codelucas/newspaper/
	Currently using Mercury as Newspaper3k extracts title from HTML headers on Heroku deployment.
'''


def original_title_check(post, article_data):
	'''Below websites titles are usually different than actual title'''
	ignore_title_check_domains = ['newslaundry.com','ETtech.com ']
	'''No point in checking title with twitter'''
	ignore_twitter = ['twitter.com']

	try : 
		article_title = article_data['title']
		content_check = 'content' in article_data
		
		''' Ignore Twitter links and non English articles for automated checks due to English Title rules '''

		if content_check and article_data['domain'] not in ignore_title_check_domains and article_data['domain'] not in ignore_twitter: 

			''' Article title will always be a subset of Reddit Post Title. This is to take care of mobile flairs like [P], [NP] etc.'''
			#Striping [],apostrophe from title and article title while original title check
			post.title=re.sub('[\[\]\']','',post.title)
			article_title=re.sub('[\[\]\']','',article_title)
			
			if unidecode(article_title.lower()) in unidecode(post.title.lower()) :
				post.mod.approve()
				print("Approved {0.shortlink} of {0.author}'s".format(post))

			else :
				report_reason= "Title Mismatch.Original Title:"+ unidecode(article_title)
				#print (report_reason)
				if len(report_reason) > 100:
					post.report("Title may not match. Please check and approve.")
				else:
					post.report(report_reason)
				print("Reported {0.shortlink} of {0.author}'s for title mismatch".format(post))
				print ("OP's Reddit Post Title- ", unidecode(post.title))
				print ("Original Article Title- ", unidecode(article_title))

		if article_data['domain'] in ignore_title_check_domains :
			post.report('Bot can not help, check title and approve.')

	except Exception as e:
		print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno), type(e), e)
		print("Ignored", post.shortlink, "due to", e)
		ignored.append(post.id)





def auto_flair(post):
	if (post.link_flair_text is None and post.banned_by is not None):
		for flairs in all_flairs:
			for flair in flairs:
				if flair.lower() in post.title.lower():
					template= flairs[1][1:-1]
					flair_text= flairs[0][1:-1]
					post.mod.flair(text =flairs[0][1:-1])
					print("Flaired", post.shortlink, "as", flairs[0])
					return True
	return False

def flair_check(post,r):
	if (auto_flair(post) is True):
		return
	# If message has no flair
	if (post.link_flair_text is None and str(post.subreddit) == 'india'):
		if((time.time() - post.created_utc) > time_until_message) and post.id not in no_flair.values():
			final_add_flair_message = add_flair_message.format(post_url=post.shortlink)
			print("Sent Message to : {}".format(post.author))
			print("for above post {0.shortlink}".format(post))
			r.redditor(post.author.name).message(post.shortlink, final_add_flair_message)
			#comment = post.reply(final_add_flair_message)
			#comment.mod.distinguish(sticky=True)
			no_flair[post.shortlink] = post.id
			#flairchecked_comment.append(comment.id)
			#flaiedchecked_post.append(post.id)
		no_flair_timeout_check(post)
		
def no_flair_timeout_check(post):
	if(str(post.subreddit) == 'india'):	
		if((time.time() - post.created_utc) > time_until_remove):
			final_remove_post_message = remove_post_message.format(post_url=post.shortlink)
			comment = post.reply(final_remove_post_message)
			comment.mod.distinguish(sticky=True)
			post.mod.remove()
			print("Removed {0.shortlink} of {0.author}s for no flair".format(post))
			for k in list(no_flair.keys()):
				if no_flair[k] == post.id:
					print("Popped the post")
					no_flair.pop(k)
					'''Below code is a legacy code which does not work with new praw, Need to check'''
					#retry = 0
					# while retry < max_retries:
						# retry = retry + 1
						# try:
							# k_comment = r.submission(k).comments[0]
							# k_comment.mod.remove()
						# except Exception as e:
							# print((traceback.format_exc()))
							#print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno), type(e), e)
							# pass
	else:
		ignored.append(post.id)

while True:
	r = praw.Reddit(client_id=os.environ['client_id'],
					client_secret=os.environ['client_secret'],
					password=os.environ['REDDIT_PASSWORD'],
					user_agent=os.environ['useragent'],
					username=os.environ['REDDIT_USERNAME'])		
	print("Logged In as ", r.user.me())
	subreddit=r.subreddit('india+gstindia')
	print("Found list of submissions")
	try:
		while True:
			if (datetime.now() - last_purged).seconds > (purge_interval_min * 60):
				del ignored[:]
				print("Purged ignored", ignored)
				last_purged = datetime.now()
			print("Checking the new submissions since the last run!")
			unmoderated = [x for x in subreddit.mod.unmoderated(limit=None)]
			
			for post in unmoderated:
				
				if (post.is_self is False and post.id not in ignored and post.secure_media is None and post.subreddit == 'gstindia'):	
					article_data = get_article_data(post)
					if article_data is not None:
						anti_anti_ad_block(article_data, post)
						ignored.append(post.id)
						post.mod.approve()
						continue
					else:
						ignored.append(post.id)
				else:
					if (post.is_self is False and post.secure_media is None and post.banned_by is None and post.link_flair_text is not None and post.id not in ignored and post.num_reports == 0):
						article_data = get_article_data(post)
						print('init title check')
						if article_data is not None :
							anti_anti_ad_block(article_data, post)
							# Language check Code is commented out as we are getting a lot of false positives
							if 'title' in article_data: 
								# Perform Title check only if Mercury API returns 'title'						
								original_title_check(post, article_data)

					flair_check(post,r)
			time.sleep(delay_base_min * 60)
	except Exception as e:
		print((traceback.format_exc()))
		print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno), type(e), e)
		print("RESET", "due to", e)
		time.sleep(delay_base_min * 60)