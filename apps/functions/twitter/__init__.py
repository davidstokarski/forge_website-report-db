from re import S
import tweepy
# import configparser
import pandas as pd
 
api_key = "Qav0kQrv06rEU99YZleAJrUVv"
api_key_secret = "4U4omgAa2h0xj1PxHOIECS0xg4T5gzCfPotRQV9e6zBP74AR1g"
access_token = "1534315674406895621-zRzI6CXHugkjD2je6EgpK848cPKtlu"
access_token_secret = "7GeAndTyJBCRGiA35jGLod7NWgQD5VisiJpAtbKYgdFKe"
auth = tweepy.OAuthHandler(api_key, api_key_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth)
 
async def twitter_function(search_terms,limit,remove_dups):
    #you can change 'user' to whatever twitter handle you want
    limit = int(limit)
    
    tweets = tweepy.Cursor(api.search_tweets, q = ' '.join(search_terms),
                count=100, tweet_mode='extended').items(limit)
    
    columns = ['Time', 'User', 'Tweet']
    data = []
    unique=[]
    for tweet in tweets:
        try:
            txt=tweet.full_text.split(': ')[1]
        except:
            txt=tweet.full_text
        if txt not in unique and remove_dups==True:
            unique.append(txt)
            data.append([tweet.created_at, tweet.user.screen_name, tweet.full_text])
    df = pd.DataFrame(data, columns=columns)
    return df