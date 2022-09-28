# Scrape some documents
# TODO: fix translation
# TODO: make it more performant (actually limiting articles)
# TODO: indicate progress
# TODO: because this takes >2 minutes each run, there should be a list of "jobs" and a queue from where anyone who submits a job can find and download their scrapes once they're complete.
# We need to make this actually allow downloads
# TODO: code style fix. It's really ugly right now

# Asyncio loop error was fixed by removing all the "asyncio.run" and related statements while wrapping scraper_pre into its own function

from .scraper_pre import get_df_from_search_terms
import dateparser
from langdetect import detect
from translate import Translator
from google_trans_new import google_translator
import googletrans
from functools import wraps, partial
# import nest_asyncio
import asyncio
from tqdm.asyncio import tqdm_asyncio
from tqdm import tqdm
import time
from newspaper import Article
from sklearn.feature_extraction.text import TfidfVectorizer
import string
from uclassify import uclassify
from operator import methodcaller
# from os import path
# import pickle
from datetime import datetime, timedelta, timezone
# from urllib.parse import urlparse
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
# from nltk.stem import WordNetLemmatizer
# from nltk import tokenize
import re
import spacy
# python -m spacy download en_core_web_sm #if this fails
en = spacy.load("en_core_web_sm")
#from google.colab import files

# For async
from apps.utils.asyncify import asyncify, timer_start, timer_end

# For translation


async def scraper_function(search_terms, start_date, end_date):
    # get_all_values gives a list of rows.
    # df = pd.read_csv("./dummy.csv", names=['Original_Title', 'Original_URL', 'Date', 'Summary'])
    print("Loading dataframe")
    df = await get_df_from_search_terms(search_terms)  # ['elon musk'])

    def trace(f):
        def traced(*args, **kwargs):
            print(*args, **kwargs)
            return f(*args, **kwargs)
        return traced

    # @title Last week-only dataframe
    def last_week_only(df):
        # selecting values from a week ago
        today = datetime.now(timezone.utc)
        last_week = today - timedelta(days=7)
        df = df.copy()
        df = df[df['Date'].apply(methodcaller('timestamp'))
                > last_week.timestamp()]
        df.reset_index(drop=True, inplace=True)
        return df

    def filter_date_range(df, start_date, end_date):
        # selecting values from a week ago
        df = df.copy()
        dates = df['Date'].apply(methodcaller('timestamp'))
        df = df[(start_date.timestamp() < dates) & (dates < end_date.timestamp())]
        df.reset_index(drop=True, inplace=True)
        return df

    # Preprocess JUST a df
    def preprocess_df(df):
        df = df.copy()
        # removing any blank values to avoid errors
        df = df.replace(r'^\s*$', float('NaN'), regex=True)
        df = df.dropna(how='any', subset=[
                       'Original_Title', 'Original_URL', 'Date', 'Summary'])

        df['Date'] = df['Date'].apply(
            partial(dateparser.parse, settings={'TIMEZONE': 'UTC'}))
        df = df.dropna(how='any', subset=['Date'])

        return filter_date_range(df, start_date, end_date)

    print("Preprocessing dataframe")
    df = preprocess_df(df)

    # @title Setting up async

    # prep for async
    # nest_asyncio.apply()

    # @title googletrans integration

    # function recieves source_text
    #   if it isn't english it will return the english translation
    def translate(source_text, *, dest='en'):
        try:
            translator = googletrans.Translator()
            source_lang = translator.detect(source_text).lang
            if source_lang != "en":
                final_text = translator.translate(source_text, dest=dest).text
            print("used googletrans")
            return final_text
        except:
            try:
                translator = google_translator()
                final_text = translator.translate(source_text, lang_tgt=dest)
                print('used google_trans_new')
                return final_text
            except:
                from_lang = detect(source_text)
                # TODO: Make this work for any language
                machine = Translator(from_lang=from_lang, to_lang='English')
                final_text = machine.translate(source_text)
                print('used translator')
                return final_text

    #print(translate("bonjour, je m'appelle david et je suis americain. j'aime les hamburgers."))
    #print(translate("Hola, me llamo Santiago. Soy de los Estados Unidos. Me gustan las hamburguesas."))

    # @title Utilities for cleaning text
    # todo: I need to edit the capitalization code so that 'S' doesn't end up capitalized at the end of words
    # and to make sure it complies with VG standards

    # standardizing capitalization
    def truecase(title):

        # if all the words are capitalized, we capitalize the first letter of each word
        # and leave the other letters lowercase
        if title.isupper():
            return title.title()

        # if some words are uppercase (acronyms) while others aren't,
        # we'll leave the acronyms as they are and capitalize the first letter of every other word
        else:
            return " ".join([word if word.isupper() else word.title() for word in re.split("\s+", title)])

    # Standardizing title spacing and capitalization
    def clean_title(title):
        # Cleaning cruft
        title = re.sub(r"\s+", " ", title)
        title = re.sub(r" ([:;,\.?!\-\)]|\%:)", r"\1", title)
        title = re.sub(r"([\-\(\/]) ", r"\1", title)
        title = re.sub('<b>|</b>', '', title)
        # title = re.sub(r"", r"\1", title)

        # standardizing capitalization
        return truecase(title)

    # standardizing urls
    def clean_url(url):
        return url
        # try:
        #   split_url = re.split('&url=|/?&ct=', url)
        #   clean_url = split_url[1]
        #   return clean_url
        # except:
        #   return url

    # creating a function to do all of our text cleaning at once. Now our text will be standardized, making it easier to compare with other texts.
    def preprocess_text(text, doc=None):
        if doc is None:
            doc = en(text)
        # returning string of cleaned text
        return [token.lemma_.lower() for token in doc if not (token.is_digit or token.is_stop or token.is_punct)]

    def preprocess_texts(texts):
        pipeline = en.pipe(texts, disable=["tok2vec", "parser", "ner"])
        return [" ".join(preprocess_text(None, doc)) for doc in pipeline]

    # @title Identifying duplicate titles
    print("Deduplicating dataframe")
    # creating lists of columns. will be used to create dataframe with unique titles
    urls = df["Original_URL"]
    dates = df["Date"]
    titles = df["Original_Title"]
    summaries = df['Summary']

    # Cleaning titles
    titles = titles.map(clean_title)

    # Deduplicating titles
    unique_titles = []
    unique_urls = []
    unique_dates = []
    unique_summaries = []

    for t, u, d, s in zip(titles, urls, dates, summaries):
        if t not in unique_titles and u not in unique_urls:
            unique_titles.append(t)
            unique_urls.append(u)
            unique_dates.append(d)
            unique_summaries.append(s)

    # creating extra dictionary for unique values
    dataframe = pd.DataFrame({"Unique_Titles": unique_titles, "Unique_Dates": unique_dates,
                             "Original_URLs": unique_urls, "Unique_Summaries": unique_summaries})
    # adding column of translated titles
    #print(dataframe.apply(lambda row: translate(row.Unique_Titles), axis=1))
    # dataframe.apply(lambda row: translate(row.Unique_Titles), axis=1)
    dataframe['Translated_Title'] = dataframe['Unique_Titles']

    # adding column of cleaned urls
    dataframe['URL'] = dataframe.apply(
        lambda row: clean_url(row.Original_URLs), axis=1)

    # initializing count vectorizer function
    vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2))

    # calling tfidf vectorizer
    tfidf_matrix = vectorizer.fit_transform(
        preprocess_texts(dataframe["Unique_Titles"]))

    # creating dense matrix
    title_term_matrix = tfidf_matrix.todense()

    # creating pandas data frame out of matrix
    title_data = pd.DataFrame(title_term_matrix)
    # calculating cosine similarity, which measures the angle between two document vectors to calculate similarity. Check out https://www.machinelearningplus.com/nlp/cosine-similarity/ for more of the math
    title_cos_sim = cosine_similarity(title_data, title_data)

    # creating dataframe  out of cos similarity matrix
    DF = pd.DataFrame(title_cos_sim, columns=unique_titles)

    removed_duplicate_indexes = []
    alt_urls = dict()

    for i, a in tqdm(enumerate(unique_titles)):
        # Find all duplicates: similarity > 0.8, nothing is a duplicate of itself,
        # and we can ignore the duplicates whose matches have already been removed
        duplicates = DF.drop([i]+removed_duplicate_indexes)
        duplicates = duplicates[duplicates[a] > 0.30]
        if not duplicates.empty:
            # print(
            #     f"Eliminating #{i} - {a[:10]}... because it's a duplicate of #{duplicates.index[0]} - {unique_titles[duplicates.index[0]][:10]}...")

            # Add this to the list of alternative urls for later
            # used url as key rather than title. should make it easier to pass into scraper function
            if a not in alt_urls:
                a_url = dataframe["URL"][duplicates.index[0]]
                # print(a_url)
                alt_urls[a_url] = []
            alt_urls[a_url].append(dataframe["URL"][i])

            removed_duplicate_indexes.append(i)

    print(f"Total: {len(removed_duplicate_indexes)} duplicates removed")

    # adding in all other urls to alt_urls list so we don't end up with key errors
    for url in dataframe["URL"]:
        if url not in alt_urls:
            alt_urls[url] = [url]
    dataframe = dataframe.drop(removed_duplicate_indexes)

    # # @title Scraping URLs
    # # @markdown Note: This might take 10-20 minutes to run.
    # async def list_scraper(url_list, semaphore: asyncio.Semaphore):
    #     list_length = len(url_list)
    #     url_tasks = [asyncio.create_task(scraper(url, semaphore)) for url in url_list]
    #     for task in url_tasks:
    #         results = await task
    #         print("Scraping urls", url_list)
    #         if results[0] != "Text not scraped. Check url.":
    #             return results
    #         elif url_list.index(url) == list_length - 1:
    #             return results
    #         else:
    #             continue

    # # Asyncify the scraper
    # async def scraper(url, semaphore: asyncio.Semaphore):
    #     async with semaphore:
    #         try:
    #             # scraping with Newspaper library
    #             article = Article(url)
    #             article.download()
    #             article.parse()
    #             # nlp not used in this iteration of the code
    #             # article.nlp()
    #         except:
    #             pass

    #         article_text = article.text
    #         # checking to make it worked properly & leaving a note for the end user if not.
    #         if not article_text:
    #             article_text = "Text not scraped. Check url."

    #         # storing author name in "authors" variable. The .authors property returns a list.
    #         author = article.authors

    #         # turning list into a string
    #         authors = ""
    #         for i in author:
    #             authors += i
    #             authors += ", "

    #         # checking to make it worked properly & leaving a note for the end user if not.
    #         if not authors:
    #             authors = "Author not scraped. Check url."
    #         return (article_text, authors)

    # # Create a list of tasks to run in parallel
    # async def scrape_all_alts(dataframe, alt_urls):

    #     timer_start("article_scraping")
    #     semaphore = asyncio.Semaphore(value=1)
    #     scraping_tasks = [asyncio.create_task(
    #         list_scraper(alt_urls[url], semaphore)) for url in dataframe["URL"]]

    #     # Run them
    #     print(f"Scraping {len(scraping_tasks)} URLs")
    #     # Por debuggar
    #     # from tqdm.asyncio import tqdm_asyncio
    #     scraping_results = await asyncio.gather(*scraping_tasks)
    #     timer_end("article_scraping")

    #     return scraping_results

    # async def add_scraping_data(dataframe, alt_urls):
    #     dataframe = dataframe.copy()
    #     scraping_results = await scrape_all_alts(dataframe, alt_urls)
    #     # extract text and authors from the results
    #     dataframe["Text"], dataframe["Authors"] = zip(*scraping_results)
    #     return dataframe

    # # Run them
    # dataframe = await add_scraping_data(dataframe, alt_urls)

    # @title Running scraper and translating text
    # @markdown Note: This might take 10-20 minutes to run.

    @asyncify
    def list_scraper(url_list):
        list_length = len(url_list)
        for url in url_list:
            results = scraper(url)
            if results[0] != "Text not scraped. Check url.":
                return results
            elif url_list.index(url) == list_length - 1:
                return results
            else:
                continue
    timer_start("article_scraping")

    # Asyncify the scraper
    def scraper(url):
        try:
            # scraping with Newspaper library
            # print('Downloading', url)
            article = Article(url)
            article.download()
            # print('Downloaded', url)
            article.parse()
            # nlp not used in this iteration of the code
            # article.nlp()
        except:
            pass

        article_text = article.text
        # checking to make it worked properly & leaving a note for the end user if not.
        if not article_text:
            article_text = "Text not scraped. Check url."

        # storing author name in "authors" variable. The .authors property returns a list.
        author = article.authors

        # turning list into a string
        authors = ""
        for i in author:
            authors += i
            authors += ", "

        # checking to make it worked properly & leaving a note for the end user if not.
        if not authors:
            authors = "Author not scraped. Check url."
        return (article_text, authors)

    # Create a list of tasks to run in parallel
    scraping_tasks = [list_scraper(alt_urls[url]) for url in dataframe["URL"]]

    # Run them
    print(f"Scraping {len(scraping_tasks)} URLs")
    scraping_results = await tqdm_asyncio.gather(*scraping_tasks)
    # scraping_results = await asyncio.gather(*scraping_tasks) # plain version
    timer_end("article_scraping")

    # extract text and authors from the results
    dataframe["Text"], dataframe["Authors"] = map(
        tuple, zip(*scraping_results))

    # adding column of translated titles
    # dataframe.apply(lambda row: translate(row.Text), axis=1)
    dataframe['Translated_Text'] = dataframe['Text']

    # @title Analyzing articles for similarity and deleting duplicates
    # @param { type:"slider", min:0, max:1, step:0.1 }
    similarity_threshold = 0.15
    # @markdown Similarity scores higher than this will be considered duplicates

    # initializing count vectorizer function
    vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 1))

    # calling tfidf vectorizer
    tfidf_matrix = vectorizer.fit_transform(
        preprocess_texts(dataframe["Translated_Text"]))

    # creating dense matrix
    text_term_matrix = tfidf_matrix.todense()

    # creating pandas data frame out of matrix
    text_data = pd.DataFrame(text_term_matrix)
    # calculating cosine similarity, which measures the angle between two document vectors to calculate similarity. Check out https://www.machinelearningplus.com/nlp/cosine-similarity/ for more of the math
    text_cos_sim = cosine_similarity(text_data, text_data)

    # creating list of titles to cycle through
    unique_titles = [c for c in dataframe["Unique_Titles"]]

    # creating dataframe  out of cos similarity matrix
    DF = pd.DataFrame(text_cos_sim, columns=unique_titles)

    removed_duplicate_indexes = []

    for i, a in tqdm(enumerate(unique_titles)):
        # Find all duplicates: similarity > 0.8, nothing is a duplicate of itself,
        # and we can ignore the duplicates whose matches have already been removed
        duplicates = DF.drop([i]+removed_duplicate_indexes)
        duplicates = duplicates[duplicates[a] > similarity_threshold]
        if not duplicates.empty:
            # print(
            #     f"Eliminating #{i} - {a[:20]}... because it's a duplicate of #{duplicates.index[0]} - {unique_titles[duplicates.index[0]][:20]}...")

            removed_duplicate_indexes.append(i)

    print(f"Total: {len(removed_duplicate_indexes)} duplicates removed")

    # resetting index
    dataframe.reset_index(drop=True, inplace=True)

    # removing duplicate indexes
    dataframe = dataframe.drop(removed_duplicate_indexes)
    dataframe.reset_index(drop=True, inplace=True)

    # @title Classifying articles by category
    # creating uclassify object
    a = uclassify()

    # api key
    try:
        a.setReadApiKey("dUofd9VRSPE4")
        texts = [article for article in dataframe["Translated_Text"]]
        classified = a.classify(texts, "VG_classifier")

    # backup
    except:
        a.setReadApiKey('aRvEAOo71xQd')
        texts = [article for article in dataframe["Translated_Text"]]
        classified = a.classify(texts, "VG_classifier")

    # preparing for csv export
    confidences = []
    categories_list = []
    for i in classified:
        text = i[0]
        confidence = i[1]
        categories = i[2]
        confidences.append(confidence)
        categories_list.append(categories)

    best_match_categories = []
    for category_list in categories_list:
        l_float = [(name, float(weight)) for name, weight in category_list]
        best_match_category = max(l_float, key=lambda t: t[1])[0]
        best_match_categories.append(best_match_category)

    dataframe["Category"] = best_match_categories
    dataframe["Confidence"] = confidences
    dataframe['Categories'] = categories_list

    # @title Creating & Downloading csv file
    # today = datetime.today().date()

    # creating a title
    # title = f'VG_Webscraping_{today}.csv'
    # # creating csv file
    # dataframe.to_csv(title, encoding="utf8", index=False)
    # files.download(title)

    # print(dataframe)
    print("Scraping done")
    return dataframe

# Just run it™
# asyncio.run(scraper_function(["donald trump"]))
