#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: Seraina Betschart
# date: December 2025
# Project eee-ScienceDebates
# Universität Zürich

#######################################################################################################################
# The purpose of this script is to process the youtube corpus into a form usable for the lcp corpus builder script.
# This includes:
# - Cutting the data file into several files based on comments under individual videos (lcp document level).
# - Word tokenization and lemmatization
# - Doing some manual error correction
# - Saving individual JSON files for the comments per video

# To use the script, specify input and output paths in the main() function at the bottom.
# (input contains the file which was processed with 'process_yt_corpus.py')

#######################################################################################################################

import pandas as pd
from germalemma import GermaLemma
import json
import os
import shutil
import re
import logging


def get_pper_lemmas(token):
    pper_mapping = {
        # 1st person singular
        "ich": "ich",
        "mich": "ich",
        "mir": "ich",
        # 2nd person singular
        "du": "du",
        "dich": "du",
        "dir": "du",
        # 3rd person masculine
        "er": "er",
        "ihn": "er",
        "ihm": "er",
        # 3rd person feminine
        "sie": "sie",
        # 3rd person neuter
        "es": "es",
        "'s": "es",
        # 1st person plural
        "wir": "wir",
        "uns": "wir",
        # 2nd person plural
        "ihr": "ihr",
        "euch": "ihr",
        # polite form
        "ihnen": "sie"
    }
    return pper_mapping.get(token)


def run_script(file, output_path):
    lemmatizer = GermaLemma()
    print(f"Import data from {file}")
    df = pd.read_csv(file)

    # cut corpus into individual documents (each document is the collection of comments under one video)
    grouped = df.groupby('video_title')
    tot_videos = len(grouped)

    # Setup logging
    logging.basicConfig(filename="skipped_faulty_rows.log", level=logging.INFO)
    reply_to_errors = []
    error_count = 0
    video_counter=0
    broken_comm_ids = ["M2G_v923_t270_rep_e1", "M2G_v606_t42_rep_e1", "M2G_v481_t310_rep_a4", "M2G_v455_t305_rep_f1"]

    print(f"Dataframe loaded. Start processing. Total documents: {tot_videos}")

    for video_title, group in grouped:
        reply_to_dict = {}
        proc_video = {}
        for _, row in group.iterrows():
            comment = row["tagged_body"]
            if row["id"] in broken_comm_ids:
                print(row)
                comment = "EMPTY_XX"
            if not isinstance(comment, str) or comment.strip() == "":
                comment = "EMPTY_XX"
            if comment == "EMPTY":
                comment = "EMPTY_XX"

            tokens = comment.split()
            tok_comment = []

            for i, token in enumerate(tokens):
                # Skip tokens shorter than 2 characters
                if len(token) < 2:
                    continue
                # Split on the last underscore (if any)
                if "_" in token:
                    word, pos = token.rsplit("_", 1)
                else:
                    word, pos = token, "XX"

                # cut words that are too long (LCP accepts max. 2000 bytes/word)
                # (no real word is that long, it basically just cuts a bunch of identical emojis or something similar)
                byte_len = len(word.encode("utf-8"))
                if byte_len > 800:
                    word = word[:400]

                pos = str(pos)
                if len(pos)<1:
                    pos = "XX"
                if pos[0] != "N":
                    word_x = word.lower()
                else:
                    word_x = word
                word_x = word_x.replace("@", "")
                lemma = word_x

                if pos == "ART":
                    if "ein" in word_x:
                        lemma = "ein"
                    elif word_x == "ne":
                        lemma = "ein"
                    elif word_x[0] == "d":
                        lemma = "d"
                    elif word_x == "'m":
                        lemma = "d"
                    elif word_x == "'s":
                        lemma = word_x

                elif pos == "PPER":
                    lemma = get_pper_lemmas(word_x)

                else:
                    try:
                        lemma = lemmatizer.find_lemma(word_x, pos)
                    except:
                        lemma = word_x

                tok_comment.append({"text": word, "pos": pos, "lemma": lemma})

            proc_comment = row.to_dict()
            proc_comment["tagged_body"] = tok_comment

            # # create id's
            proc_comment["thread_id"] = "_".join(proc_comment["id"].split("_")[:3])

            if proc_comment["type"]== "comment":
                reply_to_dict = {}
                proc_comment["reply_to"] = None
            else:
                if proc_comment["Antwort_auf"] == "deleted_reply":
                    proc_comment["reply_to"] = "deleted_reply"
                else:
                    try:
                        proc_comment["reply_to"] = reply_to_dict[proc_comment["Antwort_auf"]]
                    except:
                        reply_to_errors.append(row["row_id"])
                        error_count += 1

                        try:
                            proc_comment["reply_to"] = reply_to_dict["OC_0"]
                        except:
                            # print(reply_to_errors)
                            # print(f"Error count: {error_count}")
                            # print(reply_to_dict)
                            proc_comment["reply_to"] = "Error"

            reply_to_dict[proc_comment["Sprecher_ID"]]= proc_comment["id"]

            # convert pub_date to nice format
            old_pub = str(proc_comment["pub_date"]) # format "pub_date": "2019-12-03T17:17:22Z"
            new_pub = f"{old_pub[:10]} {old_pub[11:-1]}"
            proc_comment["pub_date"] = new_pub

            # rename some columns and delete not needed columns
            proc_comment["direct_address"] = proc_comment.pop("Adressierung")
            proc_comment["reply_time(s)"] = proc_comment.pop("reply_time_tot-in_s")
            for key in [ "reply_time-d", "reply_time-h", "reply_time-s", "error_code", "prob_spam", "updated", "body"]:
                del proc_comment[key]

            proc_video[row["row_id"]]= proc_comment

        video_title = re.sub(r'[<>,:"/\\|?*]', '_', video_title)
        output_file = f"{output_path}/{video_title}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(proc_video, f, ensure_ascii=False, indent=2)
        print(f"File '{video_title}.json' saved.\n{tot_videos - video_counter}/{tot_videos} documents left.")
        video_counter+=1
    print("Finished processing without apparent errors.")


###################################################################################################################
# main
###################################################################################################################
def main():
    # TODO: specify input and output paths
    input_file = "../1_data/demo_data_processed.csv"
    output_folder = "../1_data/prep_json_files"

    ######################################################################################
    output_path = os.path.join(os.path.dirname(__file__), output_folder)
    if os.path.exists(output_path):
        shutil.rmtree(output_path)
    os.makedirs(output_path)
    run_script(input_file, output_path)


if __name__ == "__main__":
    main()

