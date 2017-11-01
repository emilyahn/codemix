#!/usr/bin/env python

""" Date created: 10/23/2017
	Date modified: 10/31/2017
	*************************
	Plot things!
	* Get spans of English and Spanish within a turn of speech
	* get % spanish across dialogs -> HISTOGRAM


	To run:
		./parse_miami.py ../data/miami/txt/

"""

from collections import defaultdict, Counter
import os, sys, re
from parse_miami import load_data, load_spkr_info
import numpy as np
import matplotlib.pyplot as plt
# import math
# import argparse

__author__ = 'Emily Ahn'

# Example method invoking:
# plot_one_spkr('MAR', all_data[spkr_info['MAR'][0]]['MAR']['turns'][0], all_data[spkr_info[MAR][0]][MAR]['turns'][1])
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

# (# spa_words) / (# spa_words + # eng_words)
def plot_percent_spanish(all_data):
	perc_spa = []
	for dialog_id, dialog in all_data.items():
		num_spa_words = 0
		num_eng_words = 0
		for spkr in dialog.keys():
			num_spa_words += sum(all_data[dialog_id][spkr]['turns'][0])
			num_eng_words += sum(all_data[dialog_id][spkr]['turns'][1])
		perc_spa.append(num_spa_words * 100. / (num_spa_words + num_eng_words))

	perc_spa_list = np.array(perc_spa)

	for perc, dialog_id in sorted(zip(perc_spa, all_data.keys())):
		print '{:.2f}\t{}'.format(perc, dialog_id)

	# plot
	xmin = 0 #min([np.floor(min(span_list)), np.floor(min(eng_list))])
	xmax = 100 #max([np.ceil(max(span_list)), np.ceil(max(eng_list))])
	num_bins = 10

	plot_bins = np.linspace(xmin, xmax, num_bins)

	n, bins, patches = plt.hist(perc_spa_list, bins=plot_bins, alpha=0.5, label='spa', color='b')

	plt.ylabel('# Dialogues')
	plt.xlabel('Percentage of Spanish words')
	plt.title('Histogram of % Spanish in dialogues (Bins = {})'.format(num_bins))
	plt.legend(loc='upper right')

	# plt.show()


if __name__=='__main__':
	data_folder_path = "../data/miami/txt/" # sys.argv[1]
	spkr_tsv = '../data/spkr_info_1017.tsv' # sys.argv[2]

	all_data = load_data(data_folder_path)
	spkr_info = load_spkr_info(spkr_tsv)

	plot_percent_spanish(all_data)

	# spkr = 'MAR' #test example
	# plot_one_spkr(spkr, all_data[spkr_info[spkr][0]][spkr]['turns'][0], all_data[spkr_info[spkr][0]][spkr]['turns'][1])
	# plot_genders(all_data, spkr_info)


