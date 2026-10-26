#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: Seraina Betschart
# date: December 2025
# Project eee-ScienceDebates
# Universität Zürich

####################################################################################
# This script works with the lcpcli module to convert a series of JSON documents
# (created with 'prepare_for_lcp_corpus_builder.py') into the CSV files needed for
# the LCP upload.

# To use the script, specify input and output paths below.
####################################################################################

import json
import os
import shutil
from lcpcli.builder import *


# TODO specify path to input folder (created in 'prepare_for_lcp_corpus_builder.py') and output folder
INPUT_FOLDER = os.path.join(os.path.dirname(__file__), "../1_data/prep_json_files")
OUTPUT_FOLDER = os.path.join(os.path.dirname(__file__), "../1_data/lcp_data")


def fix_nones(value, default="UNKNOWN"):
    """
    LCP sometimes struggles with empty values.
    Thus, they are replaced by a default value (e.g. 'UNKNOWN') to ensure less processing problems later on.
    """
    return value if value not in (None, "", "None") else default


def fix_address(value, default="UNKNOWN"):
    if value == "leven":
        return True
    elif value == "new":
        return True
    else:
        return value if value not in (None, "", "None") else default


def process_document(file, corpus):
    """
    Main processing function.
    Process one JSON file containing all comments to one video (the individual document in LCP terms).
    """
    with open(file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    all_comments = []

    # extract video (document level) metadata from first entry
    first_entry = next(iter(data.values()))
    video_title = first_entry.get("video_title")
    channel_title = first_entry.get("channel_title")
    video_id = "_".join(first_entry.get("thread_id").split("_")[:2])

    thread_comments = []
    all_threads = []
    thread_test_counter = 0

    # iterate through all entries and process threads, comments and tokens
    for entry in data.values():
        tokens = []

        # process individual tokens and add token metadata
        for token in entry.get("tagged_body", []):
            if token["text"].strip():  # to check if token is not empty
                tokens.append(corpus.Word(token["text"], lemma=fix_nones(token["lemma"]), pos=fix_nones(token["pos"])))

        # process comments and add comment (segment level) metadata
        segment = corpus.Comment(*tokens,
                                 id=entry.get("id"),
                                 type=fix_nones(entry.get("type")),
                                 date=fix_nones(entry.get("pub_date")),
                                 likes=fix_nones(entry.get("like_count"), 0),
                                 num_replies=fix_nones(entry.get("num_replies"), 0),
                                 direct_address=str(fix_address(entry.get("direct_address"), default="-")),
                                 replyto=fix_nones(entry.get("reply_to")),
                                 reply_time_in_s=fix_nones(entry.get("reply_time(s)"), 0)
                                 )
        segment.author = fix_nones(entry.get("author"))
        segment.make()
        all_comments.append(segment)

        # if segment is a comment, not a reply, add currently stored comments as one thread to corpus and start new thread
        if entry.get("Sprecher_ID") == "OC_0":
            if len(thread_comments)>0:
                thread = corpus.Thread(*thread_comments,
                                       num=first_thread_comment.get("thread_id")
                                       ## add more thread metadata here if desired
                                       )
                thread.make()
                all_threads.append(thread)
                thread_test_counter += 1
            thread_comments = [segment]
            first_thread_comment = entry
        else:
            thread_comments.append(segment)

    # to not forget the last thread of a video
    if len(thread_comments) > 0:
        thread = corpus.Thread(*thread_comments,
                               num=first_thread_comment.get("thread_id")
                               ## add more thread metadata here if desired
                               )
        thread.make()
        all_threads.append(thread)

    doc = corpus.Video(*all_threads,
                       title=video_title,
                       channel=channel_title,
                       num=video_id
                       ## add more video metadata here if desired
                       )
    doc.make()
    print(f"Processed file: '{video_title}'")

    return corpus



#############################################################################################################
#############################################################################################################
def create_corpus():
    """
    Arguments for Corpus:
    name (str, mandatory) is the name of the corpus
    document (str, optional, default "Document") is the name of the document-level layer of the corpus
    segment (str, optional, default "Segment") is the name of the sentence-level layer of the corpus
    token (str, optional, default "Token") is the name of the word-level layer of the corpus
    authors (str, optional, default "placeholder") is the name(s) of the author(s) of the corpus
    institution (str, optional, default "") is the name of the institution associated with the corpus
    description (str, optional, default "") is a description of the corpus, as it will be presented to end users
    date (str, optional, default "placeholder") is the date when the corpus was curated
    revision (int | float, optional, default 1) is the revision number of the corpus
    url (str, optional, default "placeholder") is the source URL of the corpus
    license (str | None, optional, default None) is the code of the license of the corpus
    The values of authors, institution, description, date, revision, url and license can be modified in LCP after import.
    """
    shutil.rmtree(OUTPUT_FOLDER, ignore_errors=True)
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    input_folder_path = INPUT_FOLDER

    c = Corpus(
            name="Science Youtube Comments - complete",
            document="Video",
            segment="Comment",
            token="Word",
            description="Collection of comments in German Youtube Science Channels"
                )

    tot_files = len(os.listdir(input_folder_path))
    file_counter = 0
    print(f"Start processing. {tot_files} left to process.")

    # Loop through all files
    for filename in os.listdir(input_folder_path):
        file_path = os.path.join(input_folder_path, filename)
        c = process_document(file_path, c)
        file_counter += 1
        print(f"{tot_files - file_counter}/{tot_files} files left to process.")

    c.make(OUTPUT_FOLDER)
    print("Corpus created")


if __name__ == "__main__":
    create_corpus()



