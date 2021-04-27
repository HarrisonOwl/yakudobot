import datetime
import tempfile
import requests
import os
import tweepy
from threading import Thread
import cv2
from main import db
from database.models import YakudoScore
import traceback

auth = tweepy.OAuthHandler(os.environ.get('CONSUMER_KEY'),os.environ.get('CONSUMER_SECRET'))
auth.set_access_token(os.environ.get('ACCESS_TOKEN_KEY'), os.environ.get('ACCESS_TOKEN_SECRET'))
api = tweepy.API(auth)
keyword= ['#mis1yakudo']

botname = "nishinomiya443"

yakudo = None
msg = ""
url = ""
userid = None

class MyStreamListener(tweepy.StreamListener):

    def on_status(self, status):
        t = Thread(runtask(status))
        t.start()

def checkyakudo(url):
    # load img from url
    res = requests.get(url)
    img = None
    with tempfile.NamedTemporaryFile(dir='./') as fp:
        fp.write(res.content)
        fp.file.seek(0)
        img = cv2.imread(fp.name)
    result = (1/cv2.Laplacian(img, cv2.CV_64F).var())*10000 # yakudoスコアの計算
    return result

def runtask(status):
    print(status.user.screen_name)
    if status.user.screen_name != botname:
        url = "https://twitter.com/" + status.user.screen_name + "/status/" + status.id_str
        msg = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')+"\n"
        msg += "User:@"+status.user.screen_name + "\n"
        # yakudo_check_block
        yakudo = YakudoScore(username=status.user.screen_name,tweetid=status.id_str,date=datetime.datetime.now().strftime('%Y-%m-%d'))
        if hasattr(status, 'extended_entities'):
            finalscore = 0
            count = 0
            isphoto = True
            for image in status.extended_entities["media"]:
                if image["type"] == "video":
                    msg += "やめろ！クソ動画を投稿するんじゃない!\n"
                    msg += "Score:-inf\n"
                    yakudo.score = 0
                    isphoto = False
                    break
                score = checkyakudo(image['media_url_https'])
                finalscore += score
                count += 1
                childtext = "{:.0f}枚目:{:.3f}\n"
                msg += childtext.format(count, score)
                yakudo.score = score
            if isphoto:
                finalscore /= count
                msg += "GoodYakudo!\n" if finalscore >= 150 else "もっとyakudoしろ！\n"
                finaltext = "Score:{:.3f}\n"
                msg += finaltext.format(finalscore)
        else:
            msg += "画像が入ってないやん!\n"
            msg += "Score:-inf\n"
            yakudo.score = 0
        api.update_status(msg + url)
        api.create_friendship(status.user.id)
        userid = status.user.id
        db.session.add(yakudo)
        db.session.commit()

def start_monitoring():
    myStreamListener = MyStreamListener()
    print("start monitoring")
    while True:
        try:
            if yakudo is not None and msg != "" and url != "":
                api.update_status(msg + url)
                api.create_friendship(userid)
                db.session.add(yakudo)
                db.session.commit()
            print("start streaming")
            myStream = tweepy.Stream(auth=api.auth, listener=myStreamListener)
            myStream.filter(track=keyword)
        except:
            traceback.print_exc()
            continue

if __name__ == "__main__":
    start_monitoring()
