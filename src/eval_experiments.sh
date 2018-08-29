# eval scripts
# used after running cocoa/mturk_process.sh per batch

# cont1
# out_folder=cocoa/turk/amt_cont1_0615
# chat_file=${out_folder}/18content_0615_chat.json
# worker_file=${out_folder}/worker_ids.json
# survey_file=${out_folder}/18content_0615_surv.json
# crowd_files=${out_folder}/18content_batch_results.csv
# lid_outfile=${out_folder}/cont1_auto.tsv
# qual_outfile=${out_folder}/cont1_qual.tsv

# cont2
# out_folder=cocoa/turk/amt_cont2_0716
# chat_file=${out_folder}/cont_0716_chat.json
# worker_file=${out_folder}/worker_ids.json
# survey_file=${out_folder}/cont_0716_surv.json
# crowd_files=${out_folder}/cont_0718_batch.csv
# lid_outfile=${out_folder}/cont2_auto.tsv
# qual_outfile=${out_folder}/cont2_qual.tsv

# struct1
# out_folder=cocoa/turk/amt_struct1_0621
# chat_file=${out_folder}/19struct_0621_chat.json
# worker_file=${out_folder}/worker_ids.json
# survey_file=${out_folder}/19struct_0621_surv.json
# crowd_files=${out_folder}/19struct_batch.csv
# lid_outfile=${out_folder}/struct1_auto.tsv
# qual_outfile=${out_folder}/struct1_qual.tsv

# struct2
# out_folder=cocoa/turk/amt_struct2_0629_buggy
# chat_file=${out_folder}/struct_0629_trim17_chat.json
# worker_file=${out_folder}/struct_0629_batch_fix_worker_ids.json
# survey_file=${out_folder}/struct_0629_trim17_surv.json
# crowd_files=${out_folder}/struct_0629_batch_fix.csv
# lid_outfile=${out_folder}/struct2_auto.tsv
# qual_outfile=${out_folder}/struct2_qual.tsv

# soc1
# out_folder=cocoa/turk/amt_soc1_0724
# chat_file=${out_folder}/0720_social_chat.json
# worker_file=${out_folder}/worker_ids.json
# survey_file=${out_folder}/0720_social_surv.json
# crowd_files=${out_folder}/0720_social_batch.csv
# lid_outfile=${out_folder}/soc1_auto.tsv
# qual_outfile=${out_folder}/soc1_qual.tsv

# all4
# out_folder=cocoa/turk/fig8_0_all4
# chat_file=${out_folder}/fig8_0_chat.json
# worker_file=${out_folder}/worker_ids.json
# survey_file=${out_folder}/fig8_0_surv.json
# crowd_files="${out_folder}/job_0725.json ${out_folder}/job_0727.json"
# lid_outfile=${out_folder}/all4_auto.tsv
# qual_outfile=${out_folder}/all4_qual.tsv

# all8 (0731)
# out_folder=cocoa/turk/0731_all8
# chat_file=${out_folder}/0731_all8_chat.json
# worker_file=${out_folder}/worker_ids.json
# survey_file=${out_folder}/0731_all8_surv.json
# crowd_files="${out_folder}/batch_26.csv ${out_folder}/fig8_0731_97.json ${out_folder}/fig8_0728_30.json"
# lid_outfile=${out_folder}/0731_auto.tsv
# qual_outfile=${out_folder}/0731_qual.tsv

# all8 (0731)
# out_folder=cocoa/turk/0801_all8
# chat_file=${out_folder}/0801_all8_chat.json
# worker_file=${out_folder}/worker_ids.json
# survey_file=${out_folder}/0801_all8_surv.json
# crowd_files="${out_folder}/amt_0810_58.csv ${out_folder}/fig8_0806_100.json ${out_folder}/fig8_0809_100.json"
# lid_outfile=${out_folder}/0801_auto.tsv
# qual_outfile=${out_folder}/0801_qual.tsv

# random (0810)
out_folder=cocoa/turk/0810_rand
chat_file=${out_folder}/0810_rand_chat.json
worker_file=${out_folder}/worker_ids.json
survey_file=${out_folder}/0810_rand_surv.json
crowd_files="${out_folder}/amt_0815_27.csv ${out_folder}/fig8_0812_50.json"
lid_outfile=${out_folder}/0810_auto.tsv
qual_outfile=${out_folder}/0810_qual.tsv

python cocoa/eval/eval_cm.py --chat_file $chat_file --lid_outfile $lid_outfile

python cocoa/turk/process_survey.py --workers $worker_file --chats $chat_file --surveys $survey_file --crowdfiles $crowd_files --outfile $qual_outfile
