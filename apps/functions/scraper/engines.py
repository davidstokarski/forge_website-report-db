import asyncio
from functools import lru_cache, reduce
from operator import methodcaller 
import time

# Import everything
from tqdm.asyncio import tqdm_asyncio
import httpx # for sending requests
from lxml import etree # important for parsing the DOM (i.e. scraping search results)
from bs4 import BeautifulSoup # very little purpose, could be removed, but helps clean up the dom for lxml

# APIs
## Search engines
from duckduckgo_search import ddg_news # 
from GoogleNews import GoogleNews
## Search libraries
from fuzzywuzzy import fuzz
## Colab

# Utilities
## Data wrangling
import pandas as pd
## Web
from urllib.parse import urlencode, urljoin, unquote # the right way to handle query strings
## Standard stuff
import random
import re
import logging # for logging errors

from apps.utils.asyncify import asyncify

# Mother class for news scraper sources
class NewsSource:
  name = "News"
  def __init__(self, search):
      self.search = search
  def articles(self):
      raise NotImplementedError
  def next_page(self):
      raise NotImplementedError

# SearX scraper

# A nice class that encapsulates everything I want from the searx scraper
# TODO: document better
# Usage: `instance = SearxSearch(search)` where `search` is the term for which to search.
# `instance.articles()` returns a list of articles which are dicts with the properties `title`, `url`, `date`, `body`
# This list is usually paginated, so use `instance.next_page()` to navigate to the next page
# so you can call `instance.articles()` again.
class SearxSearch(NewsSource):
  """Wraps messy scraping of SearX into a neat API"""
  
  SERVERS = ['asowneryt.cloudns.nz', 'northboot.xyz', 'procurx.pt', 's.zhaocloud.net', 'search.bus-hit.me', 'search.chemicals-in-the-water.eu', 'search.jpope.org', 'search.mdosch.de', 'search.neet.works', 'search.ononoki.org', 'search.privacyguides.net', 'search.rabbit-company.com', 'search.roombob.cat', 'search.snopyta.org', 'search.zzls.xyz', 'searx.be', 'searx.ebnar.xyz', 'searx.fmac.xyz', 'searx.gnous.eu', 'searx.gnu.style',
            'searx.loafland.xyz', 'searx.mha.fi', 'searx.mxchange.org', 'searx.orion-hub.fr', 'searx.ppeb.me', 'searx.prvcy.eu', 'searx.pwoss.org', 'searx.sethforprivacy.com', 'searx.sev.monster', 'searx.sp-codes.de', 'searx.stuehieyr.com', 'searx.tiekoetter.com', 'searx.tuxcloud.net', 'searx.tyil.nl', 'searxng.ir', 'searxng.zackptg5.com', 'serx.ml', 'suche.dasnetzundich.de', 'suche.uferwerk.org', 'swag.pw', 'sx.catgirl.cloud', 'www.gruble.de']
  USER_AGENTS = ["Mozilla/5.0 (X11; Linux x86_64; rv:93.0) Gecko/20100101 Firefox/93.0", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.85 Safari/537.36 Edg/90.0.818.46", "Mozilla/5.0 (X11; CrOS x86_64 13982.82.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.157 Safari/537.36"]

  name = "SearX"
  def __init__(self, search, *, server = None, time_range = "", language = "en-US", engines = "bin,gon,ptsn,qwn,wn,yhn,bi,brave,ddg,gb,sp,yh", categories = "news,general"):
      self.all_articles = []
      self.all_urls = set() # for checking duplicates
      self.all_content_hashes = set() # likewise
      # print("Give it a few seconds...")
      while True:
          try:
            self.server = server or random.choice(self.SERVERS)
            # print(f"Chose server: {self.server}")
            self.request("/search?"+urlencode({"q": search, "time_range": time_range, "language": language, "engines": engines, "categories": categories}, safe = "+"))
            if self.res.status_code == 200 and self.res.text:
                break # we've hit a server that likes us
          except:
            pass
          # print("Failed. Trying another...")
      self.parse()
  
  # Helper functions

  def _clean_text(self, element_text):
      # return " ".join([s for s in [str(textNode).strip() for textNode in element_text] if s])
      return re.sub(r'\s+', ' ', "".join(element_text)).strip()

  # TRY EXCEPT THE HORROR!!
  def _parse_article(self, article_element):
      """Dissect a single search result with the surgical precision of xpaths"""
      try:
          full_body = self._clean_text(article_element.xpath("p//text()"))
          image = None
          try:
              # news articles are structured differently
              if 'news' in article_element.xpath("@class")[0]:
                  try:
                      date = article_element.xpath("time/@datetime")[0]
                  except IndexError:
                      match = re.match(
                      r"(?:\d\d? )?[JFMASOND][aepuco][nbrylgptvc][a-z]*(?: \d\d?)?(?:,? \d\d\d\d)?(?:[,/]? \d\d?:\d\d [AP]M)?|\d\d? (?:weeks|days|hours|minutes) ago", full_body)
                      date = None if match is None else match.group()
                  image_query = article_element.xpath(".//img/@src")
                  image = image_query[0] if len(image_query) else None
                  body = full_body
              else:
                  date, body = re.match(
                  r"^((?:\d\d? )?[JFMASOND][aepuco][nbrylgptvc][a-z]*(?: \d\d?)?(?:,? \d\d\d\d)?(?:[,/]? \d\d?:\d\d [AP]M)?|\d\d? (?:weeks|days|hours|minutes) ago) ?.? ?(.+)$", full_body).groups()
          except (NameError, AttributeError) as e:
              date = None
              body = full_body
          
          url_query = article_element.xpath(".//a/@href")
          return {
              "title": self._clean_text(article_element.xpath("h3//text()|h4//text()")),
              "url": url_query[0] if len(url_query) else None,
              "date": date,
              "body": body,
              "image": image
          }
      except:
          # print("Could not parse an article. Element HTML: " +  etree.tostring(article_element, encoding=str, pretty_print=True))
          logging.exception('')
          return {"title": None, "url": None, "date": None, "body": None, "image": None}

  def _get_navigation(self):
      try: 
          form = self.dom.xpath("//*[@id='pagination']//button[contains(.,'next') or contains(.,'Next') or contains(.,'seguinte')]/ancestor::form")[0]
          action = form.xpath("@action")[0]
          inputs = {input.xpath("@name")[0]: input.xpath("@value")[0]
                  for input in form.xpath(".//input")}
          return (inputs, action)
      except Exception as e:
          print("Could not get navigation")
          logging.exception('')

  # check for uniqueness with side effects
  def _unique_save(self, field, unique_set):
    unique = field not in unique_set
    if unique:
      unique_set.add(field)
    return unique

  # Meaty functions
  # TODO: allow POST here as well depending on what the site wants so it's natural
  def request(self, path, *, absolute=False):
      address = path if absolute else urljoin(f"https://{self.server}", path) 
      self.res = httpx.get(address, headers={
          "User-Agent": random.choice(self.USER_AGENTS),
          "Accept": "text/html,application/xhtml+xml,application/xml",
          "Accept-Language": "en-US,en;q=0.5",
          "Accept-Encoding": "gzip, deflate",
          "Connection": "keep-alive",
          "Upgrade-Insecure-Requests": "1",
          "Pragma": "no-cache",
          "Cache-Control": "no-cache"
      })

  def parse(self):
      """Must be called before getting articles"""
      self.soup = BeautifulSoup(self.res.text, "html.parser")
      self.dom = etree.HTML(str(self.soup))

  def articles(self, *, filtered=True):
      filtered_a = None
      try:
          a = [self._parse_article(article) for article in self.dom.xpath('//article[contains(@class, "result")]|//div[@id="main_results"]//div[contains(@class, "result")]')]
          filtered_a = [article for article in a if self._unique_save(article['url'], self.all_urls) and self._unique_save(article['title']+article['body'], self.all_content_hashes)]
          self.all_articles += filtered_a
      except Exception as e:
          print(a)
          print("Could not parse articles. Full content: " + self.res.text)
          logging.exception('')
      else:
          if not len(a):
              print("Empty result. Full content: " + self.res.text)
      if filtered:
        return filtered_a
      else:
        return a

  def to_page(self, pageno = "next"):
      try: 
          inputs, action = self._get_navigation()
          if pageno != "next":
              inputs['pageno'] = pageno

          # init again
          path = f'{action}?{urlencode(inputs, safe="+")}'
          print("Navigating to " + path)
          self.request(path)
          self.parse()
          return pageno if pageno != "next" else int(inputs['pageno'])
      except Exception as e:
          print("Could not navigate to page " + pageno)
          logging.exception('')

  def next_page(self):
      return self.to_page()

# Google News
# Uses python lib
class GoogleNewsSource(NewsSource):
  name = "Google News"
  def __init__(self, search, **kwargs):
    super().__init__(search)
    self.instance = GoogleNews(**kwargs) 
    self._get_news(self.search)
  @lru_cache(None)
  def _get_news(self, search):
    return self.instance.get_news(search)
  def articles(self):
    return [{
        'body': '', 
        'date': r['datetime'], 
        'image': r['img'], 
        'source': r['site'], 
        'url': r['link'], 
        'title': r['title']
      } for r in self.instance.results()]

# Duckduckgo news
# Nice because SearX doesn't currently implement it, although I opened an issue for it at https://github.com/searxng/searxng/issues/1602 
class DdgNewsSource(NewsSource):
  name = "Duckduckgo News"
  def __init__(self, search, **kwargs):
    super().__init__(search)
    self.options = kwargs
  @lru_cache(None)
  def articles(self):
    return ddg_news(self.search, **self.options)

# GDELT
# https://www.gdeltproject.org/
# Global Database of Events, Language, and Tone
class GdeltSource(NewsSource):
  name = "GDELT"
  def __init__(self, search, *, theme = None):
    super().__init__(search)
    # self.options = kwargs
    self.theme = theme
  def articles(self):
    # TODO: integrate theme! http://data.gdeltproject.org/api/v2/guides/LOOKUP-GKGTHEMES.TXT https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/
    query_string = urlencode({"query": self.search, "timespan": "1W", "mode": "artlist", "sort": "hybridrel", "format": "json", "maxrecords": 200}) # i need more
    res = httpx.get(f"https://api.gdeltproject.org/api/v2/doc/doc?{query_string}")
    try:
      data = res.json()
      return [{
          'body': '', 
          'date': a['seendate'], 
          'image': a['socialimage'], 
          'source': a['domain'], 
          'url': a['url'], 
          'title': a['title']
      } for a in data['articles']]
    except:
      print(res.text)
      return []

# Google Alerts
# Uses the RSS feed built by Luke
# This Google Sheet url is currently hardcoded, but this should be fixed
# Generated using File > Share > Publish to web
# on a customized version of Luke's sheet
# TODO: Make it save past alerts instead of just pulling the latest stuff
class GoogleAlerts(NewsSource):
  name = "Google Alerts"
  def __init__(self, search, *, feeds_gsheet_csv_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR_f4MuP6pbHjQv6KRYRvvO7kmhQQ6Pgc6nttxqEaQJy8vu1yYmR1Ly8yeZkXsjQkoAjxo6UQA_4FEV/pub?gid=1148691518&single=true&output=csv" ):
    super().__init__(search)
    self.gsheet = feeds_gsheet_csv_url
    # self.feeds = feeds

  def _get_sheet(self):
    return pd.read_csv(self.gsheet, names=['title', 'title_translated', 'url', 'date', 'description', 'description_translated'])

  def articles(self, n=100):  
    def get_ratio(row):
      name = row['title_translated'] + ' ' + row['description_translated']
      return fuzz.token_sort_ratio(name, self.search)

    df = self._get_sheet()

    # Snip an arbitrary number
    return df.assign(similarity=df.apply(get_ratio, axis=1), body=df['description']).sort_values(['similarity', 'date'], ascending=False)[:n].to_dict(orient='records')

# Yahoo news searcher
# They don't provide an API, so I made a scraper off of the SearX class
# Usage: `instance = YahooNews(search)` where `search` is the term for which to search.
# `instance.articles()` returns a list of articles which are dicts with the properties `title`, `url`, `date`, `body`
# This list is usually paginated, so use `instance.next_page()` to navigate to the next page
# so you can call `instance.articles()` again.
# This is eager loading, so it gets articles as soon as you instantiate it.
class YahooNews(SearxSearch):
  """Yahoo News Scraper Class"""
  
  name = "Yahoo News"
  def __init__(self, search):
      self.all_articles = []
      self.all_urls = set()
      self.all_content_hashes = set() # likewise
      self.server = "news.search.yahoo.com"
      
      self.request("/search?"+urlencode({"p": search, "fr2": "sb-top", "fr": "news", "nojs": True}, safe = "+"))
      self.parse()
  
  # Imagine using monads :')
  def _parse_article(self, article_element):
      """Dissect a single search result with the surgical precision of xpaths"""
      try:
          full_body = self._clean_text(article_element.xpath(".//p//text()"))
          image = None
          # TODO: add source
          try:
              # news articles are structured differently
              try:
                  date = self._clean_text(article_element.xpath(".//span[contains(@class, 's-time')]//text()"))[2:]
              except IndexError:
                  pass # ??
              image_query = article_element.xpath(".//img[@class='s-img']/@src")
              image = image_query[0] if len(image_query) else None
              body = full_body
          except (NameError, AttributeError) as e:
              date = None
              body = full_body
          
          url_query = article_element.xpath(".//a/@href")
          return {
              "title": self._clean_text(article_element.xpath(".//h4//text()")),
              "url": self._untrack_url(url_query[0]) if len(url_query) else None,
              "date": date,
              "body": body,
              "image": image
          }
      except:
          print("Could not parse an article. Element HTML: " +  etree.tostring(article_element, encoding=str, pretty_print=True))
          logging.exception('')
          return {"title": None, "url": None, "date": None, "body": None, "image": None}

  @staticmethod
  def _untrack_url(url):
    try:
      return unquote(re.sub(r'.+RU=([^/]+)/.+', "\\1", url))
    except Exception as e:
      return url

  def articles(self, *, filtered=True):
      filtered_a = None
      try:
          a = [self._parse_article(article) for article in self.dom.xpath('//div[contains(@class, "NewsArticle")]')]
          filtered_a = [article for article in a if self._unique_save(article['url'], self.all_urls) and self._unique_save(article['title']+article['body'], self.all_content_hashes)]
          self.all_articles += filtered_a
      except Exception as e:
          print(a)
          print("Could not parse articles. Full content: " + self.res.text)
          logging.exception('')
      else:
          if not len(a):
              print("Empty result. Full content: " + self.res.text)
      if filtered:
        return filtered_a
      else:
        return a

  # TODO: implement
  def to_page(self, pageno = "next"):
      try: 
          # These urls look like
          # https://news.search.yahoo.com/search;_ylt=AwrXnCVZ0PNi6hkA38_QtDMD;_ylu=Y29sbwNncTEEcG9zAzEEdnRpZAMEc2VjA3BhZ2luYXRpb24-?p=coding&nojs=true&fr=news&fr2=piv-web&b=01&pz=10&bct=0&xargs=0
          # Where `b=01` is the page number zero-indexed followed by `1` 
          goto_url = self.dom.xpath(f"//div[@class='compPagination']//a[@class='next']/@href")[0]
          if pageno != "next": 
              re.sub(goto_url, r'b=(\d+)(\d)', f'b={pageno - 1}1') # IDK if this works with all pages over 10
          
          print("Navigating to " + goto_url)
          self.request(goto_url, absolute=True)

          self.parse()
          return pageno if pageno != "next" else int(self.dom.xpath(f"//div[@class='pages']/strong/text()")[0])
      except Exception as e:
          print("Could not navigate to page " + pageno)
          logging.exception('')

# Personal SearX instance
# Different from the main SearX because it supports json, so some limitations may be reduced?
# Haven't checked its effectiveness in comparison yet
# Default instance lives at searx.elijahmendoza.eu.org/searxng
# To get the authorization code, inspect the network requests when you log in to the instance with the username and password,
# then copy the Authorization: Bearer header stuff
# Lazy, only gets articles when you call the .articles() method
class PrivateSearx(NewsSource):
  name = "Private Searx"
  def __init__(self, search, *, authorization="", server="searx.elijahmendoza.eu.org/searxng", time_range = "", language = "en-US", engines = "bin,gon,ptsn,qwn,wn,yhn,bi,brave,ddg,gb,sp,yh", categories = "news,general", safesearch = 2):
    self.server = server
    self.pageno = 1 # internal tracking of this
    self.authorization = authorization
    self.search_opts = dict(time_range=time_range, language=language, engines=engines, categories=categories)
    super().__init__(search)
    # self.feeds = feeds

  def request(self, path, *, absolute=False):
    address = path if absolute else urljoin(f"https://{self.server}", path) 
    return httpx.get(address, headers={
        "Accept": "text/html,application/xhtml+xml,application/xml",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
        "Authorization": self.authorization
    })

ENGINES_BY_NAME = {engine.name: engine for engine in [GoogleAlerts, GoogleNewsSource, PrivateSearx, SearxSearch, YahooNews, GdeltSource, DdgNewsSource]}

class Aggregator(NewsSource):
  name = "Aggregator"
  def __init__(self, search):
    self.sources = []
    self.source_tasks = []
    self.all_articles = []
    self.hashes = set()
    super().__init__(search)
  #   self.search = search
  # #   self.searx_instance = SearxSearch(search, **searx_options)
  @staticmethod
  def from_engine_options(l: list, ENGINES_BY_NAME=ENGINES_BY_NAME):
    def reducer(agg, source_options):
      name, args, kwargs = source_options
      if type(name) == str:
        return agg.with_source(ENGINES_BY_NAME[name], *args, **kwargs)
      else:
        # It's a class
        engine = name
        return agg.with_source(engine, *args, **kwargs)

    def start(search_term):
      return reduce(reducer, l, Aggregator(search_term))
    return start

  def _is_unique_save(self, article):
    dup = article['url'] in self.hashes or str(article['title']) + str(article['body']) in self.hashes
    if (not dup):
      self.hashes.add(article['url'])
      self.hashes.add(str(article['title']) + str(article['body']))
    return not dup
  # TODO: parallelize
  def with_source(self, source_class, *, search = None, **kwargs):
    print(f"Adding source {source_class.name}...")
    self.sources.append(source_class(search or self.search, **kwargs))
    print("Done")
    return self # for chaining
  # The async version
  def add_source(self, source_class, *, search = None, **kwargs):
    print(f"Adding {source_class.name} to queue...")
    self.source_tasks.append(asyncio.create_task(asyncify(source_class)(search or self.search, **kwargs)))
    return self
  # Run all sources gathered *async function*
  async def register_sources(self):
    # Gather them all synchronously and add them
    # Because we live in sync-land
    print(f"Adding sources asynchronously...")
    new_sources = await tqdm_asyncio.gather(*self.source_tasks)
    self.sources += new_sources
    print("Done")
    return self

  async def _get_source_articles(self, source):
    try:
      # print(f"Getting articles from {source.name}")
      articles = await asyncify(source.articles)()
      # print(f"Got {len(articles)} from {source.name}")
      return articles
    except Exception as e:
      print(f"Source {source.name} raised an error {e}")
      return [] # :(
          
  # todo: add yandex and yahoo scrapers $x("//ul[@id='search-result']/li//div[contains(@class, 'OrganicContent')]") $x("//ul[@id='search-result']/li//h2[contains(@class, 'OrganicTitle-LinkText')]") $x("//ul[@id='search-result']/li//div[contains(@class, 'OrganicTitle')]/a/@href")
  # should memoize
  async def articles(self, sources = None):
    # print([s.articles() for s in self.sources])
    # todo: parallelize (done?)
    sources = sources or self.sources
    article_tasks = [asyncio.create_task(self._get_source_articles(s)) for s in sources]
    source_articles = await tqdm_asyncio.gather(*article_tasks)
    new_articles = [{**a, 'source_engine': s.name} for s, l in zip(sources, source_articles) for a in l]
    filtered_new_articles = [a for a in new_articles if self._is_unique_save(a)]
    # print(len(new_articles), len(filtered_new_articles))
    self.all_articles += filtered_new_articles
    return filtered_new_articles
  def next_page(self):
    for source in self.sources:
      source.next_page()
  async def juice_all_pages(self, cap=1000):
    zero_count = 0
    pageables = [] # list of engines that are "pageable"
    # TODO: parallelize and make this work. IT should be able to go through all pages and add them to the list, but quit if the source refuses to give any more or can't give anymore
    while zero_count < 3:
      try:
        # first run
        if len(pageables) == 0: # only if there are no pageables yet
          for s in self.sources:
            try:
              s.next_page()
              pageables.append(s)
            except NotImplementedError:
              continue
          if len(pageables) == 0: # if this is STILL the case then get out! Nothing to do here.
            return
        else: # succeeding runs
          for s in pageables:
            s.next_page()

        new_articles = await self.articles(pageables) # get the articles for the pageables only
        print(f"Aggregator: New articles {len(new_articles)}, total {len(self.all_articles)}") # logging, optional
        # throttle :(
        sleeptime = random.random() * (1 if len(new_articles) > 0 else 5)
        time.sleep(sleeptime)
        # counter that resets if source has given up
        if len(new_articles) == 0:
          zero_count += 1
        else:
          zero_count = 1
        
        # Break if the total number of articles goes above the cap
        if len(self.all_articles) > cap:
          break
      except Exception as e:
        logging.exception('')
        break
      except:
        print("ended")
        break

