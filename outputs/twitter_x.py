#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Twitter Publisher
# Adapted from papersbot.py
#

import os
import re
import time
import tweepy
import yaml
from bs4 import BeautifulSoup
import urllib.request
import urllib.parse
import filetype


def html_to_text(s):
    return BeautifulSoup(s, "html.parser").get_text()


def clean_text(s):
    s = s.replace("[ASAP]", "").replace("\x0A", "")
    s = re.sub(r"\(arXiv:.+\)", "", s)
    return re.sub(r"\s\s+", " ", s).strip()


def find_image(entry):
    if "description" not in entry:
        return
    soup = BeautifulSoup(entry.description, "html.parser")
    img = soup.find("img")
    if img:
        img = img["src"]
        if len(img) == 0:
            return
        if img[0] == "/":
            p = urllib.parse.urlparse(entry.id)
            img = f"{p.scheme}://{p.netloc}" + img
    return img


def download_image(url):
    if not url:
        return None
    try:
        img, _ = urllib.request.urlretrieve(url)
    except Exception:
        return None
    kind = filetype.guess(img)
    if kind:
        res = f"{img}.{kind.extension}"
        os.rename(img, res)
    else:
        return None
    if os.path.getsize(res) < 4096:
        os.remove(res)
        return None
    return res


class TwitterPublisher:
    def __init__(self, config):
        self.config = config
        self.api_v1 = None
        self.api_v2 = None
        self.maxlength = 280
        if 'twitter' in config:
            self._init_twitter()

    def _init_twitter(self):
        cred = self.config['twitter']
        auth = tweepy.OAuthHandler(cred["consumer_key"], cred["consumer_secret"])
        auth.set_access_token(cred["access_key"], cred["access_secret"])
        self.api_v1 = tweepy.API(auth)
        self.api_v2 = tweepy.Client(
            consumer_key=cred["consumer_key"],
            consumer_secret=cred["consumer_secret"],
            access_token=cred["access_key"],
            access_token_secret=cred["access_secret"]
        )
        print("Twitter initialized")

    def publish(self, message):
        if not self.api_v2:
            return  # Skip if not configured
        title = clean_text(html_to_text(message['title']))
        url = message['link']
        tweet_body = f"{title[:self.maxlength - len(url) - 1]} {url}"
        media = None
        # Note: Image handling simplified, assume entry available or skip
        print(f"TWEET: {tweet_body}")
        try:
            self.api_v2.create_tweet(text=tweet_body, media_ids=media)
        except tweepy.errors.TooManyRequests:
            print("Twitter rate limit hit")
        except Exception as e:
            print(f"Twitter error: {e}")