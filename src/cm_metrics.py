# -*- coding: utf-8 -*-
# from src.parse_miami import load_data, load_spkr_info
import spacy
# from itertools import groupby
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


# assume text is list of words
# only remove final "_{eng|spa|engspa}", e.g. "T_V_eng" -> "T_V"
def remove_lidtags_miami(text):
	return ['_'.join(word.split('_')[:-1]) for word in text]


# take full text (list of str), return [spa_closed_lst, eng_closed_lst]
# each sublist contains Booleans
def get_closed(text, spa_pos, eng_pos):
	closed_class = ['AUX', 'DET', 'CONJ', 'CCONJ', 'ADP']
	text = remove_lidtags_miami(text)
	# get english
	eng_closed_lst = []
	for i, word in enumerate(text):
		eng_is_closed = False
		if word in eng_closed_lst or eng_pos[i] in closed_class:
			eng_is_closed = True
		eng_closed_lst.append(eng_is_closed)

	# eng_aux = [word in eng_aux_lst for word in text]

	# get spanish
	# doc = nlp_all[0](unicode(' '.join(text), "utf-8"))
	# num_spa = len([1 for token in doc if token.pos_ == 'AUX'])
	spa_closed_lst = [spa_tag in closed_class for spa_tag in spa_pos]
	return [spa_closed_lst, eng_closed_lst]


# take full text (list of str), return [spa_pos_lst, eng_pos_lst]
def get_pos(text):
	# text = remove_lidtags_miami(text)
	str_text = ' '.join(text).decode('utf-8')
	doc_spa = nlp_all[0](unicode(str_text), "utf-8")
	spa_pos = [token.pos_ for token in doc_spa]
	doc_eng = nlp_all[1](unicode(str_text), "utf-8")
	eng_pos = [token.pos_ for token in doc_eng]
	return [spa_pos, eng_pos]


# given list of POS tags, return Boolean list of if it's NOUN/ADJ/VERB
# tag set inspiration: Content morphemes in Myers-Scotton's ML/EL framework
# noise: English aux can be tagged as VERB, e.g. "is"
# TODO: try removing PROPN, and adding PRON
def is_content(pos_lst):
	# cont_lst = []
	# for pos_tag in pos_lst:
	# 	if pos_tag in ['NOUN', 'ADJ']:
	# 		cont_lst.append('1')
	# 	if pos_tag == 'VERB'
	# 		if
	return [pos_tag in ['NOUN', 'ADJ', 'VERB', 'PROPN'] for pos_tag in pos_lst]


# split into 2 methods later: miami-specific, then style metrics
def get_style_metrics(all_data, dialog_id):
	# total_turns = sum([len(
	# 					all_data[dialog_id][spkr]['turn_num']
	# 					) for spkr in all_data[dialog_id].keys()])

	for spkr in all_data[dialog_id].keys():
		for line_i, words_01 in enumerate(all_data[dialog_id][spkr]['words_01']):
			# only process if utt = code-mixed
			if not (0 in words_01 and 1 in words_01):
				continue

			words_lst = remove_lidtags_miami(all_data[dialog_id][spkr]['words'][line_i])
			print ' '.join(words_lst)
			spa_pos, eng_pos = get_pos(words_lst)
			spa_aux, eng_aux = get_closed(words_lst, spa_pos, eng_pos)
			spa_cont = is_content(spa_pos)
			eng_cont = is_content(eng_pos)

			for i in range(len(words_01)):
				print '{}: {}'.format(words_01[i], words_lst[i])
				print 'S-POS\t{}\tE-POS\t{}'.format(spa_pos[i], eng_pos[i])
				print 'S-AUX\t{}\tE-AUX\t{}'.format(int(spa_aux[i]), int(eng_aux[i]))
				print 'S-CON\t{}\tE-CON\t{}'.format(int(spa_cont[i]), int(eng_cont[i]))
				print ''
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
			break


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
