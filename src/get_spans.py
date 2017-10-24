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
from parse_miami import load_data
# import math
# import argparse

__author__ = 'Emily Ahn'

if __name__=='__main__':
    data_folder_path = sys.argv[1]

    all_data = load_data(data_folder_path)
    for dialog_id, dialog in all_data.items():
        for spkr in dialog.keys():
        	
        	for turn in dialog[spkr]['words']:
        		turn_01 = []
        		for word in turn:
	        		if word.endswith("_eng"):
	        			turn_01.append(1)
	        		if word.endswith("_spa"):
	        			turn_01.append(0)



