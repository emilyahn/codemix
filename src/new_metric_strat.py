import spacy
from itertools import groupby


nlp_en = spacy.load('en')
nlp_sp = spacy.load('es')
nlp_all = [nlp_sp, nlp_en]


# give an utterance's LID labels and list(text)
# return strategy
def process_tags_2(words_01, words_lst, styles=None, styles_txt=None):
	# all indices -> 0 = SPA, 1 = ENG

	# TOKENIZE OPTION A (align spacy tokenizer with words_lst):
	# uni_words_lst = [unicode(word, "utf-8") for word in words_lst]
	# doc_spa = spacy.tokens.doc.Doc(nlp_all[0].vocab, words=uni_words_lst)
	# for name, proc in nlp_all[0].pipeline:
	# 	doc_spa = proc(doc_spa)
	# doc_eng = spacy.tokens.doc.Doc(nlp_all[1].vocab, words=uni_words_lst)
	# for name, proc in nlp_all[1].pipeline:
	# 	doc_eng = proc(doc_eng)

	# TOKENIZE OPTION B (higher acc):
	str_text = ' '.join(words_lst).decode('utf-8')
	doc_spa = nlp_all[0](unicode(str_text), "utf-8")
	doc_eng = nlp_all[1](unicode(str_text), "utf-8")

	spa_pos = [token.pos_ for token in doc_spa]
	eng_pos = [token.pos_ for token in doc_eng]
	tokens_all = [doc_spa, doc_eng]
	pos_all = [spa_pos, eng_pos]

	hyp_strat = None
	uneven = False

	if len(words_01) != len(eng_pos) or len(words_01) != len(spa_pos):
		# print 'UNEVEN', len(words_01), len(eng_pos), len(spa_pos)
		# print zip(words_lst, [token.text for token in doc_eng], [token.text for token in doc_spa])
		uneven = True

	num_lang = (len([1 for item in words_01 if item == 0]), len([1 for item in words_01 if item == 1]))

	# (1) check if structure
	# (1a) find finite verbs
	fin_vb_list = []
	for word_i, word_lang in enumerate(words_01):
		if word_lang == 2:
			continue

		if pos_all[word_lang][word_i] != 'VERB':
			continue

		token = tokens_all[word_lang][word_i]
		morph_tag = nlp_all[word_lang].vocab.morphology.tag_map[token.tag_]
		# print words_lst[word_i], morph_tag

		if word_lang == 0:
			# {u'morph': u'Mood=Ind|Number=Sing|Person=3|Tense=Pres|VerbForm=Fin', u'pos': u'VERB'}
			if 'VerbForm=Fin' in morph_tag['morph']:
				fin_vb_list.append(0)

		elif word_lang == 1:
			# EX:
			# {74: 99, u'Tense': u'pres', u'VerbForm': u'fin'},
			if 'VerbForm' in morph_tag:
				if morph_tag['VerbForm'] == 'fin':
					fin_vb_list.append(1)

	# (1b) find function words
	closed_class = ['AUX', 'CONJ', 'CCONJ', 'ADP', 'PRON']
	func_list = []
	for word_i, word_lang in enumerate(words_01):
		if word_lang == 2:
			continue

		if pos_all[word_lang][word_i] in closed_class:
			func_list.append(word_lang)

	# (1c) check contiguous 2+ words in language
	# get list of (key, num-consecutive):
	# EX: [ (0, 2), (1, 3), ... ] for [0,0,1,1,1,...]
	# first: remove any interrupting LID=2 tags
	no_2_words01 = [num for num in words_01 if num != 2]
	num_lang_groups = [(k, len(list(g))) for k, g in groupby(no_2_words01)]
	# num_lang_groups = [(k, len(list(g))) for k, g in groupby(words_01)]

	atleastn = [False, False]
	consec_thresh = 2
	first_atleastn = None
	for lang, num_consec in num_lang_groups:
		if lang == 2:
			continue

		if num_consec >= consec_thresh:
			atleastn[lang] = True
			# assign 0 or 1, for which lang first has >=2 # of func
			if first_atleastn is None:
				first_atleastn = lang

	# combine STRUCT CONDITIONS
	# if all(atleastn) and 0 in fin_vb_list and 1 in fin_vb_list:
	if all(atleastn):
		if (0 in func_list or 0 in fin_vb_list) and (1 in func_list or 1 in fin_vb_list):
			hyp_strat = 's-{}'.format(first_atleastn)

	# (2) check if content
	if not hyp_strat:
		if fin_vb_list or func_list:  # not empty
			set_vb = set(fin_vb_list)
			set_fn = set(func_list)
			content_list = []
			for word_i, word_lang in enumerate(words_01):
				if word_lang == 2:
					continue

				# allowable content: NOUN (not PROPN)
				if pos_all[word_lang][word_i] in ['NOUN', 'ADJ']:
					# don't allow if first letter is capitalized (indicator of Named Entity)
					if words_lst[word_i][0].isupper():
						# print 'CAUGHT', words_lst[word_i]
						continue

					content_list.append(word_lang)

			for item in set_vb:
				if 1 - item in content_list and num_lang[item] >= num_lang[1 - item]:
					hyp_strat = 'c-{}'.format(item)
					break

			if not hyp_strat:
				for item in set_fn:
					if 1 - item in content_list and num_lang[item] >= num_lang[1 - item]:
						hyp_strat = 'c-{}'.format(item)
						break

	if not hyp_strat:
		hyp_strat = 'neither'

	if styles is not None and styles_txt is not None:
		# print 'DOING SOMETHING'
		styles[hyp_strat] += 1
		styles_txt[hyp_strat].append(' '.join(words_lst))

	return hyp_strat, uneven
