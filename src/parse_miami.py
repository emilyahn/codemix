#!/usr/bin/env python

""" Date created: 10/17/2017
    Date modified: 10/17/2017
    *************************
    process Miami txt files

"""

from collections import defaultdict
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

        

if __name__=='__main__':
    all_data = {}
    data_folder_path = sys.argv[1]
    for filename in os.listdir(data_folder_path):
        filename_path = os.path.join(data_folder_path,filename)
        if not filename.endswith('_parsed.txt'): continue #skips 'sastre3'
        dialog_id, dialog_dict = process_one_file(filename_path)
        all_data[dialog_id] = dialog_dict

    # print all_data['sastre10'].keys()
    # print all_data['zeledon8']['FLA']['words'][:20]
    # print len(all_data['zeledon8']['MAR']['time_start'])
    for key, dialog in all_data.items():
        print key, len(dialog.keys())
