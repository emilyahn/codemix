#!/bin/sh
# commands to run on k10

# CODE=204-B
# lang=tam
CODE=$1
lang=$2

cp /home/awb/data/babel/${CODE}.tar.bz2 .
tar xjf ${CODE}.tar.bz2 &
# cp BABEL_BP_106_tagalog/README* .
mkdir babel_${lang}_extra
cp ${CODE}/BABEL_*/README* babel_${lang}_extra/
# mv *.txt *.tsv babel_tag_extra/
cp ${CODE}/BABEL_*/conversational/reference_materials/* babel_${lang}_extra/

mkdir babel_${lang}_trans
cp ${CODE}/BABEL_*/conversational/dev/transcription/*.txt babel_${lang}_trans/
