from src import cm_metrics
from src import calc_cocoa
from src import new_metric_strat
from sklearn.metrics import cohen_kappa_score
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix
import csv
from collections import defaultdict
from sklearn.metrics import precision_recall_fscore_support
from sklearn.metrics import accuracy_score


hum_labels = ['se', 'es', 'sg', 'eg', 'n']
sys_labels = ['s-0', 's-1', 'c-0', 'c-1', 'neither']
sys_hum_map = {sys: hum for (hum, sys) in zip(hum_labels, sys_labels)}
hum_sys_map = {hum: sys for (hum, sys) in zip(hum_labels, sys_labels)}


# 1a
# outdict[id]['lbl' | 'txt'] = list
def gold_to_info(gold_dict, mi_data, tw_data, co_data):
	# idfile = './data/all_cm/random150.0211' #test
	outdict = defaultdict(dict)
	# with open(idfile, 'r') as f:
	# 	ids = [line.split('\t')[0] for line in f.readlines()]

	for idname in gold_dict:
		idshort = idname[:2]

		if idshort == 'tw':
			# twitter:
			if idname in tw_data['id']:
				id_idx = tw_data['id'].index(idname)
			# for i, tw_id in enumerate(tw_data['id']):
				outdict[idname]['lbl'] = tw_data['lbl'][id_idx]
				outdict[idname]['txt'] = tw_data['txt'][id_idx]

		elif idshort == 'mi':
			# miami:
			for dialog_id in mi_data.keys():
				for spkr in mi_data[dialog_id].keys():
					if idname in mi_data[dialog_id][spkr]['uttid']:
						id_idx = mi_data[dialog_id][spkr]['uttid'].index(idname)

						outdict[idname]['lbl'] = mi_data[dialog_id][spkr]['words_01'][id_idx]
						words_lst = cm_metrics.remove_lidtags_miami(mi_data[dialog_id][spkr]['words'][id_idx])
						if words_lst[-1] == '':
							words_lst = words_lst[:-1]
						outdict[idname]['txt'] = words_lst

		else:  # idshort == 'co'
		# if idshort == 'co':
			for chat_id in co_data:
				if chat_id in idname:
					utt_num = idname[-2:]  # str
					outdict[idname]['txt'] = co_data[chat_id]['txt_dict'][utt_num]
					outdict[idname]['lbl'] = co_data[chat_id]['lbl_dict'][utt_num]

	return outdict


# 1b
# all_info[id]['lbl' | 'txt'] = list
def info_to_strategy(gold_dict, all_info):  # , heur_name='new'
	# from file ids
	# get predictions of strategies based on classification heuristic
	heur_preds = []
	old_heur_preds = []
	debug_strat = 'eg'
	print 'DEBUG STRAT:', debug_strat
	uneven_ctr = 0

	for idname in all_info:
		if 'lbl' not in all_info[idname]:
			continue

		sys_strat, is_uneven = new_metric_strat.process_tags_2(all_info[idname]['lbl'], all_info[idname]['txt'])
		hum_strat = sys_hum_map[sys_strat]
		heur_preds.append(hum_strat)

		if is_uneven:
			# print idname
			uneven_ctr += 1

		old_sys_strat = cm_metrics.process_tags(all_info[idname]['lbl'], all_info[idname]['txt'])
		old_heur_preds.append(sys_hum_map[old_sys_strat])

		if gold_dict[idname] == debug_strat:
			if debug_strat != hum_strat:
				print hum_strat, ' '.join(all_info[idname]['txt'])



	print 'TOTAL UNEVEN', uneven_ctr

	gold_truths = [gold_dict[idname] for idname in all_info] #  if idname in gold_dict

	mi_idxs = [idname[:2] == 'mi' for idname in all_info]
	gold_truths_mi = [gold_dict[idname] for idname in all_info if idname[:2] == 'mi'] # if idname in gold_dict
	heur_preds_mi = [heur_preds[i] for i in range(len(gold_dict)) if mi_idxs[i]] # if idname in gold_dict
	check_annotations(gold_truths_mi, heur_preds_mi, "GOLD MI", "HEUR MI")

	tw_idxs = [idname[:2] == 'tw' for idname in all_info]
	gold_truths_tw = [gold_dict[idname] for idname in all_info if idname[:2] == 'tw'] # if idname in gold_dict
	heur_preds_tw = [heur_preds[i] for i in range(len(gold_dict)) if tw_idxs[i]] # if idname in gold_dict
	check_annotations(gold_truths_tw, heur_preds_tw, "GOLD TW", "HEUR TW")

	co_idxs = [idname[:2] == 'co' for idname in all_info]
	gold_truths_co = [gold_dict[idname] for idname in all_info if idname[:2] == 'co'] # if idname in gold_dict
	heur_preds_co = [heur_preds[i] for i in range(len(gold_dict)) if co_idxs[i]] # if idname in gold_dict
	check_annotations(gold_truths_co, heur_preds_co, "GOLD CO", "HEUR CO")

	check_annotations(gold_truths, heur_preds, "GOLD", "HEUR")
	# check_annotations(gold_truths, old_heur_preds, "GOLD", "OLD HEUR")


# calc cohen's kappa and print confusion matrix
# def check_annotations(annot_file, annot1_name, annot2_name):
def check_annotations(a1_labels, a2_labels, annot1_name, annot2_name):

	# a1_labels = []
	# a2_labels = []
	# with open(annot_file, 'r') as infile:
	# 	reader = csv.DictReader(infile)
	# 	for row in reader:
	# 		a1_labels.append(row[annot1_name])
	# 		a2_labels.append(row[annot2_name])

	# calc cohen
	# print 'COHEN', cohen_kappa_score(a1_labels, a2_labels, labels=hum_labels)
	print 'PRF', precision_recall_fscore_support(a1_labels, a2_labels, average='weighted')
	print 'ACC', accuracy_score(a1_labels, a2_labels)

	cnf_matrix = confusion_matrix(a1_labels, a2_labels, labels=hum_labels)  # , labels=style_bots // y_test, y_pred
	# print cnf_matrix
	# plt.figure()
	calc_cocoa.plot_confusion_matrix(cnf_matrix, hum_labels, xylabels=[annot2_name, annot1_name], normalize=True, title='strat compare', cmap=plt.cm.Blues)
	plt.figure()
	calc_cocoa.plot_confusion_matrix(cnf_matrix, hum_labels, xylabels=[annot2_name, annot1_name], normalize=False, title='strat compare', cmap=plt.cm.Blues)
	plt.show()


def get_gold_annot(annot_file):
	gold_set = {}
	with open(annot_file, 'r') as infile:
		reader = csv.DictReader(infile)
		for row in reader:
			uttid = row['ID']
			if row['joint']:
				gold_set[uttid] = row['joint']
			else:
				gold_set[uttid] = row['EA']

	return gold_set


def check_JB(jb_file, gold_dict):
	# jb_file = './data/all_cm/EA-CJ-JB_annot_0301_joint.csv'
	jb_dict = {}
	with open(jb_file, 'r') as infile:
		reader = csv.DictReader(infile)
		for row in reader:
			uttid = row['ID']
			jb_dict[uttid] = row['JB']

	gold_truths = [gold_dict[idname] for idname in jb_dict]
	jb_labels = [jb_dict[idname] for idname in jb_dict]

	print 'COHEN', cohen_kappa_score(gold_truths, jb_labels, labels=hum_labels)
	check_annotations(gold_truths, jb_labels, "GOLD", "JB")


if __name__ == '__main__':
	# check_annotations('./data/all_cm/EA-CJ_annot_0214_fix.csv', 'EA', 'CJ')
	print get_gold_annot('./data/all_cm/EA-CJ_annot_0225_joint.csv')
