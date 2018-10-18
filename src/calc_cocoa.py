from cm_metrics import calc_i_idx, calc_m_idx, process_tags
from collections import defaultdict
import csv
import json
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix
import itertools
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import KFold
# from random import shuffle
from sklearn.metrics import classification_report
from sklearn.preprocessing import normalize
from scipy.stats import pearsonr
import statistics

# calculate avg response time
def calc_response_times(events_dict, agents_dict):

	resp_time_dict = {}  # key = event index, value = float(response_time)
	resp_time_dict_select = {}  # key = event index, value = float(response_time)

	# list of agents 'rule_bot' or 'human', across events in sequence
	agent_id = {}
	agent_id[0] = 'human'
	agent_id[1] = 'rule_bot'
	if agents_dict['0'] == 'rule_bot':
		agent_id[1] = 'human'
		agent_id[0] = 'rule_bot'

	agent_list = [agent_id[event['agent']] for event in events_dict]

	for i, event in enumerate(events_dict):
		if i == 0:
			continue
		# print i, agent_list[i]
		if agent_list[i] == 'human' and agent_list[i - 1] == 'rule_bot':
			# if not include_select:

			# print event['data']
			this_time = float(event['time'])
			last_time = float(events_dict[i - 1]['time'])
			resp_time = this_time - last_time
			if event['action'] == 'select' or events_dict[i - 1] == 'select':
				resp_time_dict_select[i] = resp_time
				continue

			resp_time_dict[i] = resp_time

	if resp_time_dict:
		rt_avg = sum(resp_time_dict.values()) / len(resp_time_dict.keys())
	else:
		rt_avg = 0

	if resp_time_dict_select:
		# combine_dict = {}
		for k, val in resp_time_dict.iteritems():
			resp_time_dict_select[k] = val
		rt_avg_select = sum(resp_time_dict_select.values()) / len(resp_time_dict_select.keys())
	else:
		resp_time_dict_select = resp_time_dict
		rt_avg_select = rt_avg

	return resp_time_dict, rt_avg, resp_time_dict_select, rt_avg_select


# read in txt file of 3 columns (LID tsv, qual tsv, chat json)
# will combine across batches
# returns all_data: 	dict[chat_id] = dicts...
# each entry in qual tsv will be direct key in each chat dict
def load_all_data(master_filelist):
	all_data = defaultdict(dict)

	# read filenames from list
	file_names = defaultdict(list)
	master_reader = csv.DictReader(open(master_filelist, 'r'), delimiter='\t')
	for row in master_reader:
		for file_type in master_reader.fieldnames:  # iterate thru keys (header)
			if row[file_type]:
				file_names[file_type].append(row[file_type])

	# read all qual TSVs
	for qual_file in file_names['qual_tsv']:
		reader = csv.DictReader(open(qual_file, 'r'), delimiter='\t')
		for row in reader:
			chat_id = row['chat_id']
			for category in reader.fieldnames:  # iterate thru keys (header)
				if category == 'chat_id':
					continue
				all_data[chat_id][category] = row[category]
	print 'read all qual tsvs'

	# read chat jsons
	# grab agents, events, styles (in case not present in qual surveys)
	for chat_json in file_names['chat_json']:
		chat_list = json.load(open(chat_json))
		# store agents and events
		for chat in chat_list:
			chat_id = chat['uuid']
			all_data[chat_id]['agents'] = chat['agents']
			all_data[chat_id]['style'] = chat['scenario']['styles']

			all_data[chat_id]['resp_time_dict'], all_data[chat_id]['resp_time_avg'], all_data[chat_id]['resp_time_dict_select'], all_data[chat_id]['resp_time_avg_select'] = calc_response_times(chat['events'], chat['agents'])

	print 'read all chat jsons'

	# read LID TSVs
	# creates ['txt_dict'] and ['lbl_dict'] entries per chat in all_data
	# each of those are dict[utt_num] = list(words or lbl)
	for lid_file in file_names['lid_tsv']:
		with open(lid_file) as f:
			for line in f.readlines():
				all_info = line.replace('\n', '').split('\t')

				# concat chat_id with utt-number
				# utt-number always has two digits (i.e. 3 -> 03)
				chat_id = all_info[1]
				utt_num = all_info[2].zfill(2)  #TODO: save as int, not str
				txt = all_info[3]  # single token
				lbl = all_info[4]
				if len(all_info) > 5:
					if all_info[5] != '':
						# use manually fixed LID tag instead, if applicable
						lbl = all_info[5]

				if 'txt_dict' not in all_data[chat_id]:
					all_data[chat_id]['txt_dict'] = defaultdict(list)
					all_data[chat_id]['lbl_dict'] = defaultdict(list)

				all_data[chat_id]['txt_dict'][utt_num].append(txt)
				all_data[chat_id]['lbl_dict'][utt_num].append(int(lbl))
	print 'read all lid tsvs'

	# calc m and i per chat
	for chat_id in all_data:
		if not is_valid_chat(all_data, chat_id):
			continue

		lbl_lst = []
		lbl_dict = all_data[chat_id]['lbl_dict']
		for utt_num in sorted(lbl_dict.keys()):  # utt_num = '00', '01', ...
			words_01 = lbl_dict[utt_num]
			lbl_lst.append(words_01)

		all_data[chat_id]['m_idx'] = calc_m_idx(lbl_lst, one_user=True)
		all_data[chat_id]['i_idx'] = calc_i_idx(lbl_lst, one_user=True)

	return all_data


# ensure chat is present, has survey AND contains text
def is_valid_chat(full_data, chat_id):
	if chat_id not in full_data:
		return False

	return 'outcome' in full_data[chat_id] and 'txt_dict' in full_data[chat_id]


# 	returns style2chat: 	dict[style] = set(chats)
def get_style2chat(all_data):
	style2chat = defaultdict(list)

	for chat_id, chat_dict in all_data.iteritems():
		# try:
		style = chat_dict['style']
		# except:
		# 	import pdb; pdb.set_trace()
		# 	foo = 1
		style2chat[style].append(chat_id)

	return style2chat


# calculate strategies for a specified chat list
def get_general_cm_metrics(all_data, param_chat_list=None):

	styles = defaultdict(int)
	styles_txt = defaultdict(list)
	general_stats = {}
	num_cm_utt = 0
	num_eng_only = 0
	num_spa_only = 0
	num_total_utt = 0
	num_tokens = 0
	no_chat_ctr = 0
	outcome_ctr = 0
	num_cm_dialogues = 0
	is_cm_chat = False
	chat_lid_lsts = defaultdict(list)  # for calc m/i-idx across utts per chat
	strat_dict = {}  # for calc m/i-idx across utts per chat
	avg_resp_times = []  # list of floats
	avg_resp_times_select = []  # list of floats

	if param_chat_list:
		chat_list = param_chat_list

	else:
		chat_list = all_data.keys()
		print 'using all chat ids'

	for chat_id in sorted(chat_list):
		# if chat_id not in all_data:
		# 	print 'ERROR: Chat ID not valid: {}'.format(chat_id)
		# 	no_chat_ctr += 1
		# 	continue

		# if 'txt_dict' not in all_data[chat_id]:
		# 	# print 'Chat has no text: {}'.format(chat_id)
		# 	no_chat_ctr += 1
		# 	continue

		if not is_valid_chat(all_data, chat_id):
			no_chat_ctr += 1
			continue

		txt_dict = all_data[chat_id]['txt_dict']
		lbl_dict = all_data[chat_id]['lbl_dict']
		avg_resp_times.append(all_data[chat_id]['resp_time_avg'])
		avg_resp_times_select.append(all_data[chat_id]['resp_time_avg_select'])
		strat_dict[chat_id] = defaultdict(int)  # alternately: be simple list
		outcome_ctr += int(all_data[chat_id]['outcome'])

		for utt_num in sorted(txt_dict.keys()):  # utt_num = '00', '01', ...
			num_total_utt += 1
			words_01 = lbl_dict[utt_num]
			chat_lid_lsts[chat_id].append(words_01)
			num_tokens += len(words_01)

			# only process if utt = code-mixed
			# also get counts for if monolingual
			if not (0 in words_01 and 1 in words_01):
				if 0 in words_01:
					num_spa_only += 1
					strat_dict[chat_id]['spa'] += 1
					# print 'SPA: ', data['txt'][i]
				elif 1 in words_01:
					num_eng_only += 1
					strat_dict[chat_id]['eng'] += 1
					# print 'ENG: ', data['txt'][i]
				else:
					strat_dict[chat_id]['unk'] += 1

				continue  # move on to next UTT

			num_cm_utt += 1
			is_cm_chat = True
			# unsure why strip last word...
			words_lst = txt_dict[utt_num]
			if not words_lst:
				import pdb; pdb.set_trace()
			if words_lst[-1] == '':
				print 'trimming end', words_lst
				words_lst = words_lst[:-1]

			# store user strategies back into another dict, to be returned
			user_style = process_tags(words_01, words_lst, styles, styles_txt, finegrain=False)
			strat_dict[chat_id][user_style] += 1

		if is_cm_chat:
			num_cm_dialogues += 1

		is_cm_chat = False

	general_stats['dialogues'] = len(chat_list) - no_chat_ctr
	general_stats['num_success'] = outcome_ctr
	general_stats['cm_dial'] = num_cm_dialogues
	general_stats['utts'] = num_total_utt
	general_stats['cm_utt'] = num_cm_utt
	general_stats['sp_utt'] = num_spa_only
	general_stats['en_utt'] = num_eng_only
	general_stats['tokens'] = num_tokens
	general_stats['avg_rt'] = sum(avg_resp_times) / len(avg_resp_times)
	general_stats['avg_rt_select'] = sum(avg_resp_times_select) / len(avg_resp_times_select)

	# style_calcs = calc_styles(styles)

	# import pdb; pdb.set_trace()
	general_stats['m-idx'] = calc_m_idx(chat_lid_lsts)
	general_stats['i-idx'] = calc_i_idx(chat_lid_lsts)
	# print 'M-IDX:', calc_m_idx(chat_lid_lsts)
	# print 'I-IDX:', calc_i_idx(chat_lid_lsts)

	# print
	# print '*'*20
	# print

	# return styles_txt
	return {'general': general_stats, 'style': styles, 'style_utt': styles_txt, 'user_styles': strat_dict}


# all_data must be dict of key=style, val=dict from get_general_cm_metrics()
# this will probably break if given any different kind of format...
def viz_general(all_data):
	# styles_list = sorted(all_data.keys())
	styles_list = ['sp_lex', 'sp_lex_soc', 'en_lex', 'en_lex_soc', 'sp2en', 'sp2en_soc', 'en2sp', 'en2sp_soc', 'sp_mono', 'en_mono', 'random']
	# print styles_list
	all_dial = sum([all_data[style]['general']['dialogues'] for style in styles_list])
	avg_dial = statistics.mean([all_data[style]['general']['dialogues'] for style in styles_list])
	all_cm_dial = sum([all_data[style]['general']['cm_dial'] for style in styles_list])

	all_utt = sum([all_data[style]['general']['utts'] for style in styles_list])
	all_tok = sum([all_data[style]['general']['tokens'] for style in styles_list])
	all_cm = sum([all_data[style]['general']['cm_utt'] for style in styles_list])
	all_sp = sum([all_data[style]['general']['sp_utt'] for style in styles_list])
	all_en = sum([all_data[style]['general']['en_utt'] for style in styles_list])
	all_cm_perc = '{:.2f}'.format(float(all_cm)/all_utt)
	all_sp_perc = ['{:.2f}'.format(float(all_sp)/all_utt)]
	all_en_perc = ['{:.2f}'.format(float(all_en)/all_utt)]
	avg_m = statistics.mean([all_data[style]['general']['m-idx'] for style in styles_list])
	var_m = statistics.stdev([all_data[style]['general']['m-idx'] for style in styles_list])
	avg_i = statistics.mean([all_data[style]['general']['i-idx'] for style in styles_list])
	var_i = statistics.stdev([all_data[style]['general']['i-idx'] for style in styles_list])
	avg_rt = statistics.mean([all_data[style]['general']['avg_rt'] for style in styles_list])
	var_rt = statistics.stdev([all_data[style]['general']['avg_rt'] for style in styles_list])
	avg_rt_select = statistics.mean([all_data[style]['general']['avg_rt_select'] for style in styles_list])
	var_rt_select = statistics.stdev([all_data[style]['general']['avg_rt_select'] for style in styles_list])
	avg_outcome = sum([all_data[style]['general']['num_success'] for style in styles_list]) / float(all_dial)
	# avg_outcome = statistics.mean([all_data[style]['general']['num_success']/float(all_data[style]['general']['dialogues']) for style in styles_list])
	# var_outcome = statistics.stdev([all_data[style]['general']['num_success']/float(all_data[style]['general']['dialogues']) for style in styles_list])
	# all_perc_outcome = all_outcome / float(all_dial)

	# print '\t'.join(['% spa utt'] + all_sp_perc + ['{:.2f}'.format(all_data[style]['general']['sp_utt']/float(all_data[style]['general']['utts'])) for style in styles_list])
	# print '\t'.join(['% eng utt'] + all_en_perc + ['{:.2f}'.format(all_data[style]['general']['en_utt']/float(all_data[style]['general']['utts'])) for style in styles_list])
	# print

	print 'all tok', all_tok
	print 'all dial', all_dial

	print 'WITH SELECT'
	print 'bot strat\t# dialogues\t% success\t% dial CM from user\tavg utts\tavg tokens\t% CM utt\tavg RT\tm\ti'
	print 'average  \t{:.2f}\t{:.2f}\t{:.2f}\t{:.2f}\t{:.2f}\t{}\t{:.2f}\t{:.2f}\t{:.2f}'.format(avg_dial, avg_outcome, all_cm_dial / float(all_dial), all_utt / float(all_dial), all_tok / float(all_utt), all_cm_perc, avg_rt_select, avg_m, avg_i)
	for style in styles_list:
		print '{}\t{}\t{:.2f}\t{:.2f}\t{:.2f}\t{:.2f}\t{:.2f}\t{:.2f}\t{:.2f}\t{:.2f}'.format(style.ljust(9), all_data[style]['general']['dialogues'], all_data[style]['general']['num_success']/float(all_data[style]['general']['dialogues']), all_data[style]['general']['cm_dial']/float(all_data[style]['general']['dialogues']), all_data[style]['general']['utts']/float(all_data[style]['general']['dialogues']), all_data[style]['general']['tokens']/float(all_data[style]['general']['utts']), all_data[style]['general']['cm_utt']/float(all_data[style]['general']['utts']), all_data[style]['general']['avg_rt_select'], all_data[style]['general']['m-idx'], all_data[style]['general']['i-idx'])

	print
	print '*'*20
	print
	rt_list = np.array([all_data[style]['general']['avg_rt_select'] for style in styles_list])
	num_toklist = np.array([all_data[style]['general']['tokens']/float(all_data[style]['general']['utts']) for style in styles_list])
	rt_numtok_r_val, rt_numtok_p_val = pearsonr(rt_list, num_toklist)
	print '\trt_numtok\t{:.4f}\t{:.4f}'.format(rt_numtok_r_val, rt_numtok_p_val)

	fig, ax = plt.subplots()
	plt.scatter(rt_list, num_toklist)
	z = np.polyfit(rt_list, num_toklist, 1)
	p = np.poly1d(z)
	# annotate
	for i, style in enumerate(styles_list):
		plt.annotate(style, (rt_list[i] + 0.1, num_toklist[i]))

	plt.plot(rt_list, p(rt_list), "r--")
	# the line equation:
	print "y=%.6fx+(%.6f)" % (z[0], z[1])
	plt.xlabel('Avg Response Time (sec)')
	plt.ylabel('Avg # Tokens per Utterance')
	plt.show()

	print
	print '*'*20
	print

	# print 'WITHOUT SELECT'
	# print 'bot strat\t# dialogues\t% dial CM from user\tavg utts\tavg tokens\t% CM utt\tavg RT'
	# print 'average  \t{}\t{:.2f}\t{:.2f}\t{:.2f}\t{}\t{:.2f}'.format(all_dial, all_cm_dial / float(all_dial), all_utt / float(all_dial), all_tok / float(all_utt), all_cm_perc, avg_rt)
	# for style in styles_list:
	# 	print '{}\t{}\t{:.2f}\t{:.2f}\t{:.2f}\t{:.2f}\t{:.2f}'.format(style.ljust(9), all_data[style]['general']['dialogues'], all_data[style]['general']['cm_dial']/float(all_data[style]['general']['dialogues']), all_data[style]['general']['utts']/float(all_data[style]['general']['dialogues']), all_data[style]['general']['tokens']/float(all_data[style]['general']['utts']), all_data[style]['general']['cm_utt']/float(all_data[style]['general']['utts']), all_data[style]['general']['avg_rt'])

	# print
	# print '*'*20
	# print
	# rt_list = np.array([all_data[style]['general']['avg_rt'] for style in styles_list])
	# num_toklist = np.array([all_data[style]['general']['tokens']/float(all_data[style]['general']['utts']) for style in styles_list])
	# rt_numtok_r_val, rt_numtok_p_val = pearsonr(rt_list, num_toklist)
	# print '\trt_numtok\t{:.4f}\t{:.4f}'.format(rt_numtok_r_val, rt_numtok_p_val)

	# plt.scatter(rt_list, num_toklist)
	# z = np.polyfit(rt_list, num_toklist, 1)
	# p = np.poly1d(z)
	# plt.plot(rt_list,p(rt_list),"r--")
	# # the line equation:
	# print "y=%.6fx+(%.6f)"%(z[0],z[1])
	# plt.show()

	'''user_style_list = [style for style in styles_list if not style.endswith('_soc') and not style == 'random']
	user_style_list.append('neither')
	user_style_names = '\t'.join(user_style_list)  # 4 styles + neither, like miami and twitter calculations

	print 'bot strat\tm-idx\ti-idx\t{}'.format(user_style_names)
	print 'average  \t{:.2f}\t{:.2f}'.format(avg_m, avg_i)
	#UNNECESSARY (done in viz_cm_style()), also BUGGY (everything bins to "neither")
	for style in styles_list:
		#TODO: use this to report different kind of entrainment score!! Ratio maybe?
		# accumulate counts of each utterance's user style
		# user_style_counts = defaultdict(int)
		# user_style_norm = {}

		# for chatid, style_dict in all_data[style]['user_styles'].iteritems():
		# 	for user_strat, count in style_dict.iteritems():
		# 		user_style_counts[user_strat] += count

		# print user_style_counts

		# total_cm_denom = float(sum([user_style_counts[user_style] for user_style in user_style_list]))
		# print total_cm_denom
		# if total_cm_denom == 0:
		print '{}\t{:.2f}\t{:.2f}'.format(style.ljust(9), all_data[style]['general']['m-idx'], all_data[style]['general']['i-idx'])
			# continue

		# for user_style in user_style_list:
		# 	user_style_norm[user_style] = user_style_counts[user_style] / total_cm_denom

		# user_style_norm_txt = '\t'.join(['{:.2f}'.format(user_style_norm[style_name]) for style_name in user_style_list])

		# print '{}\t{:.2f}\t{:.2f}\t{}'.format(style.ljust(9), all_data[style]['general']['m-idx'], all_data[style]['general']['i-idx'], user_style_norm_txt)
	'''

# taken from http://scikit-learn.org/stable/auto_examples/model_selection/plot_confusion_matrix.html
def plot_confusion_matrix(cm, classes, normalize=False, title='Strategy Matrix', cmap=plt.cm.Blues):
	"""
	This function prints and plots the confusion matrix.
	Normalization can be applied by setting `normalize=True`.
	"""
	if normalize:
		cm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
	# 	# print("Normalized")
	# else:
	# 	print('NOT Normalized')

	# print(cm)

	plt.imshow(cm, interpolation='nearest', cmap=cmap)
	plt.title(title)
	plt.colorbar()
	tick_marks = np.arange(len(classes))
	plt.xticks(tick_marks, classes, rotation=45)
	plt.yticks(tick_marks, classes)

	fmt = '.2f' if normalize else 'd'
	thresh = cm.max() / 2.
	for i, j in itertools.product(range(cm.shape[0]), range(cm.shape[1])):
		plt.text(j, i, format(cm[i, j], fmt),
				 horizontalalignment="center",
				 color="white" if cm[i, j] > thresh else "black")

	plt.tight_layout()
	plt.ylabel('Bot Strategy')
	plt.xlabel('User Strategy')


# pass in dict where dict[style] = style_dict from get_general_cm_metrics()
# style key is of form 'en2sp', not 's-1'
# @param is_social: 0 = no social, 1 = social only, 2 = combined
#TODO: is_social = 1 does NOT work
def viz_cm_style(all_data, is_social=2):
	name_map = {'c-0': 'sp_lex', 'c-1': 'en_lex', 's-1': 'en2sp', 's-0': 'sp2en'}
	name_map_flip = {d: k for k, d in name_map.iteritems()}
	style_subset = ['sp_lex', 'en_lex', 'sp2en', 'en2sp']
	style_subset_rand = ['sp_lex', 'en_lex', 'sp2en', 'en2sp', 'random']
	# style_social_bots = [s + '_soc' for s in style_subset]
	style_social_rand = ['sp_lex_soc', 'en_lex_soc', 'sp2en_soc', 'en2sp_soc', 'random']
	all_styles = style_subset + style_social_rand  # all 9 (reg4, social4, rand1)

	style_bots = style_subset_rand
	# 0 = no social, 1 = social only, 2 = combined
	if is_social == 1:
		style_bots = style_social_rand

	elif is_social == 2:
		style_bots = all_styles

	zipped_list = []
	for style_bot in style_bots:
		for style_user in style_subset:
			num_entries = 0
			style_user_cs01 = name_map_flip[style_user]  # en2sp -> s-1
			if style_user_cs01 in all_data[style_bot]['style']:
				num_entries = all_data[style_bot]['style'][style_user_cs01]

			# print style_bot, style_user, num_entries
			# zipped_list.extend([(style_bot.replace('_soc', ''), style_user) for i in range(num_entries)])
			zipped_list.extend([(style_bot, style_user) for i in range(num_entries)])  # don't collapse '_soc' label
		# print '*'*5

	bot_list = [x for x, y in zipped_list]
	user_list = [y for x, y in zipped_list]

	# Compute confusion matrix
	cnf_matrix = confusion_matrix(bot_list, user_list, labels=style_bots)  # y_test, y_pred
	np.set_printoptions(precision=2)

	# Plot non-normalized confusion matrix
	plt.figure()
	plot_confusion_matrix(cnf_matrix, classes=style_bots,
						  title='Strategy matrix, without normalization')

	# Plot normalized confusion matrix
	plt.figure()
	plot_confusion_matrix(cnf_matrix, classes=style_bots, normalize=True,
						  title='Normalized strategy matrix')

	plt.show()


# use linear regression (or other model) to predict binary success
# later: predict success as multiclass ranging values
# use chatids from style_dict (removes chats w/o text)
# style_data = dict[bot_style][chat_id], result from looping get_general_cm_metrics
# general_data = dict[chat_id], result from load_all_data()
def predict_success(general_data, style_data, filter_chatlist=None):
	# grab relevant features
	# X : numpy array or sparse matrix of shape [n_samples, n_features]
	# y : numpy array of shape [n_samples, n_targets]
	bot_style_list = ['sp_lex', 'en_lex', 'sp2en', 'en2sp', 'sp_lex_soc', 'en_lex_soc', 'sp2en_soc', 'en2sp_soc', 'random']
	user_style_list = ['sp_lex', 'en_lex', 'sp2en', 'en2sp', 'neither', 'spa', 'eng', 'unk']  # expanded set
	# user_style_list = ['sp_lex', 'en_lex', 'sp2en', 'en2sp']

	# flatten bot styles
	# print general_data.keys()
	chat_key_dict = {}
	for style, style_dict in style_data.iteritems():
		for chat_id, chat_dict in style_dict['user_styles'].iteritems():
			if filter_chatlist:
				if chat_id not in filter_chatlist:
					continue

			if 'outcome' not in general_data[chat_id]:  # chat w/o survey
				continue

			# info_dict = chat_dict
			# info_dict['bot_style'] = style  # not necessary
			chat_key_dict[chat_id] = chat_dict

	all_X = []
	all_y = []

	# use chatids from style_dict (removes chats w/o text)
	for chat_id, style_dict in chat_key_dict.iteritems():
		# ft_01 = bot style (condition), one-hot encoded
		ft_01 = [0] * len(bot_style_list)
		chat_bot_style = general_data[chat_id]['style']
		# print style_dict
		# break
		ft_01[bot_style_list.index(chat_bot_style)] = 1  # type=int (index)

		# ft_02 = user style (normalized)  # len = 4 or 8
		ft_02_raw = [0] * len(user_style_list)
		for user_style in user_style_list:
			style_utt_count = style_dict[user_style]  # int
			if style_utt_count == 0:
				#bug: all CM strategies are zero, they go here
				continue
			# print 'HERE(@*#U($@*U#$*#U('
			ft_02_raw[user_style_list.index(user_style)] = style_utt_count

		ft_02_norm = normalize(np.array(ft_02_raw).reshape(-1, 1), axis=0, norm='max')

		# print ft_02_raw
		# ft_03 = entrainment. defined 1 if user has copied bot at least 1x, else -1
		if chat_bot_style == 'random':
			ft_03_entrain = [-1]
		else:
			chat_bot_style = chat_bot_style.replace('_soc', '')  # remove "_soc"
			# print chat_bot_style
			# print user_style_list.index(chat_bot_style)
			# print ft_02_raw[user_style_list.index(chat_bot_style)]
			ft_03_entrain = [-1]
			if ft_02_raw[user_style_list.index(chat_bot_style)] > 0.0:
				ft_03_entrain = [1]
				# print 'FOUND*#(@*$(@($@$#&&$('


		# print ft_03_entrain

		# flatten all feature lists, can pack many lists into tuple passed to concat
		flat_feats = np.concatenate((ft_01, ft_02_norm, ft_03_entrain), axis=None)
		# print flat_feats
		all_X.append(flat_feats)
		outcome = int(general_data[chat_id]['outcome']) * 2 - 1  # map [0, 1] to [-1, 1]
		all_y.append(outcome)

	# do kfold
	all_X = np.array(all_X)
	all_y = np.array(all_y)
	kf = KFold(n_splits=5, shuffle=True, random_state=32)
	kf.get_n_splits(all_X)
	for train_index, test_index in kf.split(all_X):
		# print("TRAIN:", train_index, "TEST:", test_index)
		X_train, X_test = all_X[train_index], all_X[test_index]
		y_train, y_test = all_y[train_index], all_y[test_index]

		# train model
		# model = LinearRegression()
		model = LinearRegression(normalize=True)
		model.fit(X_train, y_train)

		# predict success
		y_pred_orig = model.predict(X_test)
		# print y_pred_orig
		# y_pred = [int(np.floor(guess + 0.5)) * 2 - 1 for guess in y_pred]
		try:
			y_pred = [int(guess / abs(guess)) for guess in y_pred_orig]
		except ValueError:
			y_pred = [int((guess + 0.01) / abs(guess + 0.01)) for guess in y_pred_orig]

		# print 'PRED', y_pred
		# print 'FACT', y_test

		# print results and weights
		target_names = ['no friend', 'friend']
		ft_names = bot_style_list + user_style_list + ['entrain_1x']
		print(classification_report(y_test, y_pred, target_names=target_names))
		print 'WEIGHTS'
		# print model.coef_
		for i, weight in enumerate(model.coef_):
			print ft_names[i], weight
		print '*'*20
		print


# from original loaded data, calc correlations b/w m/i-idxs and success
# measures of success: binary,
#TODO: perhaps create scatterplot
def pearsons_cm_success(general_data, cm_data=None, filter_chatlist=None):
	m_list = []
	i_list = []
	entrain_list = []
	social_list = []

	results_dict = defaultdict(list)
	for chat_id in general_data:
		if not is_valid_chat(general_data, chat_id):
			continue

		if filter_chatlist:
			if chat_id not in filter_chatlist:
				continue
		# m_idx = general_data[chat_id]['m_idx']
		# i_idx = general_data[chat_id]['i_idx']
		# bin_success = int(general_data[chat_id]['outcome'])
		# num_turn = len(general_data[chat_id]['lbl_dict'].keys())

		m_list.append(general_data[chat_id]['m_idx'])
		i_list.append(general_data[chat_id]['i_idx'])
		results_dict['bin_success'].append(int(general_data[chat_id]['outcome']))
		results_dict['num_turn'].append(len(general_data[chat_id]['lbl_dict'].keys()))
		results_dict['n01_i_understand'].append(int(general_data[chat_id]['n01_i_understand']))
		results_dict['n02_cooperative'].append(int(general_data[chat_id]['n02_cooperative']))
		results_dict['n03_human'].append(int(general_data[chat_id]['n03_human']))
		results_dict['n04_understand_me'].append(int(general_data[chat_id]['n04_understand_me']))
		results_dict['n05_chat'].append(int(general_data[chat_id]['n05_chat']))
		results_dict['n06_texts'].append(int(general_data[chat_id]['n06_texts']))
		results_dict['n07_tech'].append(int(general_data[chat_id]['n07_tech']))

		# entrainment (optional)
		if not cm_data:
			continue

		# ft_03 = entrainment. defined 1 if user has copied bot at least 1x, else 0
		chat_bot_style = general_data[chat_id]['style']
		social_val = 0
		if '_soc' in chat_bot_style:
			social_val = 1

		if chat_bot_style == 'random':
			entrain_val = 1
		else:
			chat_bot_style = chat_bot_style.replace('_soc', '')  # remove "_soc"
			# print chat_bot_style
			# print user_style_list.index(chat_bot_style)
			# print ft_02_raw[user_style_list.index(chat_bot_style)]
			entrain_val = 0
			if cm_data['user_styles'][chat_id][chat_bot_style] > 0:
				entrain_val = 1

		# print entrain_val
		entrain_list.append(entrain_val)
		social_list.append(social_val)

	print 'NUM CHATS USED: {}\n'.format(len(results_dict['bin_success']))
	for success_type, success_list in results_dict.iteritems():
		print success_type.upper()
		if cm_data:
			entrain_r_val, entrain_p_val = pearsonr(entrain_list, success_list)
			social_r_val, social_p_val = pearsonr(social_list, success_list)
			print '\tentrain\t{:.4f}\t{:.4f}'.format(entrain_r_val, entrain_p_val)
			print '\tsocial\t{:.4f}\t{:.4f}'.format(social_r_val, social_p_val)

		m_r_val, m_p_val = pearsonr(m_list, success_list)
		i_r_val, i_p_val = pearsonr(i_list, success_list)
		print '\tm-idx\t{:.4f}\t{:.4f}'.format(m_r_val, m_p_val)
		print '\ti-idx\t{:.4f}\t{:.4f}'.format(i_r_val, i_p_val)


def main():
	all_data = load_all_data('src/files_list_fix.txt')
	style2chat_dict = get_style2chat(all_data)
	for style, chat_list in style2chat_dict.iteritems():
		get_general_cm_metrics(chat_list, all_data)


if __name__ == '__main__':
	main()
