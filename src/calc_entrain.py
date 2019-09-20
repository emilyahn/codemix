# -*- coding: utf-8 -*-

""" Date created: 06/25/2019
	Date modified: 08/28/2019
	*************************
	Entrainment metrics
	* Interchangeable items
		* Language pair
			* Corpus
			* Subset of users (by style / demographics)
		* Scores: Metric equation
		* Lexicon: groups of words (features)

	To run (from codemix/):
		python ./src/calc_entrain.py

"""
from __future__ import division
import re
# import langid
import numpy as np
import pandas as pd
import os
from collections import defaultdict, Counter
# from itertools import groupby
from src import parse_miami
from src import cm_metrics
from src import calc_cocoa


__author__ = 'Emily Ahn'


# 'neither' category = -1
lang_map = {'es': 0, 'en': 1, 'tg': 2, 'na': -1}
lang3_map = {'spa': 0, 'eng': 1, 'tgl': 2, 'not': -1}


class ConvData():

	def __init__(self, infile_name='./data/miami/clean_1208', corp_name='miami', lang_pair='spa-eng'):
		# format uttid: '[corp_name]_[dialog_id]_[utt_num]_[spkr]''
		self.texts = {}  # [uttid] = list(words)... no trailing LID tags
		self.lid_labels = {}  # [uttid] = list(language ID tags among {0,1,2})
		self.cm_styles = {}
		self.dialog_uttids = defaultdict(list)  # [dialog_id] = list(utt_ids)
		self.dialog_spkrs = defaultdict(list)  # [dialog_id] = list([spkr1, spkr2])
		self.langs = [lang_pair.split('-')[0], lang_pair.split('-')[1]]  # assumes perfect format

		if corp_name == 'miami':
			self.load_miami(infile_name)
		elif corp_name == 'com_amig':  # 437 chats (-100 mono)
			self.load_com_amig(infile_name)
		elif corp_name == 'reddit':
			self.load_reddit(infile_name)
		elif corp_name == 'babel':
			self.load_babel(infile_name)
		else:
			raise Exception('Must specify valid corpus name.')

		print 'loaded', corp_name

	# helper
	# convert neither tag '2' -> '-1'
	# line = list(int) in range [0, 2]
	def change_spa_neither_tag(self, line):
		no_2_line = []
		for lid_label in line:
			if lid_label == 2:
				no_2_line.append(-1)
			else:
				no_2_line.append(lid_label)

		return no_2_line

	# helper
	# convert tags in str form (e.g. 'eng', 'tgl', 'spa') to int w/ map
	def get_tags_int(self, text):
		tags_str = [word.split('_')[-1] for word in text]
		tags_int = []
		for tag_str in tags_str:
			if tag_str in self.langs:
				tags_int.append(lang3_map[tag_str])
			else:  # ella has more fine-grained tags for neither (uni, ambiguous lang, unk)... we could make use of this in the future
				tags_int.append(-1)

		return tags_int


	def load_miami(self, infolder):
		full_dict = parse_miami.load_data(infolder)
		for dialog_id, dialog_dict in full_dict.iteritems():
			# if not dialog_id == 'zeledon8': continue  #debug w/ 1 dialog only
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
					# if utt_id.split('_')[-1] != spkr:
					# 	print utt_id, spkr
					turn_num = spkr_dict['turn_num'][line_i]  # int

					words = cm_metrics.remove_lidtags_miami(spkr_dict['words'][line_i])
					# if consecutive spkr, merge
					#TODO: maybe delineate contiguous utts with '|' or '.'
					no_2_line = self.change_spa_neither_tag(line)
					if last_turn + 1 == turn_num:
						self.texts[last_uttid].extend(words)
						self.lid_labels[last_uttid].extend(no_2_line)  # list of [0,1]s
					else:
						self.texts[utt_id] = words
						self.lid_labels[utt_id] = no_2_line  # list of [0,1]s
						last_uttid = utt_id
						self.dialog_uttids[dialog_id].append(utt_id)

					last_turn = turn_num

			# ensure order
			self.dialog_uttids[dialog_id] = sorted(self.dialog_uttids[dialog_id])

	def load_com_amig(self, infile_name):
		com_data = calc_cocoa.load_all_data('./src/files_list_fix.txt')
		bot_data = calc_cocoa.load_all_data('./src/files_list_bot.txt')
		problem_ctr = 0
		invalid_ctr = 0

		for chat_id, usr_dict in com_data.iteritems():
			#check
			if chat_id not in bot_data:
				# print 'problem', chat_id
				problem_ctr += 1
				continue

			if 'outcome' not in usr_dict or 'txt_dict' not in usr_dict:
				# print 'not valid', chat_id
				invalid_ctr += 1
				continue

			turns = usr_dict['all_chat']
			#following check doesn't catch, can remove
			if len(turns) != len(usr_dict['lbl_dict']) + len(bot_data[chat_id]['lbl_dict']):
				print 'bot + user != all_chat', chat_id
				continue

			usr_idx = 0 if usr_dict['agents']['0'] == 'human' else 1
			absolute_turns = {'user': [], 'bot': []}
			for turn_i, turn in enumerate(turns):
				if turn[0] == usr_idx:
					absolute_turns['user'].append(turn_i)
				else:
					absolute_turns['bot'].append(turn_i)

			# create proper (absolute) utt_ids, populate class dicts
			new_chat_id = chat_id.replace('_', '')
			# first: user
			worker_id = 'hum-{}'.format(usr_dict['worker_id'])
			self.dialog_spkrs[new_chat_id].append(worker_id)
			for usr_turn_i_str, usr_turn_lbls in usr_dict['lbl_dict'].iteritems():
				usr_turn_i = int(usr_turn_i_str)
				abs_utt_id = 'co_{}_{}_{}'.format(new_chat_id, str(absolute_turns['user'][usr_turn_i]).zfill(2), worker_id)
				self.dialog_uttids[new_chat_id].append(abs_utt_id)
				self.lid_labels[abs_utt_id] = self.change_spa_neither_tag(usr_turn_lbls)
				self.texts[abs_utt_id] = usr_dict['txt_dict'][usr_turn_i_str]

			# second: bot
			cm_strategy = usr_dict['style'].replace('_', '')
			self.dialog_spkrs[new_chat_id].append('bot-{}'.format(cm_strategy))
			self.cm_styles[new_chat_id] = cm_strategy
			bot_dict = bot_data[chat_id]
			for bot_turn_i_str, bot_turn_lbls in bot_dict['lbl_dict'].iteritems():
				bot_turn_i = int(bot_turn_i_str)
				abs_utt_id = 'co_{}_{}_{}'.format(new_chat_id, str(absolute_turns['bot'][bot_turn_i]).zfill(2), 'bot-{}'.format(cm_strategy))
				self.dialog_uttids[new_chat_id].append(abs_utt_id)
				self.lid_labels[abs_utt_id] = self.change_spa_neither_tag(bot_turn_lbls)
				self.texts[abs_utt_id] = bot_dict['txt_dict'][bot_turn_i_str]

			# ensure order
			self.dialog_uttids[new_chat_id] = sorted(self.dialog_uttids[new_chat_id])
			# import pdb; pdb.set_trace()

		# print 'PROBLEMS:', problem_ctr
		# print 'INVALID:', invalid_ctr

	# chain can have multiple spkrs, only take last 2 spkrs
	# e.g. if spkr post order is: 1, 2, 3, 2 -> keep posts from [2, 3, 2]
	def load_reddit(self, infolder_name='./data/reddit/english_spanish_reddit_conversations'):
		#REMINDER what to populate
		# format uttid: '[corp_name]_[dialog_id]_[utt_num]_[spkr]''
		self.texts = {}  # [uttid] = list(words)
		self.lid_labels = {}  # [uttid] = list(language ID tags among {0,1,2})
		self.dialog_uttids = defaultdict(list)  # [dialog_id] = list(utt_ids)
		self.dialog_spkrs = defaultdict(list)  # [dialog_id] = list([spkr1, spkr2])

		one_spkr_ctr = 0
		for filename in os.listdir(infolder_name):
			if not filename.endswith('.txt'):
				continue

			# store each post, then prune to get only last 2 speakers
			post_idx = -1
			posts = []
			title = ''
			with open(os.path.join(infolder_name, filename), 'r') as f:
				for line in f.readlines():
					line = line.strip()
					if not line:  # empty line (break b/w posts)
						continue

					if line.startswith('author'):
						post_idx += 1
						# in case underscore is present in username
						new_post_dict = {'author': line.replace('author: ', '').replace('_', '#REPL#')}
						new_post_dict['body'] = []
						posts.append(new_post_dict)

					elif line.startswith('post title'):
						title = line.replace('post title: ', '')

					else:  # post body... new lines simply append without marker for newline break (could add this in though)
						posts[post_idx]['body'].extend(line.replace('post body: ', '').split())

			# if chains are all 1 spkr, ignore file
			all_spkrs = set([posts[post_i]['author'] for post_i in range(len(posts))])
			if len(all_spkrs) < 2:
				# print '## ', filename
				one_spkr_ctr += 1
				continue

			# assumes chains are length >= 2
			last_spkr_set = set([posts[post_idx]['author'], posts[post_idx - 1]['author']])
			keep_idxs = [post_idx, post_idx - 1]
			last_idx = post_idx - 2

			# in case last 2+ posts are from same 1 spkr
			while len(last_spkr_set) < 2:
				last_spkr_set.add(posts[last_idx]['author'])
				keep_idxs.append(last_idx)
				last_idx -= 1

			while last_idx >= 0:
				if posts[last_idx]['author'] not in last_spkr_set:
					break
				else:
					keep_idxs.append(last_idx)
				last_idx -= 1

			# grab info to store in main dicts
			for post_i in sorted(keep_idxs):
				dialog_id = filename.split('_')[1].replace('.txt', '')  # e.g. '0002'
				utt_num = str(post_i).zfill(2)
				spkr = posts[post_i]['author']
				uttid = 'rd{}_{}_{}_{}'.format(self.langs[0], dialog_id, utt_num, spkr)
				self.dialog_uttids[dialog_id].append(uttid)
				# assert len(last_spkr_set) == 2  #check
				self.dialog_spkrs[dialog_id] = list(last_spkr_set)

				text = posts[post_i]['body']
				no_tags_words = cm_metrics.remove_lidtags_miami(text)
				no_tags_words = [word.lower() for word in no_tags_words]
				self.texts[uttid] = no_tags_words

				# convert tags in str form (e.g. 'eng', 'tgl', 'spa') to int w/ map
				self.lid_labels[uttid] = self.get_tags_int(text)

		print 'ignored (one spkr only):', one_spkr_ctr

	# 425 TGL conversations
	def load_babel(self, infolder_name='./data/babel/ella_babel_trans_langid/trans_langid'):
		filenames = os.listdir(infolder_name)

		# get dialog_ids that only have both channels (inline and outline)
		no_inline_outlines = [fname[:34] for fname in filenames]
		both_channels = [x for x, y in Counter(no_inline_outlines).items() if y == 2]
		dialog_ids = [fname for fname in filenames if fname[:34] in both_channels]

		# get data
		# for file_short in dialog_ids:
		if True:
			file_short = 'BABEL_BP_106_04577_20120409_220039'
			dialog_id = file_short.replace('BABEL_BP_106_', '').replace('_', '-')

			# every other line is timestamp, starting with 1st line ex:
			# [1.015]
			# <no-speech>
			# [6.625]
			# hello_eng pare_tgl <sta>

			times_dict = {}

			def fill_times_dict(in_or_out):
				filename_path = os.path.join(infolder_name, file_short + '_{}Line_langid.txt'.format(in_or_out))

				with open(filename_path) as f:
					all_lines = [line.strip() for line in f.readlines()]

				last_time = -1.
				for line in all_lines:
					if line.startswith('['):  # timestamp
						last_time = float(line.replace('[', '').replace(']', ''))
					elif line == '<no-speech>':
						continue
					else:
						times_dict[last_time] = (in_or_out, line)

			fill_times_dict('in')
			fill_times_dict('out')

			# process text and LID labels
			for utt_i, time_stamp in enumerate(sorted(times_dict.keys())):
				# format uttid: '[corp_name]_[dialog_id]_[utt_num]_[spkr]''
				uttid = 'bbl_{}_{:04d}_{}'.format(dialog_id, utt_i, times_dict[time_stamp][0])
				self.dialog_uttids[dialog_id].append(uttid)
				self.dialog_spkrs = ['in', 'out']

				text = [word.lower() for word in times_dict[time_stamp][1].split() if not word.startswith('<')]  # remove nonspeech like <laugh>
				# import pdb; pdb.set_trace()
				self.texts[uttid] = cm_metrics.remove_lidtags_miami(text)

				self.lid_labels[uttid] = self.get_tags_int(text)

	# def detect_lang(self, tool_name, word_str):
	# 	if tool_name == 'langid':
	# 		langid.set_languages(self.langs)  # e.g. ['es', 'en']
		#TODO: continue


class Lexicon():

	def __init__(self, lang='eng'):
		self.lang = lang
		self.lang_idx = lang3_map[lang]
		self.word_dict = defaultdict(list)
		self.rgx_words = defaultdict(list)

	# load list of words that are 1 entry per line
	def load_wordlist(self, filename='./data/word_lists/en_aux.txt', word_cat='en_aux'):
		if word_cat in self.word_dict:
			print 'Word category [{}] already in lexicon'.format(word_cat)
			return 0

		with open(filename, 'r') as f:
			self.word_dict[word_cat] = [line.strip() for line in f.readlines()]

		self.rgx_words[word_cat] = [re.compile(r'\b{}\b'.format(entry)) for entry in self.word_dict[word_cat]]

	# load according to special format of LIWC
	def load_liwc(self, filename='./data/word_lists/LIWC2007_English080730_eahn.dic'):
		with open(filename, 'r') as f:
			f.readline()  # first line = '%'
			texts = [line.strip() for line in f.readlines()]
		split = texts.index('%')
		codes_words = {line.split('\t')[1]: int(line.split('\t')[0]) for line in texts[:split]}
		codes_int = {d: k for k, d in codes_words.iteritems()}

		for entry in texts[split + 1:]:
			word = entry.split('\t')[0]
			# print entry.split('\t')[1:]
			cats_int = [int(cat) for cat in entry.split('\t')[1:]]
			rgx_word = word

			if '*' in word:
				rgx_word = rgx_word.replace('*', '\S*')
				# print rgx_word, type(rgx_word)
				# word = word.replace('*', '')  # remove

			for cat_int in cats_int:
				cat_word = codes_int[cat_int]
				self.word_dict['liwc-{}'.format(cat_word)].append(word)
				new_rgx_word = re.compile(r'\b{}\b'.format(rgx_word))
				# print rgx_word, type(rgx_word)
				# break
				self.rgx_words['liwc-{}'.format(cat_word)].append(new_rgx_word)


	# given text = list of words, return matched items
	# only use words that have relevant language-ID
	# text_list and lid_list must have same length
	def in_text_list(self, text_list, lid_list, word_cat, ignore_star=False):
		matches = []
		if self.lang_idx not in lid_list:
			return matches

		for word in self.word_dict[word_cat]:
			if ignore_star:
				if '*' in word:
					continue

			lid_idxs = np.where(np.array(lid_list) == self.lang_idx)
			# word_idxs = np.where(text_list == word)
			this_lang_text_list = np.take(text_list, lid_idxs)
			# counts = this_lang_text_list.count(word)

			if '*' in word:  # liwc items only
				no_star_word = word.replace('*', '')
				pd_text_list = pd.Series(this_lang_text_list[0])
				counts = np.where(pd_text_list.str.startswith(no_star_word))[0].size
			else:
				counts = np.where(this_lang_text_list == word)[0].size
			# counts = np.intersect1d(lid_idxs, word_idxs)
			if counts > 0:
				matches.extend([word] * counts)

		return matches

	# given text = str of words, return regex-matched items
	#TODO: does not handle filtering non-relevant language ID items
	def in_text_longstr(self, text_str, word_cat):
		matches = []
		for rgx_word in self.rgx_words[word_cat]:
			matches.extend(re.findall(rgx_word, text_str))

		return matches


class Scores():

	def __init__(self, conv_data, lexicon):
		self.data = conv_data
		self.lex = lexicon
		self.dnm_scores = defaultdict(dict)
		self.msr_scores = defaultdict(dict)
		self.naist_scores = defaultdict(dict)
		self.soto_scores = defaultdict(dict)

	# self.scores[word_cat][spkr1] = how much spkr1 (replier) entrained to spkr2
	# self.scores[word_cat][spkr2] = how much spkr2 (replier) entrained to spkr1
	# returns (full score, term1 of eqn = minuend, term2 of eqn = subtrahend)
	def calc_dnm(self, word_cat, given_dialogid=None, calc_ratio=False, ignore_star=False):
		""" Danescu-Niculescu-Mizil et al. (2011) Entrainment, WWW
			* = P(ft in reply utt from SPK-2 / ft in previous utt from SPK-1)
				- P(ft in reply utt from SPK-2 / all replies to SPK-1)
			* Does not factor high-level temporal nature (e.g. start vs end of dialogue)
		"""
		# TEST: 1 dialogue, pass in given_dialogid='zeledon8'
		# dialog_id = 'zeledon8'
		# spkrs = ['MAR', 'FLA']

		dialog_speakers = self.data.dialog_spkrs.iteritems()
		if given_dialogid:  # create
			dialog_speakers = (given_dialogid, self.data.dialog_spkr[given_dialogid])

		for dialog_id, spkrs in dialog_speakers:

			# calc in both directions simultaneously
			spkr1, spkr2 = spkrs
			ft_in_reply = {spkr1: 0, spkr2: 0}
			ft_in_prev = {spkr1: 0, spkr2: 0}
			ft_in_reply_and_prev = {spkr1: 0, spkr2: 0}
			spkr_reply_cts = {spkr1: 0, spkr2: 0}

			uttid_prev = self.data.dialog_uttids[dialog_id][0]
			words_prev = self.data.texts[uttid_prev]
			matches_prev = self.lex.in_text_list(words_prev, self.data.lid_labels[uttid_prev], word_cat, ignore_star=ignore_star)
			for utt_id in self.data.dialog_uttids[dialog_id][1:]:
				spkr_reply = utt_id.split('_')[-1]
				# print dialog_id, spkrs, spkr_reply
				# if spkr_reply not in spkrs:
				if spkr_reply not in spkr_reply_cts:
					import pdb; pdb.set_trace()
					foo=4
				spkr_reply_cts[spkr_reply] += 1
				spkr_prev = uttid_prev.split('_')[-1]
				words_reply = self.data.texts[utt_id]
				matches_reply = self.lex.in_text_list(words_reply, self.data.lid_labels[utt_id], word_cat, ignore_star=ignore_star)

				if not calc_ratio:
					# variation 1: ft = 1 if any present in text
					if matches_reply:
						ft_in_reply[spkr_reply] += 1
						# AND
						if matches_prev:
							ft_in_reply_and_prev[spkr_reply] += 1
					if matches_prev:
						ft_in_prev[spkr_prev] += 1

				'''
				#TODO: fix logic
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
				'''
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

				return term1 - term2, term1, term2

			self.dnm_scores[word_cat][spkr1] = calc_a_entrained_to_b(spkr1, spkr2)
			self.dnm_scores[word_cat][spkr2] = calc_a_entrained_to_b(spkr2, spkr1)

	def calc_msr(self):
		""" Bawa et al. (2018) Accommodation of Code-choice in Miami, ACL
		"""
		self.msr_scores['foo'] = 0

	def calc_naist(self):
		""" Mizukami et al. (2016), SIGdial
			Modified Nenkova (2008), add smoothing
		"""
		self.naist_scores['foo'] = 0

	def calc_soto(self):
		""" Soto et al. (2018), Interspeech
			* Pearson r of convergence of “each speakers’ CS ratio for each speaker turn”
			* CS ratio = total # of CS normalized by total # of tokens
			* # of CS = # switch points in an utterance
		"""
		self.soto_scores['foo'] = 0


def main():
	miami = ConvData(infile_name='./data/miami/clean_1208', corp_name='miami', lang_pair='spa-eng')
	en_aux_lex = Lexicon(infile_name='./data/word_lists/en_aux.txt')
	# en_aux_lex = Lexicon(infile_name='./data/word_lists/en_fw_1_list.txt', lang='en')
	scores = Scores(miami, en_aux_lex)

	scores.calc_dnm(calc_ratio=False)
	print(scores.scores['dnm'])
	print('ALL SCORES\n', [scores.scores['dnm'][i][0] for i in scores.scores['dnm'].keys()])
	print('AVERAGE\n', np.mean([scores.scores['dnm'][i][0] for i in scores.scores['dnm'].keys()]))
	import pdb; pdb.set_trace()


def main_com():
	com_amig = ConvData(corp_name='com_amig', lang_pair='spa-eng')
	import pdb; pdb.set_trace()


def main_babel():
	bbl_tgl = ConvData(corp_name='babel', lang_pair='tgl-eng', infile_name='./data/babel/ella_babel_trans_langid/trans_langid')
	import pdb; pdb.set_trace()


def main_red():
	# red_spa = ConvData(corp_name='reddit', lang_pair='spa-eng', infile_name='./data/reddit/english_spanish_reddit_conversations')
	red_tgl = ConvData(corp_name='reddit', lang_pair='tgl-eng', infile_name='./data/reddit/english_tagalog_reddit_conversations')
	import pdb; pdb.set_trace()


if __name__ == '__main__':
	# main()
	# main_com()
	# main_red()
	main_babel()
