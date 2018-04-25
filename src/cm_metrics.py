# -*- coding: utf-8 -*-
# from src.parse_miami import load_data, load_spkr_info
import spacy
from itertools import groupby


nlp_en = spacy.load('en')
nlp_sp = spacy.load('es')
nlp_all = [nlp_sp, nlp_en]  # 0: spa, 1: eng

# EXAMPLE...
# words_str = ''
# doc = nlp_all[0](unicode(words_str, "utf-8"))
# for token in doc:
# 	print token.pos_
# EXAMPLE END...


# TODO: how to handle words tagged with BOTH? e.g. Named Entities
# split into 2 methods later: miami-specific, then style metrics
def get_style_metrics(all_data, dialog_id):
	# total_turns = sum([len(
	# 					all_data[dialog_id][spkr]['turn_num']
	# 					) for spkr in all_data[dialog_id].keys()])

	for spkr in all_data[dialog_id].keys():
		for line_i, line in enumerate(all_data[dialog_id][spkr]['words_01']):
			# only process if utt = code-mixed
			if not (0 in line and 1 in line): continue
			# spans: [ (0, 2), (1, 3), ... ] for [0,0,1,1,1,...]
			spans = [(k, len(list(g))) for k, g in groupby(line)]
			word_idx = 0
			for span in spans:
				words_str = ''  # UNICODE ERRORS?
				for this_word_idx in range(span[1]):
					this_word = all_data[dialog_id][spkr]['words'][line_i][word_idx].split('_')[0]
					words_str += ' {}'.format(this_word)
					word_idx += 1

				words_str = words_str.strip()
				print words_str

				doc = nlp_all[span[0]](unicode(words_str, "utf-8"))
				for token in doc:
					print token.pos_

			break






