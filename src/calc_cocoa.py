from cm_metrics import calc_i_idx, calc_m_idx, calc_styles, process_tags
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
		# for now, just store agents and events
		for chat in chat_list:
			chat_id = chat['uuid']
			all_data[chat_id]['agents'] = chat['agents']
			all_data[chat_id]['events'] = chat['events']
			all_data[chat_id]['style'] = chat['scenario']['styles']
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
				utt_num = all_info[2].zfill(2)
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

	return all_data


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
def get_general_cm_metrics(chat_list, all_data):

	styles = defaultdict(int)
	styles_txt = defaultdict(list)
	general_stats = {}
	num_cm_utt = 0
	num_eng_only = 0
	num_spa_only = 0
	num_total_utt = 0
	num_tokens = 0
	no_chat_ctr = 0
	num_cm_dialogues = 0
	is_cm_chat = False
	chat_lid_lsts = defaultdict(list)  # for calc m/i-idx across utts per chat
	strat_dict = {}  # for calc m/i-idx across utts per chat

	for chat_id in sorted(chat_list):
		# import pdb; pdb.set_trace()
		if chat_id not in all_data:
			print 'ERROR: Chat ID not valid: {}'.format(chat_id)
			no_chat_ctr += 1
			continue

		if 'txt_dict' not in all_data[chat_id]:
			# print 'Chat has no text: {}'.format(chat_id)
			no_chat_ctr += 1
			continue

		txt_dict = all_data[chat_id]['txt_dict']
		lbl_dict = all_data[chat_id]['lbl_dict']
		strat_dict[chat_id] = defaultdict(int)  # alternately: be simple list

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
	general_stats['cm_dial'] = num_cm_dialogues
	general_stats['utts'] = num_total_utt
	general_stats['cm_utt'] = num_cm_utt
	general_stats['sp_utt'] = num_spa_only
	general_stats['en_utt'] = num_eng_only
	general_stats['tokens'] = num_tokens

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


# this will probably break if given any different kind of format...
def viz_general(all_data):
	styles_list = sorted(all_data.keys())
	all_dial = sum([all_data[style]['general']['dialogues'] for style in styles_list])
	all_cm_dial = sum([all_data[style]['general']['cm_dial'] for style in styles_list])

	all_utt = sum([all_data[style]['general']['utts'] for style in styles_list])
	all_tok = sum([all_data[style]['general']['tokens'] for style in styles_list])
	all_cm = sum([all_data[style]['general']['cm_utt'] for style in styles_list])
	all_sp = sum([all_data[style]['general']['sp_utt'] for style in styles_list])
	all_en = sum([all_data[style]['general']['en_utt'] for style in styles_list])
	all_cm_perc = ['{:.2f}'.format(float(all_cm)/all_utt)]
	all_sp_perc = ['{:.2f}'.format(float(all_sp)/all_utt)]
	all_en_perc = ['{:.2f}'.format(float(all_en)/all_utt)]
	avg_m = sum([all_data[style]['general']['m-idx'] for style in styles_list])/len(styles_list)
	avg_i = sum([all_data[style]['general']['i-idx'] for style in styles_list])/len(styles_list)

	print '\t'.join(['----------\ttotal'] + [style[:7] for style in styles_list])
	print '\t'.join(['# dialogues'] + [str(all_dial)] + [str(all_data[style]['general']['dialogues']) for style in styles_list])
	print '\t'.join(['% dial w/ cm'] + ['{:.2f}'.format(all_cm_dial / float(all_dial))] + ['{:.2f}'.format(all_data[style]['general']['cm_dial']/float(all_data[style]['general']['dialogues'])) for style in styles_list])
	print '\t'.join(['# utts   '] + [str(all_utt)] + [str(all_data[style]['general']['utts']) for style in styles_list])
	print '\t'.join(['avg utts'] + ['{:.2f}'.format(all_utt / float(all_dial))] + ['{:.2f}'.format(all_data[style]['general']['utts']/float(all_data[style]['general']['dialogues'])) for style in styles_list])
	print '\t'.join(['# tokens'] + [str(all_tok)] + [str(all_data[style]['general']['tokens']) for style in styles_list])
	print '\t'.join(['avg tokens'] + ['{:.2f}'.format(all_tok / float(all_utt))] + ['{:.2f}'.format(all_data[style]['general']['tokens']/float(all_data[style]['general']['utts'])) for style in styles_list])
	print
	print '\t'.join(['# CM  utt'] + [str(all_cm)] + [str(all_data[style]['general']['cm_utt']) for style in styles_list])
	print '\t'.join(['% CM  utt'] + all_cm_perc + ['{:.2f}'.format(all_data[style]['general']['cm_utt']/float(all_data[style]['general']['utts'])) for style in styles_list])
	print '\t'.join(['# spa utt'] + [str(all_sp)] + [str(all_data[style]['general']['sp_utt']) for style in styles_list])
	print '\t'.join(['% spa utt'] + all_sp_perc + ['{:.2f}'.format(all_data[style]['general']['sp_utt']/float(all_data[style]['general']['utts'])) for style in styles_list])
	print '\t'.join(['# eng utt'] + [str(all_en)] + [str(all_data[style]['general']['en_utt']) for style in styles_list])
	print '\t'.join(['% eng utt'] + all_en_perc + ['{:.2f}'.format(all_data[style]['general']['en_utt']/float(all_data[style]['general']['utts'])) for style in styles_list])
	print
	print '\t'.join(['m idx   '] + ['{:.2f}'.format(avg_m)] + ['{:.2f}'.format(all_data[style]['general']['m-idx']) for style in styles_list])
	print '\t'.join(['i idx   '] + ['{:.2f}'.format(avg_i)] + ['{:.2f}'.format(all_data[style]['general']['i-idx']) for style in styles_list])


# taken from http://scikit-learn.org/stable/auto_examples/model_selection/plot_confusion_matrix.html
def plot_confusion_matrix(cm, classes,
							normalize=False,
							title='Strategy Matrix',
							cmap=plt.cm.Blues):
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


def main():
	all_data = load_all_data('src/files_list_fix.txt')
	style2chat_dict = get_style2chat(all_data)
	for style, chat_list in style2chat_dict.iteritems():
		get_general_cm_metrics(chat_list, all_data)


if __name__ == '__main__':
	main()
