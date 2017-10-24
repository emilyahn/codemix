#!/usr/bin/env python

""" Date created: 10/17/2017
    Date modified: 10/23/2017
    *************************
    process Miami txt files
    To run:
        ./parse_miami.py ../data/miami/txt/

"""

from collections import defaultdict, Counter
import os, sys, re
# import math
# import argparse

__author__ = 'Emily Ahn'

with open('ignore_words.txt') as f:
    ignore_words = [line.replace('\n','') for line in f.readlines()]

# dialog_dict   [spkr1] ->  ['time_start'] = list of floats
#                           ['time_end'] = list of floats
#                           ['words'] = list of (list of words)
#               [spkr2] -> ...
def process_one_file(filename):
    
    dialog_dict = {} 
    dialog_id = os.path.basename(filename).replace('_parsed.txt','')

    with open(filename) as f:
        total = [line.replace('\n','') for line in f.readlines()]

    for i, line in enumerate(total):
        turn = line.split()

        # handle spkr ids
        spkrid = turn[2]
        spkr = check_spkr(spkrid, total, i)
        if not spkr: continue # returned None, thus line was non-documented speaker

        if not spkr in dialog_dict:
            dialog_dict[spkr] = defaultdict(list)

        dialog_dict[spkr]['time_start'].append(float(turn[0]))
        dialog_dict[spkr]['time_end'].append(float(turn[1]))
        
        switch_to_spa = False
        words = []
        for word in turn[3:]:
        # clean words to capture only vocab spoken in "_eng" and "_spa"
        # change this to be a flag upon input, later
            if word in ignore_words: continue
            if bool(re.search(r'\w+sengspa\w+', word)): continue
            if bool(re.search(r'\w*_engspa', word)): continue
            if word == 'spa_eng':
                switch_to_spa = True
                continue
            if switch_to_spa:
                word = word.replace('_eng','_spa')
            words.append(word)
        dialog_dict[spkr]['words'].append(words)
    return dialog_id, dialog_dict


# skip non-documented speakers or use previous turn's spkrid (can be recursive)
def check_spkr(spkrid, total, i):
    if spkrid in ['OSE','OSA','OSB']: # skip non-documented speakers
        return None
    if spkrid in ['eng_eng', 'spa_spa']: # use previous turn's spkrid
        newid = total[i-1].split()[2]
        if newid in ['OSE','OSA','OSB','eng_eng', 'spa_spa']:
            return check_spkr(newid, total, i-1)
        return newid
    return spkrid

def load_data(data_folder_path):
	all_data = {}
    
    for filename in os.listdir(data_folder_path):
        filename_path = os.path.join(data_folder_path,filename)
        if not filename.endswith('_parsed.txt'): continue #skips 'sastre3'
        dialog_id, dialog_dict = process_one_file(filename_path)
        all_data[dialog_id] = dialog_dict
    return all_data

# words_list must be 1-dimensional
def write_words2counts(words_list, outfile):
    counts = Counter(words_list)

    writer = open(outfile, 'w')
    for wordfreq in counts:
        writer.write("{} {}\n".format(counts[wordfreq], wordfreq))
    writer.close()

def write_spkr_wordfreq(all_data, out_folder_path):
    for dialog_id, dialog in all_data.items():
        for spkr in dialog.keys():
            flat_word_list = [item for sublist in dialog[spkr]['words'] for item in sublist]
            outfile = os.path.join(out_folder_path,dialog_id+'_'+spkr+'.txt')
            write_words2counts(flat_word_list, outfile)


def write_prior_counts(all_data, outfile):
    all_words = []
    for dialog_id, dialog in all_data.items():
        for spkr in dialog.keys():
            flat_word_list = [item for sublist in dialog[spkr]['words'] for item in sublist]
            all_words.extend(flat_word_list)
    write_words2counts(all_words, outfile)


def log_odds_gender(all_data, spkr_tsv, out_folder_path):
    with open(spkr_tsv) as f:
        total = {line.split()[0]: line.replace('\n','').split()[1:] for line in f.readlines()[1:]}

    male_words = []
    female_words = []
    male_outfile = os.path.join(out_folder_path,'male_freq.txt')
    female_outfile = os.path.join(out_folder_path,'female_freq.txt')

    for dialog_id, dialog in all_data.items():
        for spkr in dialog.keys():
            flat_word_list = [item for sublist in dialog[spkr]['words'] for item in sublist]
            if total[spkr][1] == 'M':
                male_words.extend(flat_word_list)
            else:
                female_words.extend(flat_word_list)
    write_words2counts(male_words, male_outfile)
    write_words2counts(female_words, female_outfile)

if __name__=='__main__':
    data_folder_path = sys.argv[1]
    # out_folder_path = sys.argv[2]

    all_data = load_data(data_folder_path)
    

    # TODO: sort freq highest to lowest (easier to skim count files)
    # write_spkr_wordfreq(all_data, out_folder_path)

    # prior_counts_file = os.path.join(out_folder_path,'all_prior_counts.txt')
    # write_prior_counts(all_data, prior_counts_file)

    # spkr_tsv = '../data/spkr_info_1017.tsv'
    # log_odds_gender(all_data, spkr_tsv, out_folder_path)


    #####################
    # examples of accessing all_data structure
    # print all_data['zeledon8']['FLA']['words'][:20]
    # print len(all_data['zeledon8']['MAR']['time_start'])

