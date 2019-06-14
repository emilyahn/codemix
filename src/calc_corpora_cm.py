#!/usr/bin/env python

""" Date created: 04/15/19
	Date modified: 04/15/19
	*************************
	calc CM #s from various corpora
	1. Taglish
		* Babel conversations
	2. Hinglish
		* Tweets for NER/LID - 2079 tweets (Singh+ 2018)

	To run:
		./calc_corpora_cm.py

"""
import os
import csv
import unidecode
from collections import defaultdict
# import re
# import sys


__author__ = 'Emily Ahn'


# load dictionaries
def load_lang_dict(filename):
	word_list = set()
	with open(filename, 'r') as fin:
		for line in fin.readlines():
			word = line.strip().decode('utf-8')
			word = unidecode.unidecode(word)
			word_list.add(word)

	return word_list


tg_list = load_lang_dict('data/word_lists/tg_1000_common.txt')
en_list = load_lang_dict('data/word_lists/en_1000_common.txt')
# en_list.intersection(tg_list)
# > set(['shop', 'simple', 'am', 'direct', 'single', 'at', 'yes', 'post', 'out', 'sun', 'mark', 'cell', 'track', 'window', 'board', 'notice', 'star', 'beauty', 'may', 'base', 'key', 'front', 'bit', 'center', 'natural', 'room', 'oh', 'up', 'o', 'rock', 'talk'])


def calc_singh_tweets(filename):
	with open(filename) as f:
		# total = [line.strip() for line in f.readlines()]
		list_of_tweets = []
		one_tweet = []
		for line in f.readlines():
			line = line.strip()
			if not line:  # end of tweet
				list_of_tweets.append(one_tweet)
				one_tweet = []
			else:
				one_tweet.append(line)

		for tweet_info in list_of_tweets:
			all_info = tweet_info.split('\t')
			# tweet_id = all_info[0]
			txt = all_info[0]
			lbl = all_info[1]

			if lbl == 'en':  # ENG
				word_01 = 1
			elif lbl == 'hi':  # SPA
				word_01 = 0
			else:  # other: 'rest'
				word_01 = 2


# 0 = TG, 1 = EN, 2 = other
# can change default check of word list: TG or EN (comment out accordingly)
def calc_babel_taglish(babel_dir):
	counts_dict = defaultdict(int)
	# default TG {0: 166,113, 1: 12,802, 2: 421,111}
	# default EN {0: 155,295, 1: 23,620, 2: 421,111}
	words_dict = defaultdict(set)
	# num uniq words~ tg: 557 en: 608 other: 23,264
	for filename in os.listdir(babel_dir):
		filename_path = os.path.join(babel_dir, filename)
		file_id = os.path.splitext(filename)[0]

		num_utts = 0
		num_cm_utts = 0

		with open(filename_path) as f:
			all_lines = [line.strip() for line in f.readlines()]
			for line in all_lines:
				if line.startswith('[') or line == '<no-speech>':  # timestamp or other
					continue

				lang_cts = [0, 0, 0]
				num_utts += 1
				for word in line.split():
					if word.startswith('<'):
						continue

					hypothesis_01 = 2
					# DEFAULT = TAG
					if word in tg_list:
						hypothesis_01 = 0
					elif word in en_list:
						hypothesis_01 = 1
					# DEFAULT = ENG
					# if word in en_list:
					# 	hypothesis_01 = 1
					# elif word in tg_list:
					# 	hypothesis_01 = 0

					counts_dict[hypothesis_01] += 1
					words_dict[hypothesis_01].add(word)
					lang_cts[hypothesis_01] += 1

				if lang_cts[0] > 0 and lang_cts[1] > 0:
					num_cm_utts += 1
					print line

		if num_utts == 0:
			perc = 0
		else:
			perc = float(num_cm_utts) / num_utts
		# print num_cm_utts, num_utts, perc


def process_reddit(reddit_file):
	tg_reddit = []
	reader = csv.DictReader(open(reddit_file, 'r'), delimiter=',')
	for row in reader:
		if row['Lang1'] == 'Tagalog' or row['Lang2'] == 'Tagalog':
			tg_reddit.append(row['Text'])

	import pdb; pdb.set_trace()


if __name__ == '__main__':
	# calc_singh_tweets('data/hi_singh_tweets.tsv')
	# calc_babel_taglish('data/babel_tag_trans')
	process_reddit('data/reddit_cs.csv')
