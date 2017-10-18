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

def process_one_file(filename):
    
    dialog_dict = defaultdict(dict)
    dialog_id = os.path.basename(filename).replace('_parsed.txt','')

    with open(filename) as f:
        total = [line.replace('\n','') for line in f.readlines()]

    for i, line in enumerate(total):
        turn = line.split()
        time_start = turn[0]
        time_end = turn[1]

        # handle spkr ids
        spkrid = turn[2]
        check_spkr(spkrid, total, i)
        

def check_spkr(spkrid, total, i):
    if spkrid in ['OSE','OSA','OSB']: continue # skip non-documented speakers
        if spkrid in ['eng_eng', 'spa_spa']: # use previous turn's spkrid
            spkrid = total[i-1].split()[2]

        for word in turn[3:]:


if __name__=='__main__':
    all_data = defaultdict(dict) #{x: {}, y: {}}
    data_folder_path = sys.argv[1]
    for filename in os.listdir(data_folder_path):
        filename_path = os.path.join(data_folder_path,filename)
        if not filename.endswith('_parsed.txt'): continue
        process_one_file(filename_path)


