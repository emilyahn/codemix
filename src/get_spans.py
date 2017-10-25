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

def plot_one_spkr(spkr, turn_dict):
	# [0] = list of Spanish span lengths
	# [1] = list of English span lengths
	span_list = np.array(turn_dict[0])
	eng_list = np.array(turn_dict[1])

	xmin = 0 #min([np.floor(min(span_list)), np.floor(min(eng_list))])
	xmax = max([np.ceil(max(span_list)), np.ceil(max(eng_list))])
	num_bins = xmax

	plot_bins = np.linspace(xmin, xmax, num_bins)

	n, bins, patches = plt.hist(span_list, bins=plot_bins, alpha=0.5, label='spa', color='b')
	n, bins, patches = plt.hist(eng_list, bins=plot_bins, alpha=0.5, label='eng', color='r')


	plt.ylabel('freq')
	plt.xlabel('length of span (# words)')
	plt.title(spkr + ': histogram of spa & eng')
	plt.legend(loc='upper right')

	plt.show()

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

	spkr = 'MAR' #test example
	plot_one_spkr(spkr, all_data[spkr_info[spkr][0]][spkr]['turns'])
	


