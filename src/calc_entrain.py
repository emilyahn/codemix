# -*- coding: utf-8 -*-

""" Date created: 06/25/2019
	Date modified: 06/28/2019
	*************************
	Entrainment metrics
	* Interchangeable items
		* Language pair
			* Corpus
			* Subset of users (by style / demographics)
		* Scores: Metric equation
		* Lexicon: groups of words (features)
		* Language ID tool

	To run (from codemix/):
		./src/calc_entrain.py

"""
from __future__ import division
import re
import langid
# import os
from collections import defaultdict  # Counter
# from itertools import groupby
from src import parse_miami
from src import cm_metrics


__author__ = 'Emily Ahn'


class ConvData():

	def __init__(self, infile_name='./data/miami/clean_1208', corp_name='miami', lang_pair='es-en'):
		# format uttid: '[corp_name]_[dialog_id]_[utt_num]_[spkr]''
		self.texts = {}  # [uttid] = list(words)
		self.lid_labels = {}  # [uttid] = list(language ID tags among {0,1,2})
		self.cm_styles = {}
		self.dialog_uttids = defaultdict(list)
		self.dialog_spkrs = defaultdict(list)
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
		for dialog_id, dialog_dict in full_dict.iteritems():
			if not dialog_id == 'zeledon8': continue  #debug w/ 1 dialog only
			if len(dialog_dict) != 2:  # must have exactly 2 speakers
				continue

			# utt_to_info = defaultdict(dict) # if want to save other info too
			for spkr, spkr_dict in dialog_dict.iteritems():
				# per 1 turn of speech
				self.dialog_spkrs[dialog_id].append(spkr)
				last_turn = -2
				last_uttid = ''
				for line_i, line in enumerate(spkr_dict['words_01']):
					# format of utt_id:
					# 'mi_{}_{}_{}'.format(dialog_id, turn_num, spkr)
					utt_id = spkr_dict['uttid'][line_i]
					turn_num = spkr_dict['turn_num'][line_i]  # int

					words = cm_metrics.remove_lidtags_miami(spkr_dict['words'][line_i])
					# if consecutive spkr, merge
					#TODO: maybe delineate contiguous utts with '|' or '.'
					if last_turn + 1 == turn_num:
						self.texts[last_uttid].extend(words)
						self.lid_labels[last_uttid].extend(line)  # list of [0,1]s
					else:
						self.texts[utt_id] = words
						self.lid_labels[utt_id] = line  # list of [0,1]s
						last_uttid = utt_id
						self.dialog_uttids[dialog_id].append(utt_id)

					last_turn = turn_num

			self.dialog_uttids[dialog_id] = sorted(self.dialog_uttids[dialog_id])

	def load_com_amig(self, infile_name):
		pass

	def load_reddit(self, infile_name):
		pass

	def detect_lang(self, tool_name, word_str):
		langid.set_languages(self.langs)  # e.g. ['es', 'en']


class Lexicon():

	def __init__(self, infile_name='./data/word_lists/en_aux.txt'):
		with open(infile_name, 'r') as f:
			self.words = [line.strip() for line in f.readlines()]

		self.rgx_words = [re.compile(r'\b{}\b'.format(entry)) for entry in self.words]

	# given text = list of words, return matched items
	def in_text_list(self, text_list):
		matches = []
		for word in self.words:
			counts = text_list.count(word)
			if counts > 0:
				matches.extend([word] * counts)

		return matches

	# given text = str of words, return regex-matched items
	def in_text_longstr(self, text_str):
		matches = []
		for rgx_word in self.rgx_words:
			matches.extend(re.findall(rgx_word, text_str))

		return matches


class Scores():

	def __init__(self, conv_data, lexicon):
		self.scores = defaultdict(dict)
		self.data = conv_data
		self.lex = lexicon
		self.word_list = lexicon.words

		# self.calc_dnm()
		# self.calc_msr()
		# self.calc_naist()
		# self.calc_soto()

	# self.scores['dnm'][spkr1] = how much spkr1 (replier) entrained to spkr2
	# self.scores['dnm'][spkr2] = how much spkr2 (replier) entrained to spkr1
	# returns (full score, term1 of eqn = minuend, term2 of eqn = subtrahend)
	def calc_dnm(self, given_dialogid=None, calc_ratio=False):
		""" Danescu-Niculescu-Mizil et al. (2011) Entrainment, WWW
			* = P(ft in reply utt from SPK-2 / ft in previous utt from SPK-1)
				- P(ft in reply utt from SPK-2 / all replies to SPK-1)

			* Does not factor high-level temporal nature (e.g. start vs end of dialogue)
		"""
		#TEST: 1 dialogue
		dialog_id = 'zeledon8'
		spkrs = ['MAR', 'FLA']
		# if not given_dialogid:
		# for dialog_id, spkrs in self.conv_data.dialog_spkrs.iteritems():

		# calc in both directions simultaneously
		spkr1, spkr2 = spkrs
		ft_in_reply = {spkr1: 0, spkr2: 0}
		ft_in_prev = {spkr1: 0, spkr2: 0}
		ft_in_reply_and_prev = {spkr1: 0, spkr2: 0}
		spkr_reply_cts = {spkr1: 0, spkr2: 0}
		# uttid_matches = {}

		uttid_prev = self.data.dialog_uttids[dialog_id][0]
		words_prev = self.data.texts[uttid_prev]
		matches_prev = self.lex.in_text_list(words_prev)
		for utt_id in self.data.dialog_uttids[dialog_id][1:]:
			spkr_reply = utt_id.split('_')[-1]
			spkr_reply_cts[spkr_reply] += 1
			spkr_prev = uttid_prev.split('_')[-1]
			words_reply = self.data.texts[utt_id]
			matches_reply = self.lex.in_text_list(words_reply)

			if not calc_ratio:
				# variation 1: ft = 1 if any present in text
				if matches_reply:
					ft_in_reply[spkr_reply] += 1
					# AND
					if matches_prev:
						ft_in_reply_and_prev[spkr_reply] += 1
				if matches_prev:
					ft_in_prev[spkr_prev] += 1

			else:
				# variation 2: ft = proportion of tokens (e.g. 3 aux / 10 words = .3)
				if matches_reply and words_reply:  # require non-empty list of words
					ft_in_reply[spkr_reply] += len(matches_reply) / len(words_reply)
					# AND
					if matches_prev and words_prev:
						# take ratio of reply only, not prev (logic may be flawed)
						ft_in_reply_and_prev[spkr_reply] += len(matches_reply) / len(words_reply)
				if matches_prev and words_prev:
					ft_in_prev[spkr_prev] += len(matches_prev) / len(words_prev)

			# import pdb; pdb.set_trace()
			# update variables
			uttid_prev = utt_id
			words_prev = words_reply
			matches_prev = matches_reply

		# scores in 1 direction
		def calc_a_entrained_to_b(spkr_a, spkr_b):
			term1 = 0
			term2 = 0

			if ft_in_prev[spkr_b] > 0:
				term1 = ft_in_reply_and_prev[spkr_a] / ft_in_prev[spkr_b]
			if spkr_reply_cts[spkr_a] > 0:
				term2 = ft_in_reply[spkr_a] / spkr_reply_cts[spkr_a]

			return (term1 - term2, term1, term2)

		self.scores['dnm'][spkr1] = calc_a_entrained_to_b(spkr1, spkr2)
		self.scores['dnm'][spkr2] = calc_a_entrained_to_b(spkr2, spkr1)

	def calc_msr(self):
		""" Bawa et al. (2018) Accommodation of Code-choice in Miami, ACL
		"""
		self.scores['msr'] = 0

	def calc_naist(self):
		""" Mizukami et al. (2016), SIGdial
			Modified Nenkova (2008), add smoothing
		"""
		self.scores['naist'] = 0

	def calc_soto(self):
		""" Soto et al. (2018), Interspeech
			* Pearson r of convergence of “each speakers’ CS ratio for each speaker turn”
			* CS ratio = total # of CS normalized by total # of tokens
			* # of CS = # switch points in an utterance
		"""
		self.scores['soto'] = 0


def main():
	miami = ConvData(infile_name='./data/miami/clean_1208', corp_name='miami', lang_pair='es-en')
	# en_aux_lex = Lexicon(infile_name='./data/word_lists/en_aux.txt')
	en_aux_lex = Lexicon(infile_name='./data/word_lists/en_fw_1_list.txt')
	scores = Scores(miami, en_aux_lex)
	scores.calc_dnm(calc_ratio=False)
	print('NO RATIO', scores.scores['dnm'])
	scores.calc_dnm(calc_ratio=True)
	print('RATIO', scores.scores['dnm'])
	# import pdb; pdb.set_trace()


if __name__ == '__main__':
	main()
