#!/usr/bin/env python

""" Date created: 10/23/2017
	Date modified: 10/23/2017
	*************************
	Get spans of English and Spanish within a turn of speech
	To run:
		./parse_miami.py ../data/miami/txt/

"""

from collections import defaultdict, Counter
import os, sys, re
from parse_miami import load_data, load_spkr_info
from itertools import groupby
import numpy as np
import matplotlib.pyplot as plt
# import math
# import argparse

__author__ = 'Emily Ahn'

def plot_one_spkr(title, sp_list, en_list):
	# [0] = list of Spanish span lengths
	# [1] = list of English span lengths
	span_list = np.array(sp_list)
	eng_list = np.array(en_list)

	xmin = 0 #min([np.floor(min(span_list)), np.floor(min(eng_list))])
	xmax = max([np.ceil(max(span_list)), np.ceil(max(eng_list))])
	num_bins = xmax

	plot_bins = np.linspace(xmin, xmax, num_bins)

	n, bins, patches = plt.hist(span_list, bins=plot_bins, alpha=0.5, label='spa', color='b')
	n, bins, patches = plt.hist(eng_list, bins=plot_bins, alpha=0.5, label='eng', color='r')

	plt.ylabel('freq')
	plt.xlabel('length of span (# words)')
	plt.title(title + ': histogram of spa & eng')
	plt.legend(loc='upper right')

	plt.show()

def plot_genders(all_data, spkr_info):
	male_spa_span_list = []
	male_eng_span_list = []
	female_spa_span_list = []
	female_eng_span_list = []

	for dialog_id, dialog in all_data.items():
		for spkr in dialog.keys():
			flat_eng_list = dialog[spkr]['turns'][1]
			flat_spa_list = dialog[spkr]['turns'][0]

			if spkr_info[spkr][1] == 'M':
				male_spa_span_list.extend(flat_spa_list)
				male_eng_span_list.extend(flat_eng_list)
			else:
				female_spa_span_list.extend(flat_spa_list)
				female_eng_span_list.extend(flat_eng_list)

	plot_one_spkr('Male', male_spa_span_list, male_eng_span_list)
	plot_one_spkr('Female', female_spa_span_list, female_eng_span_list)

# add span info of each spkr into all_data
def add_span_info(all_data):
	for dialog_id, dialog in all_data.items():
		for spkr in dialog.keys():

			turn_dict = defaultdict(list) 
			# [0] = list of Spanish span lengths
			# [1] = list of English span lengths
			for turn in dialog[spkr]['words']:
				turn_list = []
				for i, word in enumerate(turn):
					if word.endswith("_eng"):
						turn_list.append(1)
					if word.endswith("_spa"):
						turn_list.append(0)
				for k, g in groupby(turn_list):
					turn_dict[k].append(len(list(g)))
			all_data[dialog_id][spkr]['turns'] = turn_dict

if __name__=='__main__':
	data_folder_path = "../data/miami/txt/" # sys.argv[1]
	spkr_tsv = '../data/spkr_info_1017.tsv' # sys.argv[2]

	all_data = load_data(data_folder_path)
	spkr_info = load_spkr_info(spkr_tsv)

	# add span info of each spkr into all_data
	add_span_info(all_data)

	# spkr = 'MAR' #test example
	# plot_one_spkr(spkr, all_data[spkr_info[spkr][0]][spkr]['turns'][0], all_data[spkr_info[spkr][0]][spkr]['turns'][1])
	plot_genders(all_data, spkr_info)


