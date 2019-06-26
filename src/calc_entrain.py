#!/usr/bin/env python

""" Date created: 06/25/2019
	Date modified: 06/25/2019
	*************************
	Entrainment metrics
	* Interchangeable items
		* Language pair
			* Corpus
			* Subset of users (by style / demographics)
		* Metric equation
		* Groups of words (features)
		*

	To run (from codemix/):
		./src/calc_entrain.py

"""
import os
import re
import sys
from collections import defaultdict, Counter
from itertools import groupby
from src import parse_miami
from src import cm_metrics


__author__ = 'Emily Ahn'

with open('./src/ignore_words.txt') as f:
	ignore_words = [line.replace('\n', '') for line in f.readlines()]


class ConvData():

	def __init__(self, infile_name='./data/miami/clean_1208', corp_name='miami', lang_pair='en-sp'):
		self.texts = {}
		self.lid_labels = {}
		self.cm_styles = {}
		self.dialog_ids = set()
		self.langs = [lang_pair.split('-')[0], lang_pair.split('-')[1]]  # assumes perfect format

		if corp_name == 'miami':
			self.load_miami(infile_name)
		elif corp_name == 'com_amig':
			self.load_com_amig(infile_name)
		elif corp_name == 'reddit':
			self.load_reddit(infile_name)
		else:
			raise Exception('Must specify valid corpus name.')

	def load_miami(self, infolder):
		full_dict = parse_miami.load_data(infolder)
		dialog_ids = set(full_dict.keys())
		for dialog_id, dialog_dict in full_dict.iteritems():
			if len(dialog_dict) < 2:  # less than 2 speakers
				dialog_ids.remove(dialog_id)
				continue

			# utt_ids = []
			# utt_to_info = defaultdict(dict)
			for spkr, spkr_dict in dialog_dict.iteritems():
				# per 1 turn of speech
				for line_i, line in enumerate(spkr_dict['words_01']):
					# format of utt_id:
					# 'mi_{}_{}_{}'.format(dialog_id, turn_num, spkr)
					utt_id = spkr_dict['uttid']
					# turn_num = spkr_dict['turn_num'][line_i]  # int
					# utt_ids.append(utt_id)
					# utt_to_info[utt_id]['words'] = spkr_dict['words'][line_i]  # has tags
					# utt_to_info[utt_id]['lbls'] = line
					words = spkr_dict['words'][line_i]  # has tags
					self.texts[utt_id] = cm_metrics.remove_lidtags_miami(words)
					self.lid_labels[utt_id] = line  # list of [0,1]s

		self.dialog_ids = dialog_ids

	def load_com_amig(self, infile_name):
		pass

	def load_reddit(self, infile_name):
		pass


class Lexicon():

	def __init__(self, infile_name='./data/word_lists/en_aux.txt'):
		with open(infile_name, 'r') as f:
			self.words = [line.strip() for line in f.readlines()]


class Scores():

	def __init__(self, conv_data, lexicon):
		self.scores = {}
		self.data = conv_data
		self.word_list = lexicon.words

		self.calc_dnm()
		self.calc_msr_lid()
		self.calc_sigdial()

	def calc_dnm(self):
		self.scores['dnm'] = 0

	def calc_msr_lid(self):
		self.scores['msr'] = 0

	def calc_sigdial(self):
		self.scores['sigdial'] = 0


def main():
	miami = ConvData(infile_name='./data/miami/clean_1208', corp_name='miami', lang_pair='en-sp')
	import pdb; pdb.set_trace()


if __name__ == '__main__':
	main()