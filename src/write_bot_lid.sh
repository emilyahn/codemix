lid_outfile=cocoa/eval/bot_lid_tags.tsv

out_folder=cocoa/turk/amt_cont1_0615
chat_file=${out_folder}/18content_0615_chat.json
python cocoa/eval/eval_cm.py --chat_file $chat_file --lid_outfile $lid_outfile --get_bot

out_folder=cocoa/turk/amt_cont2_0716
chat_file=${out_folder}/cont_0716_chat.json
python cocoa/eval/eval_cm.py --chat_file $chat_file --lid_outfile $lid_outfile --get_bot

out_folder=cocoa/turk/amt_struct1_0621
chat_file=${out_folder}/19struct_0621_chat.json
python cocoa/eval/eval_cm.py --chat_file $chat_file --lid_outfile $lid_outfile --get_bot

out_folder=cocoa/turk/amt_struct2_0629_buggy
chat_file=${out_folder}/struct_0629_trim17_chat.json
python cocoa/eval/eval_cm.py --chat_file $chat_file --lid_outfile $lid_outfile --get_bot

out_folder=cocoa/turk/amt_soc1_0724
chat_file=${out_folder}/0720_social_chat.json
python cocoa/eval/eval_cm.py --chat_file $chat_file --lid_outfile $lid_outfile --get_bot

out_folder=cocoa/turk/fig8_0_all4
chat_file=${out_folder}/fig8_0_chat.json
python cocoa/eval/eval_cm.py --chat_file $chat_file --lid_outfile $lid_outfile --get_bot

out_folder=cocoa/turk/0731_all8
chat_file=${out_folder}/0731_all8_chat.json
python cocoa/eval/eval_cm.py --chat_file $chat_file --lid_outfile $lid_outfile --get_bot

out_folder=cocoa/turk/0801_all8
chat_file=${out_folder}/0801_all8_chat.json
python cocoa/eval/eval_cm.py --chat_file $chat_file --lid_outfile $lid_outfile --get_bot

out_folder=cocoa/turk/0810_rand
chat_file=${out_folder}/0810_rand_chat.json
python cocoa/eval/eval_cm.py --chat_file $chat_file --lid_outfile $lid_outfile --get_bot
