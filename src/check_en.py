import os
import sys
# from collections import defaultdict
import unidecode


# check which babel langs have English in them


# load dictionaries
def load_lang_dict(filename):
	word_list = set()
	with open(filename, 'r') as fin:
		for line in fin.readlines():
			word = line.strip().decode('utf-8')
			word = unidecode.unidecode(word)
			if len(word) > 2:  #TODO: can change cutoff for EN word length
				word_list.add(word)

	return word_list

en_list = load_lang_dict('data/word_lists/en_1000_common.txt')
# en_list = load_lang_dict('en_1000_common.txt')


def calc_babel_lang(babel_dir):
	# default TG {0: 166,113, 1: 12,802, 2: 421,111}
	# default EN {0: 155,295, 1: 23,620, 2: 421,111}
	eng_words_set = set()
	# num uniq words~ tg: 557 en: 608 other: 23,264
	num_utts = 0
	num_cm_utts = 0
	for filename in os.listdir(babel_dir):
		filename_path = os.path.join(babel_dir, filename)
		# file_id = os.path.splitext(filename)[0]

		with open(filename_path) as f:
			all_lines = [line.strip() for line in f.readlines()]
			for line in all_lines:
				if line.startswith('[') or line == '<no-speech>':  # timestamp or other
					continue

				num_utts += 1
				line_has_eng = False
				for word in line.split():
					if word.startswith('<'):
						continue
					if word in en_list:
						eng_words_set.add(word)
						line_has_eng = True
				if line_has_eng:
					print line
					num_cm_utts += 1

	if num_utts == 0:
		perc = 0
	else:
		perc = float(num_cm_utts) / num_utts
	print '\nENWORDS\n', eng_words_set, '\n'
	print num_cm_utts, num_utts, perc


if __name__ == '__main__':
	babel_dir = sys.argv[1]
	calc_babel_lang(babel_dir)
