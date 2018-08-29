# -*- coding: utf-8 -*-
# from src.parse_miami import load_data, load_spkr_info
import spacy
from itertools import groupby
from collections import defaultdict
import math


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
# TODO: try adding PRON, removing DET
def get_func(text, spa_pos, eng_pos):
	closed_class = ['AUX', 'CONJ', 'CCONJ', 'ADP', 'PRON']
	# text = remove_lidtags_miami(text)
	# get english
	eng_closed_lst = []
	for i, word in enumerate(text):
		eng_is_closed = False
		if word in eng_closed_lst or eng_pos[i] in closed_class:
			eng_is_closed = True
		eng_closed_lst.append(eng_is_closed)

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


# given list of POS tags, return Boolean list of if itmems are NOUN/ADJ/VERB
# tag set inspiration: Content morphemes in Myers-Scotton's ML/EL framework
# noise: English aux can be tagged as VERB, e.g. "is"
#TODO: try removing PROPN
def get_content(pos_lst):
	return [pos_tag in ['NOUN', 'ADJ', 'VERB', 'PROPN'] for pos_tag in pos_lst]


# check if (1) Structure
# return one of {None, 0, 1}
# rule: 2 consecutive L1 func, and 2 consecutive L2 func -- in same utt
def is_structure(words_01, both_aux):
	func_lst = []  # 0s (ENG) and 1s (SPA) of function words only
	for i in range(len(words_01)):
		lang = words_01[i]
		if lang not in [0, 1]:
			continue
		if both_aux[lang][i]:  # this word is an AUX in lang X
			func_lst.append(lang)

	# TESTING ONLY
	# func_lst = [0, 1, 0, 0, 1, 1, 0, 1, 0]

	# get list of (key, num-consecutive):
	# EX: [ (0, 2), (1, 3), ... ] for [0,0,1,1,1,...]
	num_func_groups = [(k, len(list(g))) for k, g in groupby(func_lst)]

	atleast2 = [False, False]
	first_atleast2 = None
	for lang, num_consec in num_func_groups:
		# if num_consec >= 2:
		if num_consec >= 1:
			atleast2[lang] = True
			# assign 0 or 1, for which lang first has >=2 # of func
			if first_atleast2 is None:
				first_atleast2 = lang

	# print 'FUNC LIST', num_func_groups
	# print 'atleast2', atleast2
	# print 'first_atleast2', first_atleast2

	if all(atleast2):
		return first_atleast2

	return None


# check if (2) Content
# return None or (0|1, 'w'|'s')
# 0 indicates matrix lang
# 'w' (weak) : num L2 content > 0
# 's' (strong) : (weak) && num L2 content >= num L1 content
def is_content(words_01, both_aux, both_cont):
	num_aux = [0, 0]
	num_cont = [0, 0]
	# accumulate number of function and content words per language
	for i in range(len(words_01)):
		lang = words_01[i]
		if lang not in [0, 1]:
			continue
		num_aux[lang] += int(both_aux[lang][i])
		num_cont[lang] += int(both_cont[lang][i])

	# print 'AUX:', num_aux
	# print 'CONT:', num_cont
	winner = None
	if num_aux[0] > num_aux[1]:
		winner = 0
	elif num_aux[1] > num_aux[0]:
		winner = 1

	if winner is None:
		return None
	else:
		strength = None
		if num_cont[winner - 1] > 0:
			strength = 'w'
		if num_cont[winner - 1] >= num_cont[winner]:
			strength = 's'

		if strength is not None:
			return (winner, strength)
		else:
			return None


# from styles dict, compute proportions of each style
def calc_styles(styles):
	style_calcs = {}
	total_utt = float(sum([v for k, v in styles.iteritems()]))
	sorted_names = sorted(styles.keys())
	for style_name in sorted_names:
		count = styles[style_name]
		print '{}\t{:.2f}'.format(style_name, (100 * count)/total_utt)
		style_calcs[style_name] = (100 * count)/total_utt

	return style_calcs


# give an utterance's LID labels and list(text)
# update styles and styles_txt dictionaries
def process_tags(words_01, words_lst, styles, styles_txt, finegrain=True):
	# all indices -> 0 = SPA, 1 = ENG
	both_pos = get_pos(words_lst)
	spa_pos, eng_pos = both_pos

	both_aux = get_func(words_lst, spa_pos, eng_pos)
	both_cont = [get_content(spa_pos), get_content(eng_pos)]

	structure = is_structure(words_01, both_aux)
	# print 'STRUCTURE?', structure

	content = is_content(words_01, both_aux, both_cont)
	# print 'CONTENT?', content

	# check if both styles are present
	# if structure is not None and content is not None:
	# 	print '*'*20
	# 	print 's-{}'.format(structure)
	# 	print 'c-{}-{}'.format(content[0], content[1])

	name = ''
	if structure is not None:
		name = 's-{}'.format(structure)
	elif content is not None:
		name = 'c-{}'.format(content[0])
		if finegrain:
			name = 'c-{}-{}'.format(content[0], content[1])
	else:
		name = 'neither'

	styles[name] += 1
	styles_txt[name].append(' '.join(words_lst))
	return name


# print CM metrics for Miami data only
# return dict where with {style: list(txt examples)}
def get_style_metrics_miami(all_data):
	styles = defaultdict(int)
	styles_txt = defaultdict(list)
	for dialog_id in all_data.keys():
		# dialog_id = 'zeledon8'  # DEBUGGING
		num_cm_utt = 0
		for spkr in all_data[dialog_id].keys():
			# spkr = 'MAR'  # DEBUGGING
			for line_i, words_01 in enumerate(all_data[dialog_id][spkr]['words_01']):
				# only process if utt = code-mixed
				if not (0 in words_01 and 1 in words_01):
					continue

				num_cm_utt += 1
				words_lst = remove_lidtags_miami(all_data[dialog_id][spkr]['words'][line_i])
				if words_lst[-1] == '':
					words_lst = words_lst[:-1]

				process_tags(words_01, words_lst, styles, styles_txt)

		print '{}\tnum CM utt: {}'.format(dialog_id, num_cm_utt)

	calc_styles(styles)

	return styles_txt


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


# print CM metrics for Twitter data only
# return dict where with {style: list(txt examples)}
def get_style_metrics_twitter(twitter_dict):
	styles = defaultdict(int)
	styles_txt = defaultdict(list)
	num_cm_utt = 0
	num_total_tweet = 0

	for i, lbl_lst in enumerate(twitter_dict['lbl']):
		num_total_tweet += 1
		# convert text labels to list of 0s, 1s
		words_01 = []
		for lbl in lbl_lst:
			if lbl == 'lang1':  # ENG
				word_01 = 1
			elif lbl == 'lang2':  # SPA
				word_01 = 0
			else:  # other
				word_01 = 2

			words_01.append(word_01)

		# only process if utt = code-mixed
		if not (0 in words_01 and 1 in words_01):
			continue

		num_cm_utt += 1
		words_lst = twitter_dict['txt'][i]
		if words_lst[-1] == '':
			words_lst = words_lst[:-1]

		process_tags(words_01, words_lst, styles, styles_txt)

	print 'num CM utt: {}'.format(num_cm_utt)
	print 'num total : {}'.format(num_total_tweet)
	print 'percent CM: {}'.format(float(num_cm_utt)/num_total_tweet)

	calc_styles(styles)

	return styles_txt


# multilingual index across all words across users
def calc_m_idx(chat_lid_lsts):
	num_spa_eng = [0, 0, 0]  # 3rd spot will be ignored
	for user, lid_lists in chat_lid_lsts.iteritems():
		for utt_list in lid_lists:
			for x in utt_list:
				# print x
				num_spa_eng[x] += 1

	# print num_spa_eng
	num_total_01 = float(num_spa_eng[0] + num_spa_eng[1])
	# print num_total_01
	try:
		sigma = math.pow(num_spa_eng[0]/num_total_01, 2) + math.pow(num_spa_eng[1]/num_total_01, 2)
	# print 'sigma', sigma
		return (1 - sigma) / sigma
	except ZeroDivisionError:
		return 0


# integration index, averaged per user
# also print values per user just for sanity check
def calc_i_idx(chat_lid_lsts):
	scores = []
	for user, lid_lists in chat_lid_lsts.iteritems():
		user_01_list = []
		for utt_list in lid_lists:
			user_01_list.extend(utt_list)

		# remove LID tag = 2 (neither eng nor spa)
		flat_list = [utt for utt in user_01_list if utt < 2]

		if len(flat_list) < 2:
			score = 0.

		else:
			num_switches = 0
			for i, lid in enumerate(flat_list[1:]):
				if flat_list[i - 1] != lid:
					num_switches += 1

			score = float(num_switches) / (len(flat_list) - 1)

		scores.append(score)

	# print scores
	try:
		return sum(scores) / len(scores)
	except ZeroDivisionError:
		return 0


# print CM metrics for collected COCOA data only
# return dict where dict[style_label] = {style: list(txt examples)}
def get_style_metrics_cocoa(filename):

	txt_lst = defaultdict(list)
	lbl_lst = defaultdict(list)
	# chat2style = {}
	style2chat = defaultdict(set)

	# with open(chat2style_file) as f:
	# 	for line in f.readlines():
	# 		chat_id, chat_style = line.strip().split('\t')
	# 		chat2style[chat_id] = chat_style

	with open(filename) as f:
		for line in f.readlines():
			all_info = line.replace('\n', '').split('\t')

			chat_id_concat = '{}_{}'.format(all_info[1], all_info[2].zfill(2))
			# ex. style2chat['en_lex'].append('chat_id_4')
			style2chat[all_info[0]].add(chat_id_concat)
			txt = all_info[3]  # single token

			lbl = all_info[4]
			if len(all_info) > 5:
				if all_info[5] != '':
					# use manually fixed LID tag instead, if applicable
					lbl = all_info[5]

			txt_lst[chat_id_concat].append(txt)
			lbl_lst[chat_id_concat].append(lbl)

	# print sorted(txt_lst.keys())

	# this loop flattens txt_lst and lbl_lst (without chat_id_concat)
	# for chat_id_concat, txts in txt_lst.iteritems():
	# 	data['lbl'].append(lbl_lst[chat_id_concat])
	# 	data['txt'].append(txts)

	styles_txt_dct = {}

	for given_style in style2chat.keys():

		styles = defaultdict(int)
		styles_txt = defaultdict(list)
		num_cm_utt = 0
		num_eng_only = 0
		num_spa_only = 0
		num_total_tweet = 0
		chat_lid_lsts = defaultdict(list)

		print 'STYLE: {}'.format(given_style)
		print 'num utt in style:', len(style2chat[given_style])

		for chat_id_concat in sorted(style2chat[given_style]):
			# print chat_id_concat
		# for i, lbl_lst in enumerate(data['lbl']):
			utt_lbls = lbl_lst[chat_id_concat]
			# print len(utt_lbls)
			# import pdb; pdb.set_trace()

			num_total_tweet += 1
			# convert text labels to list of 0s, 1s
			words_01 = [int(utt_lbl) for utt_lbl in utt_lbls]
			chat_lid_lsts[chat_id_concat[:-3]].append(words_01)

			# only process if utt = code-mixed
			if not (0 in words_01 and 1 in words_01):
				if 0 in words_01:
					num_spa_only += 1
					# print 'SPA: ', data['txt'][i]
				elif 1 in words_01:
					num_eng_only += 1
					# print 'ENG: ', data['txt'][i]
				else:
					# print 'NEITHER: ', data['txt'][i]
					pass
				continue

			num_cm_utt += 1
			# words_lst = data['txt'][i]
			words_lst = txt_lst[chat_id_concat]
			if words_lst[-1] == '':
				words_lst = words_lst[:-1]

			process_tags(words_01, words_lst, styles, styles_txt)

		print 'num CM utt: {}'.format(num_cm_utt)
		print 'num EN utt: {}'.format(num_eng_only)
		print 'num SP utt: {}'.format(num_spa_only)
		print 'num total : {}'.format(num_total_tweet)
		print 'percent CM: {}'.format(float(num_cm_utt)/num_total_tweet)
		print 'percent EN: {}'.format(float(num_eng_only)/num_total_tweet)
		print 'percent SP: {}'.format(float(num_spa_only)/num_total_tweet)
		print

		calc_styles(styles)
		styles_txt_dct[given_style] = styles_txt

		# import pdb; pdb.set_trace()
		print 'M-IDX:', calc_m_idx(chat_lid_lsts)
		print 'I-IDX:', calc_i_idx(chat_lid_lsts)

		print
		print '*'*20
		print

	return styles_txt_dct

# filename = './data/manual_19struct_fixed.tsv'
# chat2style = './data/chatid2style.txt'
# cocoa_style_txt = get_style_metrics_cocoa(filename, chat2style)
