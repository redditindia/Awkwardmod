from settings import H_TIME_UNTIL_REMOVE

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
                         H_TIME_UNTIL_REMOVE, footer_message))

remove_post_message = ("Your post does not have any flair after the allotted "
                       "{} and has therefore been removed. Feel free to "
                       "resubmit it and remember to flair it once it is "
                       "posted.".format(H_TIME_UNTIL_REMOVE, footer_message))

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
