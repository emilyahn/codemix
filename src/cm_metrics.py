# -*- coding: utf-8 -*-
# from src.parse_miami import load_data, load_spkr_info
import spacy
from itertools import groupby
from collections import defaultdict


nlp_en = spacy.load('en')
nlp_sp = spacy.load('es')
nlp_all = [nlp_sp, nlp_en]  # 0: spa, 1: eng

with open('./data/auxiliaries.txt') as f:
	eng_aux_lst = [line.strip() for line in f.readlines()]

# EXAMPLE...
# words_str = ''
# doc = nlp_all[0](unicode(words_str, "utf-8"))
# for token in doc:
# 	print token.pos_
# EXAMPLE END...


def remove_lidtags(text):
	return ['_'.join(word.split('_')[:-1]) for word in text]


# take full text (list of str), return [num_spa_aux, num_eng_aux]
def num_aux(text):
	text = remove_lidtags(text)
	# get english
	num_eng = 0
	for word in text:
		if word in eng_aux_lst:
			num_eng += 1

	# get spanish
	doc = nlp_all[0](unicode(' '.join(text), "utf-8"))
	num_spa = len([1 for token in doc if token.pos_ == 'AUX'])
	return [num_spa, num_eng]


# take full text (list of str), return [spa_pos_lst, eng_pos_lst]
def get_pos(text):
	text = remove_lidtags(text)
	str_text = ' '.join(text).decode('utf-8')
	doc_spa = nlp_all[0](unicode(str_text), "utf-8")
	spa_pos = [token.pos_ for token in doc_spa]
	doc_eng = nlp_all[1](unicode(str_text), "utf-8")
	eng_pos = [token.pos_ for token in doc_eng]
	return [spa_pos, eng_pos]


# split into 2 methods later: miami-specific, then style metrics
def get_style_metrics(all_data, dialog_id):
	# total_turns = sum([len(
	# 					all_data[dialog_id][spkr]['turn_num']
	# 					) for spkr in all_data[dialog_id].keys()])

	for spkr in all_data[dialog_id].keys():
		for line_i, line in enumerate(all_data[dialog_id][spkr]['words_01']):
			# only process if utt = code-mixed
			if not (0 in line and 1 in line):
				continue

			print ' '.join(all_data[dialog_id][spkr]['words'][line_i])
			spa_aux, eng_aux = num_aux(all_data[dialog_id][spkr]['words'][line_i])
			spa_pos, eng_pos = get_pos(all_data[dialog_id][spkr]['words'][line_i])

			print 'aux: (spa, eng): ({}, {})'.format(spa_aux, eng_aux)
			# print 'spa_pos', spa_pos
			# print 'eng_pos', eng_pos

			# # spans: [ (0, 2), (1, 3), ... ] for [0,0,1,1,1,...]
			# spans = [(k, len(list(g))) for k, g in groupby(line)]
			# word_idx = 0
			# for span in spans:
			# 	words_str = ''  # UNICODE ERRORS?
			# 	for this_word_idx in range(span[1]):
			# 		this_word = all_data[dialog_id][spkr]['words'][line_i][word_idx].split('_')[0]
			# 		words_str += ' {}'.format(this_word)
			# 		word_idx += 1

			# 	words_str = words_str.strip()
			# 	print words_str
			# 	# span[0] = {0,1}
			# 	doc = nlp_all[span[0]](unicode(words_str, "utf-8"))
			# 	for token in doc:
			# 		print token.pos_
			# 		if token.pos_ == 'NOUN':
			# 			pass
			# break


# lbl: list of labels for each tweet
# 		lang1 = ENG, lang2 = SPA
# tweet_id is not preserved in return data
# returns: data['lbl', 'txt'] --> each has a list of (list of tokens/lbls)
def parse_twitter(tsvfile):
	data = defaultdict(list)
	txt_lst = defaultdict(list)
	lbl_lst = defaultdict(list)
	with open(tsvfile) as f:
		for line in f.readlines():
			all_info = line.replace('\n', '').split('\t')
			tweet_id = all_info[0]
			txt = all_info[4]
			lbl = all_info[5]

			txt_lst[tweet_id].append(txt)
			lbl_lst[tweet_id].append(lbl)

	for tweet_id, txts in txt_lst.iteritems():
		data['lbl'].append(lbl_lst[tweet_id])
		data['txt'].append(txts)

	return data
