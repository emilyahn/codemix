#!/usr/bin/env python

""" Date created: 10/09/2018
	Date modified: 10/09/2018
	*************************
	clean up Miami txt files, process indir, writes outdir
		* replace non-speech with tag [NS]
		* insert appropriate speaker tag when missing
		* flip some language tags when preceded by language-flip indicator

	To run:
		./clean_miami.py ../data/miami/txt/

"""
import os
import re
import sys


__author__ = 'Emily Ahn'

with open('./src/ignore_words.txt') as f:
	ignore_words = [line.strip() for line in f.readlines()]


def process_one_file(filename):

	out_lines = []

	with open(filename) as f:
		total = [line.strip() for line in f.readlines()]

	for i, line in enumerate(total):
		turn = line.split()

		# handle spkr ids
		spkrid = turn[2]
		spkr = check_spkr(spkrid, total, i)
		if not spkr:
			continue  # returned None, thus line was non-documented speaker

		switch_to_spa = False
		switch_to_eng = False
		words = []
		for word in turn[3:]:
			# clean words to capture only vocab spoken in "_eng" and "_spa"
			# change this to be a flag upon input, later
			if word in ignore_words:
				# replace with [NS_tag] (non-speech tag)
				nonspeech = word.split('_')[0]
				word = '[NS_{}]'.format(nonspeech)

			if bool(re.search(r'\w+sengspa\w+', word)):
				before, after = word.split('sengspa')
				lid_tag = after.split('_')[-1]
				word = '{}_{}'.format(before, lid_tag)

			if word == 'spa_eng':
				switch_to_spa = True
				continue

			if switch_to_spa:
				word = word.replace('_eng', '_spa')

			if word == 'eng_spa':
				switch_to_eng = True
				continue

			if switch_to_eng:
				word = word.replace('_spa', '_eng')

			words.append(word)

		out_lines.append('{} {} {} {}'.format(turn[0], turn[1], spkr, ' '.join(words)))

	return out_lines


# skip non-documented speakers or use previous turn's spkrid (can be recursive)
def check_spkr(spkrid, total, i):
	if spkrid in ['OSE', 'OSA', 'OSB']:  # skip non-documented speakers
		return None

	if spkrid in ['eng_eng', 'spa_spa']:  # use previous turn's spkrid
		newid = total[i-1].split()[2]
		return check_spkr(newid, total, i-1)

	return spkrid


def load_data(data_folder_path):
	all_data = {}

	for filename in os.listdir(data_folder_path):
		filename_path = os.path.join(data_folder_path, filename)
		# if not filename.endswith('_parsed.txt'):
		# 	continue  # skips 'sastre3'
		all_data[filename] = process_one_file(filename_path)

	return all_data


def write_files(out_folder_path, file_dict):
	os.mkdir(out_folder_path)

	for filename, outlines in file_dict.iteritems():
		outfile_path = os.path.join(out_folder_path, filename)
		writer = open(outfile_path, 'w')
		for line in outlines:
			writer.write("{}\n".format(line))
		writer.close()


if __name__ == '__main__':
	in_folder_path = sys.argv[1]
	out_folder_path = sys.argv[2]

	all_data = load_data(in_folder_path)
	write_files(out_folder_path, all_data)
