import tweepy,os,datetime,time
from apscheduler.schedulers.blocking import BlockingScheduler
from main import db
from database.models import YakudoScore

twische = BlockingScheduler()

auth = tweepy.OAuthHandler(os.environ.get('CONSUMER_KEY'),os.environ.get('CONSUMER_SECRET'))
auth.set_access_token(os.environ.get('ACCESS_TOKEN_KEY'), os.environ.get('ACCESS_TOKEN_SECRET'))
api = tweepy.API(auth)
userID = "mis1yakudo334"

def getalltweets():
    all_tweets = []
    Current_Date = datetime.datetime.today()
    starttime = Current_Date.strftime('%Y-%m-%d_00:00:00_JST')
    endtime = Current_Date.strftime('%Y-%m-%d_23:59:59_JST')
    tweets = api.user_timeline(screen_name=userID,since = starttime, until = endtime, count=200,include_rts=False, tweet_mode='extended')
    all_tweets.extend([t for t in tweets if "Score:" in t.full_text])
    oldest_id = tweets[-1].id
    while True:
        tweets = api.user_timeline(screen_name=userID, since = starttime, until = endtime, count=200,include_rts=False,max_id=oldest_id - 1,tweet_mode='extended')
        if len(tweets) == 0:
            break
        oldest_id = tweets[-1].id
        all_tweets.extend([t for t in tweets if "Score:" in t.full_text])
    return all_tweets

@twische.scheduled_job('interval',minutes=1)
def timed_job():
    now = datetime.datetime.now()
    if now.minute == 0:
        yakudos = YakudoScore.query.filter(YakudoScore.date==datetime.datetime.now().strftime('%Y-%m-%d')).all()
        if len(yakudos) == 0:
            api.update_status("おいお前ら!早くyakudoしろ!(" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M') + ")")
        else:
            api.update_status("本日のyakudo:" + str(len(yakudos)) + "件(" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M') + ")")
        print("ScheduledTask Complete")
    elif now.minute == 59 and now.hour == 23:
        yakudos = YakudoScore.query.filter(YakudoScore.date == datetime.datetime.now().strftime('%Y-%m-%d')).all()
        maxscore = 0
        maxuser = ""
        maxtweetid = ""
        if len(yakudos) == 0:
            api.update_status("本日のyakudoは...何一つ...出ませんでした...")
        else:
            for yakudo in yakudos:
                if yakudo.score > maxscore:
                    maxscore = yakudo.score
                    maxtweetid = yakudo.tweetid
                    maxuser = yakudo.username
            if maxscore > 0:
                msg = "Highest Score:{:.3f}\n優勝おめでとう!\n".format(maxscore)
                url = "https://twitter.com/" + maxuser + "/status/" + maxtweetid
                api.update_status(msg + url)
            else:
                api.update_status("おい待てや...今日のyakudo...-inf点しか無いやん...")
    elif now.minute == 50:
        print("Checking Database")
        yakudos = YakudoScore.query.filter(YakudoScore.date == datetime.datetime.now().strftime('%Y-%m-%d')).all()
        count = 0
        for yakudo in yakudos:
            try:
                tweet = api.get_status(yakudo.tweetid)
            except:
                print("Tweet Not Found")
                time.sleep(1)
                api.destroy_status(yakudo.retweetid)
                YakudoScore.query.filter(YakudoScore.tweetid == yakudo.tweetid).delete()
                db.session.commit()
            count+=1
            time.sleep(1)
            if count >= 200:
                break



if __name__ == "__main__":
    twische.start()