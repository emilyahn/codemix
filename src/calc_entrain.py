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


__author__ = 'Emily Ahn'

with open('./src/ignore_words.txt') as f:
	ignore_words = [line.replace('\n', '') for line in f.readlines()]


class ConvData():

	def __init__(self, infile_name='./data/miami/clean_1208', corp_name='miami', lang_pair='en-sp'):
		self.texts = {}
		self.lid_labels = {}
		self.cm_styles = {}
		self.dialog_ids = []
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
			if len(dialog_dict) < 2:
				dialog_ids.remove(dialog_id)
				continue

			utt_ids = []
			for spkr, spkr_dict in dialog_dict.iteritems():
				# 1 turn of speech
				for line_i, line in enumerate(spkr_dict['words_01']):
					turn_num = spkr_dict['turn_num'][line_i]  # int
					# orig format of spkr_dict['uttid':
					# 'mi_{}_{}_{}'.format(dialog_id, spkr, turn_i)
					# update turn_i to actual turn_num
					pieces = spkr_dict['uttid'].split('_')[:-1]
					pieces.append(str(turn_num).zfill(4))
					utt_id = '_'.join(pieces)
					utt_ids.append(utt_id)

		self.dialog_ids = dialog_ids


class Lexicon():
	pass


def main():
	miami = ConvData(infile_name='./data/miami/clean_1208', corp_name='miami', lang_pair='en-sp')
	import pdb; pdb.set_trace()


if __name__ == '__main__':
	main()