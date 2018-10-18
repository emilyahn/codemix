first_chatids = su.get_first_chatids(fix_data)
with open('cocoa/eval/all_qual_0926.tsv', 'r') as f:
    with open('cocoa/eval/all_qual_firsttime_0926-2.tsv', 'w') as w:
        for line in f.readlines():
            if line.split()[0] in first_chatids:
                w.write(line)
