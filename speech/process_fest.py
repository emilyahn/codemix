from collections import defaultdict
import os
from src.cm_metrics import process_tags, remove_lidtags_miami


# def get_vowels():
with open('speech/vowel_arpabet.txt') as f:
	loaded_vowels = [line.strip() for line in f.readlines()]
	# return total


def is_vowel(phone):
	return phone in loaded_vowels


def process_one_file(filename):
	dialog_words = []
	dialog_id = os.path.basename(filename).replace('_parsed.txt', '')

	with open(filename) as f:
		total = [line.strip() for line in f.readlines()]

	# remove [NS...]
	for i, line in enumerate(total):
		turn = line.split()
		words = [word for word in turn[3:] if not word.startswith('[NS')]
		dialog_words.append(words)

	return dialog_id, dialog_words


def load_data(data_folder_path):
	all_data = defaultdict(dict)

	for filename in os.listdir(data_folder_path):
		filename_path = os.path.join(data_folder_path, filename)
		dialog_id, dialog_words = process_one_file(filename_path)
		# all_data[dialog_id] = {}
		all_data[dialog_id]['words'] = dialog_words

		# add span info of each spkr into all_data
		# for spkr in dialog_dict.keys():

		# turn_dict = defaultdict(list)
		all_data[dialog_id]['words_01'] = []
		# [0] = list of Spanish span lengths
		# [1] = list of English span lengths
		for turn in dialog_words:
			turn_list = []
			for i, word in enumerate(turn):
				# if word.startswith('[NS'):
				# 	continue

				if word.endswith("_eng"):
					turn_list.append(1)
				if word.endswith("_spa"):
					turn_list.append(0)
				# adds named entities, ambiguous words like "oh", "yeah"
				if word.endswith("_engspa"):
					turn_list.append(2)

			all_data[dialog_id]['words_01'].append(turn_list)
		# 	for k, g in groupby(turn_list):
		# 		# EX: turn_dict[0] = [3,5,3,1] -> list of spanish spans
		# 		# EX: turn_dict[1] = [8,1,2] -> list of english spans
		# 		turn_dict[k].append(len(list(g)))
			# all_data[dialog_id][spkr]['turns'] = turn_dict
	return all_data


def get_style_metrics_miami(all_data):
	num_zfill = 5
	name_id_dict = {}
	name_id_dict['ids'] = defaultdict(list)
	name_id_dict['txt'] = defaultdict(list)
	name_id_dict['lid'] = defaultdict(list)
	# aggregate collections. Not used
	styles = defaultdict(int)
	styles_txt = defaultdict(list)
	for dialog_id in all_data.keys():
		# dialog_id = 'zeledon8'  # DEBUGGING
		num_cm_utt = 0
		for line_i, words_01 in enumerate(all_data[dialog_id]['words_01']):
			# only process if utt = code-mixed
			if not (0 in words_01 and 1 in words_01):
				continue

			num_cm_utt += 1
			words_lst = remove_lidtags_miami(all_data[dialog_id]['words'][line_i])
			if words_lst[-1] == '':
				words_lst = words_lst[:-1]

			name = process_tags(words_01, words_lst, styles, styles_txt, finegrain=False)
			line_id = '{}_{}'.format(dialog_id, str(line_i + 1).zfill(num_zfill))
			name_id_dict['ids'][name].append(line_id)
			name_id_dict['txt'][name].append(words_lst)
			name_id_dict['lid'][name].append(words_01)

		# print '{}\tnum CM utt: {}'.format(dialog_id, num_cm_utt)

	return name_id_dict


def get_all_cm_uttids(name_ids_dict):
	cm_uttids = []
	for name in name_ids_dict['ids']:
		cm_uttids.extend(name_ids_dict['ids'][name])
	print len(cm_uttids)
	return cm_uttids


def process_one_durfile(filename):
	phones = []
	durations = []
	words = []
	with open(filename) as f:
		for line in f.readlines():
			start = float(line.split()[2])
			end = float(line.split()[1])
			dur = end - start
			phone = line.split()[0]
			word = line.split()[3]
			durations.append(dur)
			phones.append(phone)
			words.append(word)

	# includes phone=pau (word=0)
	return {'phon': phones, 'dur': durations, 'wd': words}


def get_dur_dict(dur_dir, cm_uttids):
	# dur_dir = 'speech/dur'
	dur_dicts = {}
	for filename in os.listdir(dur_dir):
		filename_path = os.path.join(dur_dir, filename)
		utt_id = os.path.basename(filename).replace('.dur', '')
		if utt_id not in cm_uttids:
			continue

		utt_dict = process_one_durfile(filename_path)
		dur_dicts[utt_id] = utt_dict

	return dur_dicts


# FOR LAB FILE NO LONGER NEEDED
def process_one_labfile(filename):
	phones = []
	timestamps = []
	with open(filename) as f:
		for line in f.readlines():
			if '#' in line:
				continue

			dur = float(line.split()[0])
			phone = line.split()[2]
			timestamps.append(dur)
			phones.append(phone)

	durations = []
	for i, timestamp in enumerate(timestamps):
		if i == 0:
			prior = 0.0

		duration = timestamp - prior
		durations.append(duration)
		prior = timestamp

	return phones, durations


def get_vowel_durations(vowels, phones, durations, words):
	vowel_phones = []
	vowel_durs = []
	vowel_words = []
	for i, phone in enumerate(phones):
		if phone in vowels:
			vowel_phones.append(phone)
			vowel_durs.append(durations[i])
			vowel_words.append(words[i])

	return vowel_phones, vowel_durs, vowel_words


# can be modularized with language flag: Spanish=0, English=1
# return dict[strat][phone] = list(durations)
def get_eng_vowel_dur(name_ids_dict, dur_dicts):
	engvow_phon_dur = {}
	for name, idlist in name_ids_dict['ids'].iteritems():
		print name
		ctr = 0
		strat_dict = defaultdict(list)
		for i_utt, uttid in enumerate(idlist):
			if uttid in dur_dicts:
				ctr += 1

				for i, phone in enumerate(dur_dicts[uttid]['phon']):
					if is_vowel(phone):  # get vowels only
						word = dur_dicts[uttid]['wd'][i]
						try:
							word_idx = name_ids_dict['txt'][name][i_utt].index(word)
							lid_tag = name_ids_dict['lid'][name][i_utt][word_idx]
							if lid_tag == 1:  # get english only
								strat_dict[phone].append(dur_dicts[uttid]['dur'][i])
						except ValueError:
							pass

		print ctr
		engvow_phon_dur[name] = strat_dict

	return engvow_phon_dur


# from dict of all found eng vowels, return sorted list of ENG vowels only
def get_sorted_eng_vowels_only(engvow_phon_dur):
	eng_vowels = []
	for strat, strat_dict in engvow_phon_dur.iteritems():
		eng_vowels.extend(strat_dict.keys())

	eng_vowels_set = set(eng_vowels)
	engvow_sorted = sorted(list(eng_vowels_set))

	print engvow_sorted
	return engvow_sorted


def print_dur_dict(engvow_phon_dur, engvow_sorted):
	for strat, strat_dict in engvow_phon_dur.iteritems():
		print strat

	for engvow in engvow_sorted:
		avgdurs = []
		for strat, strat_dict in engvow_phon_dur.iteritems():
			if engvow in strat_dict:
				avgdur = sum(strat_dict[engvow]) / len(strat_dict[engvow])
			else:
				avgdur = ''
			avgdurs.append(avgdur)

		print '{}\t{}'.format(engvow, '\t'.join([str(dur) for dur in avgdurs]))


def main():
	data_dir = 'data/miami/clean_1009'
	all_data = load_data(data_dir)
	name_ids_dict = get_style_metrics_miami(all_data)
	for name in name_ids_dict['ids']:
		print name, len(name_ids_dict['ids'][name])

	print name_ids_dict['txt'].keys()



if __name__ == '__main__':
	main()