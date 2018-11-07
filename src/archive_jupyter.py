# first_chatids = su.get_first_chatids(fix_data)
with open('cocoa/eval/all_qual_0926.tsv', 'r') as f:
    with open('cocoa/eval/all_qual_unique_1031.tsv', 'w') as w:
        for line in f.readlines():
            if cc.is_valid_chat(fix_data, line.split()[0]):
                w.write(line)
