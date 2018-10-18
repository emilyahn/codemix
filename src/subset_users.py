import csv
import json
from collections import defaultdict


country_dict = json.load(open('data/country_mapping.json'))
country_spellings = json.load(open('data/country_altspell.json'))
splits = [',', ';', ' and', ' y ']


# reads 1 qual file (either first-time or full)
# this is subset of contents from calc_cocoa.py:load_all_data()
def read_qual_file(qual_file):
	all_data = defaultdict(dict)
	reader = csv.DictReader(open(qual_file, 'r'), delimiter='\t')
	for row in reader:
		# print row
		chat_id = row['chat_id']
		for category in reader.fieldnames:  # iterate thru keys (header)
			if category == 'chat_id':
				continue
			all_data[chat_id][category] = row[category]

	return all_data


# full_data is version from load_all_data() in calc_cocoa.py
# given list of workers, return chatids that only correspond to those workers
def get_chats_from_workers(worker_list, full_data):
	chat_list = []
	for chat_id, chat_dict in full_data.iteritems():
		if 'worker_id' not in chat_dict:
			continue

		worker = chat_dict['worker_id']
		if worker in worker_list:
			chat_list.append(chat_id)
	return chat_list


# full_data is version from load_all_data() in calc_cocoa.py
def get_first_chatids(full_data):
	first_chatids = []
	workers_dct = {}
	ctr = 0
	for chat_id, chat_dict in full_data.iteritems():
		if 'submit' not in chat_dict:
			ctr += 1
			continue

		submit_time = chat_dict['submit']
		worker = chat_dict['worker_id']
		if worker == '[none]':
			continue

		if worker not in workers_dct:
			workers_dct[worker] = (submit_time, chat_id)
		elif submit_time < workers_dct[worker][0]:
			workers_dct[worker] = (submit_time, chat_id)
		else:
			# print 'repeat worker'
			pass

	first_chatids = [items[1] for workers, items in workers_dct.iteritems()]
	print len(first_chatids)
	print 'NOT IN QUAL TSV:', ctr
	return first_chatids


# will split into 2 groups (high and low scores)
# threshold: >= [score_thresh]/3 correct
# use unique workers only
def split_span_quiz(all_data, amt_worker_file, fig8_jsonlist_file, score_thresh=2):
	worker_to_score = {}
	high_workerids = []
	low_workerids = []

	# process FIG8 from list of fig8 json files
	with open(fig8_jsonlist_file, 'r') as f:
		# in chronological order, nice
		for filename in f.readlines():
			if filename.startswith('#'):
				continue

			fig8_contents = json.load(open(filename.strip()))
			for task in fig8_contents['results']['judgments']:
				worker_id = str(task['worker_id'])
				if worker_id in worker_to_score:
					continue

				score = 0
				for question in task['data']:
					if question.startswith('provide') or question.startswith('copy'):
						continue
					score += int(task['data'][question])

				worker_to_score[worker_id] = score

	# process AMT csv (unique workers)
	reader = csv.DictReader(open(amt_worker_file, 'r'))
	quiz_key = ''
	for word_group in reader.fieldnames:  # iterate thru keys (header)
		if word_group.startswith('CURRENT-Hablo'):
			quiz_key = word_group

	for row in reader:
		worker_id = row['Worker ID']
		score = int(row[quiz_key]) / 33
		worker_to_score[worker_id] = score

	for worker_id, score in worker_to_score.iteritems():
		if score >= score_thresh:
			high_workerids.append(worker_id)
		else:
			low_workerids.append(worker_id)

	return high_workerids, low_workerids


# will split into 2 groups (high and low scores)
# threshold: >= [score_thresh] on scale of 1/5
# use unique workers only
def split_lang_ability(first_data, lang='spa', score_thresh=4):
	high_score_ids = []
	low_score_ids = []

	if lang == 'spa':
		lang_key = 'n11_ability_spa'
	else:
		lang_key = 'n12_ability_eng'

	for chat_id, info_dict in first_data.iteritems():
		lang_score = int(info_dict[lang_key])
		if lang_score >= score_thresh:
			high_score_ids.append(info_dict['worker_id'])
		else:
			low_score_ids.append(info_dict['worker_id'])

	return high_score_ids, low_score_ids


# will split into 2 groups (old and young)
# threshold: >= [age_thresh]
# use unique workers only
def split_age_learn_spa(first_data, age_thresh=4):
	pass


# return dict: region: country: list of worker ids
# use unique workers only
def split_country(first_data):
	return_dict = {}
	spanish_workers = []
	# create dict: key=countries, val=list of worker ids
	# convert all countries to lowercase, also get correct spelling
	country_to_userid = defaultdict(list)
	for chat_id, info_dict in first_data.iteritems():
		user_country = info_dict['n13_country'].lower()
		if any(sp in user_country for sp in splits):
			for sp in splits:
				user_country = user_country.split(sp)[0]
		if user_country in country_spellings:
			user_country = country_spellings[user_country]  # get correct spelling

		country_to_userid[user_country].append(info_dict['worker_id'])

	spa_regions = ["central_america", "caribbean", "south_america", "europe"]
	# non-spanish regions = ["english", "other"]
	for region, countries in country_dict.iteritems():
		# print '=== {} ==='.format(region)
		num_in_region = 0

		region_dict = defaultdict(list)  # dict[country] = workerlist
		for country, workerids in country_to_userid.iteritems():
			if country in countries:
				region_dict[country].extend(workerids)
				if region in spa_regions:
					spanish_workers.extend(workerids)

				num_in_region += len(workerids)
				# print '{}\t{}'.format(country, len(workerids))

		return_dict[region] = region_dict
		# print 'TOTAL', num_in_region

	# print len(spanish_workers)

	return spanish_workers, return_dict


# remove chats where users only respond with <= 2 tokens
# return list of remaining chatids
def remove_short_resp(full_data, len_thresh=2):
	num_short = 0
	long_chatids = []
	for chat_id, chat_dict in full_data.iteritems():
		if 'lbl_dict' not in full_data[chat_id]:
			continue

		is_long = False
		for utt_num, lbl_list in full_data[chat_id]['lbl_dict'].iteritems():
			if len(lbl_list) >= len_thresh:
				is_long = True
				break

		if is_long:
			long_chatids.append(chat_id)
		else:
			num_short += 1

	print '{}/{} chats removed'.format(num_short, len(long_chatids) + num_short)
	return long_chatids


# remove monolingual chats
# return list of remaining chatids
def remove_monoling(full_data):
	num_mono = 0
	biling_chatids = []
	for chat_id, chat_dict in full_data.iteritems():
		if 'lbl_dict' not in full_data[chat_id]:
			continue

		has_0 = False
		has_1 = False
		for utt_num, lbl_list in full_data[chat_id]['lbl_dict'].iteritems():
			if has_0 and has_1:
				biling_chatids.append(chat_id)
				break

			if 0 in lbl_list:
				has_0 = True

			if 1 in lbl_list:
				has_1 = True

		if not (has_0 and has_1):
			num_mono += 1

	print '{}/{} chats removed'.format(num_mono, len(biling_chatids) + num_mono)
	return biling_chatids


def main():
	first_data = read_qual_file('cocoa/eval/all_qual_firsttime_0831.tsv')

	# split_span_quiz(all_data)
	spa_country_workerids, region_dict_full = split_country(first_data)
	print spa_country_workerids


if __name__ == '__main__':
	main()
