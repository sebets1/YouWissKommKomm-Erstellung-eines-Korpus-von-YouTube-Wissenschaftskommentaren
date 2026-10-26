#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: Seraina Betschart
# date: October 2025
# Project eee-ScienceDebates
# Universität Zürich

#######################################################################################################################
# This script reads a CSV file containing youtube comments in the following format:
# - One row per comment or reply.
# - Required columns:
#     row_id, type, id, channel_title, video_title, author,
#     pub_date, updated, like_count, body, tagged_body
# - The rows must be ordered such that each top-level comment is followed by all of its replies.

# It puts them through a series of processing steps, including:
# - reconstructing conversation threads
# - assigning unique speaker IDs within each thread
# - identifying which comment each reply addresses
# - calculating reply times
# - classifying participant engagement (reply types)
# - detecting potential inconsistencies (deleted replies, timestamp issues, etc.)
# - flagging probable spam comments
# - generating new standardized comment IDs

# To use the script, specify input and output paths in the main() function at the bottom.
#######################################################################################################################


import pandas as pd
from collections import Counter
from datetime import datetime
from string import ascii_lowercase
import Levenshtein
import re


def create_reply_id(author_ind, author_id):
    """
    Called from 'add_reply_info'.
    Change the reply numbers to letters for easier read. Additional solution for conversations where more than
    26 different authors are involved.
    """
    first_letter = 0
    extra_letter = False
    while author_ind >25:
        author_ind = author_ind-26
        first_letter += 1
    if first_letter != 0:
        first_letter -= 1
        extra_letter = ascii_lowercase[first_letter]

    main_letter = ascii_lowercase[author_ind]

    if extra_letter:
        reply_id = f"{extra_letter}{main_letter}_{author_id}"
    else:
        reply_id = f"{main_letter}_{author_id}"
    return reply_id


def add_reply_info(conv_list, indices):
    """
    Assign an id to every author in a conversation and count their number of replies (e.g. first author is assigned the
    letter "a" and every subsequent reply of his will be assign "a" and an increasing number, so: "a_1", "a_2" and so
    on.
    """

    i_author = indices["author"]

    author_list = []
    id_list = []
    original_comment = conv_list[0][i_author]
    oc_counter = 0
    for row in conv_list:
        if row[i_author]==original_comment:
            row.append(f"OC_{oc_counter}")
            oc_counter+=1
        elif row[i_author] in author_list:
            author_ind = author_list.index(row[i_author])
            author_id = id_list[author_ind]
            row.append(create_reply_id(author_ind, author_id))
            id_list[author_ind] += 1

        else:
            author_list.append(row[i_author])
            id_list.append(2)
            row.append(create_reply_id(author_list.index(row[i_author]), 1))
    return conv_list


def find_author_last_resort(comment_tokens, author_list_b):
    """
    Called from 'add_reply_to'.
    If author addressed to wasn't found, try with Levenshtein ratio to check if very similar spelled author exists in
    reply body.
    """

    author_list = []
    for ele in author_list_b:
        author_list.append(ele[0])

    def apply_levenshtein(target):
        for author in author_list:
            author_new = re.sub(r'\d+$', '', author)
            target_new = re.sub(r'\d+$', '', target)
            target_new = target_new.replace(" ", "")
            ratio = Levenshtein.ratio(author_new, target_new)
            if ratio >= 0.7: # experimented with different ratios, 0.7 seemed like a good recall without too many false positives
                return author
        return False

    target = comment_tokens[0]
    target_searched = apply_levenshtein(target)
    if target_searched:
        return target_searched

    # Sometimes the user name is split into several tokens. Try two and three tokens with Levenshtein.
    target = " ".join(comment_tokens[0:2])
    target_searched = apply_levenshtein(target)
    if target_searched:
        return target_searched

    target = " ".join(comment_tokens[0:3])
    target_searched = apply_levenshtein(target)
    if target_searched:
        return target_searched

    return "no_author_XXX"


def add_reply_to(conv_list, indices):
    """
    Determine to whom a reply is addressed. If other author is tagged in response, his newest reply id is added,
    otherwise it is assumed that the reply is addressed to original comment.
    """

    i_author = indices["author"]
    i_body = indices["body"]

    author_list = []
    conv_list[0]+=["-", 0, None]  # 1st value: reply_to, 2nd value: how many replies to this comment (will be added subsequently)
    oc_author = conv_list[0][i_author]
    for row in conv_list[1:]:
        if not isinstance(row[i_author], str):
            row[i_author] = "@XXX_NO_AUTHOR_FOUND_XXX"
        author_list.append([row[i_author], row[-1]])
        if not isinstance(row[i_body], str):
            row[i_body] = "XXX NO TEXT FOUND XXX"
        body_list = row[i_body].split(" ")
        author_found = False
        for token in body_list:
            if not author_found:
                if token[:2] == "@@":
                    target_author = token[1:]
                    for author in reversed(author_list):
                        if author[0] in target_author:
                            row+=[author[1], 0, True]
                            for r in conv_list:
                                if r[-3]==author[1]:
                                    r[-2]+=1
                            author_found = True
                            break
                    if not author_found:
                        if target_author == oc_author:
                            row+=["OC_0", 0, True]
                            conv_list[0][-2]+=1
                        else:
                            row+=["deleted_reply", 0, False]
                        author_found = True
        if not author_found:
            target_author = "not-found"
            if body_list[0].startswith("@"):
                target_author = body_list[0]
            elif len(body_list)>=2:
                    if body_list[1].startswith("@"):
                        target_author = body_list[1]
            elif body_list[0].startswith("+"):
                target_author = f"@{body_list[0]}"
            if target_author != "not-found":
                for author in reversed(author_list):
                    if author[0] in target_author:
                        row += [author[1], 0, True]
                        for r in conv_list:
                            if r[-3] == author[1]:
                                r[-2] += 1
                        author_found = True
                        break

            if not author_found:
                target_author = find_author_last_resort(body_list, author_list)
                if target_author != "no_author_XXX":
                    for author in reversed(author_list):
                        if author[0] in target_author:
                            row += [author[1], 0, "leven"]
                            for r in conv_list:
                                if r[-3] == author[1]:
                                    r[-2] += 1
                            author_found = True
                            break
            if not author_found:
                row+=["OC_0", 0, False]
                conv_list[0][-2] += 1

    return conv_list


def add_reply_speed(conv_list, indices):
    """
    Calculates speed of reply to comment tagged as "Antwort_auf" in a list of conversations.
    """

    i_date = indices["pub_date"]
    i_sprecher_id = indices["Sprecher_ID"]
    i_antwort_auf = indices["Antwort_auf"]

    reply_ids = {}

    for row in conv_list:
        current_date = f'{row[i_date][:10]} {row[i_date][11:-1]}'
        current_date_object = datetime.strptime(current_date, '%Y-%m-%d %H:%M:%S')
        reply_ids[row[i_sprecher_id]] = current_date_object

    conv_list[0] += [0, 0, 0, 0]

    for row in conv_list[1:]:
        if row[i_antwort_auf] == "deleted_reply":
            row += [0, 0, 0, 0]
        else:
            if row[i_antwort_auf] not in reply_ids:
                row += [0, 0, 0, 0]
            else:
                last_date_object = reply_ids[row[i_antwort_auf]]
                current_date = f'{row[i_date][:10]} {row[i_date][11:-1]}'
                current_date_object = datetime.strptime(current_date, '%Y-%m-%d %H:%M:%S')
                dif = current_date_object - last_date_object
                days = dif.days
                hours = dif.seconds // 3600  # extract full hours from seconds
                seconds = dif.seconds % 3600  # remaining seconds after extracting hours
                tot_in_sec = days * 24 * 3600 + hours * 3600 + seconds
                row += [days, hours, seconds, tot_in_sec]

    return conv_list


def add_reply_type(conv_list, indices):
    """
    Distributing labels depending on the engagement of the user.

    Categories:
    * For the original commenter:
        -beteiligter_OC: The original commenter engages further in the conversation
        -unbeteiligter_OC: The user writing the comment is not part of the replies.

    * For reacting users (replies):
        -single_reply: The user only writes this one reply in the conversation.
        -ongoing_first: The user writes several replies in the conversation. This is his/her first.
        -ongoing: The user writes several replies in the conversation. This one is neither his/her first nor last.
        -ongoing_last: The user writes several replies in the conversation. This is his/her last.
    """

    i_author = indices["author"]

    author_list = []
    OC = conv_list[0][i_author]
    OC_label = "unbeteiligter_OC"
    for row in conv_list[1:]:
        if row[i_author] == OC:
            OC_label = "beteiligter_OC"
        else:
            author_list.append(row[i_author])

    author_counts = Counter(author_list)

    seen = {}
    for row in conv_list:
        author = row[i_author]
        if author == OC:
            row.append(OC_label)
        elif author_counts[author] == 1:
            row.append("single_reply")
        elif author not in seen:
            row.append("ongoing_first")
            seen[author] = 1
        elif seen[author] == author_counts[author] - 1:
            row.append("ongoing_last")
            seen[author] += 1
        else:
            row.append("ongoing")
            seen[author] += 1

    return conv_list


def add_error_messages(conv_list, indices):
    """
    Add error messages to excel.
    ERR_DEL_REPLY: User answered to a reply that could not be found. (Different reasons, most often the original reply was
        deleted because the account was deleted. Youtube & channels sometimes delete comments. Users sometimes delete
        their own comments. It's probable that the rows were mixed up sometimes, thus somebody would answer to a reply
        in a different conversation.)
    ERR_NEG_REPLY_SPEED: The reply speed calculation resulted in a negative value. (Again different possible explanations)
    ERR_NEG_SPEED_X: This is the comment, the error comment ERR_NEG_REPLY_SPEED replied to. So oftentimes this comment caused the minusvalue.
    ERR_CHANGED_USER: Comments address other user which has supposedly changed username, so there is only one tag @. For some
        reason, this leads to many problems with recorded published date

    An added "_b" always indicates that the row itself doesn't contain a visible error but a previous row in the same
    conversation did and thus the current row might be affected too.

    Additionally, if any error was found in a conversation, 'True' is added to the row of the original commenter, if no error
    at all was found, 'True' is added to simplify filtering conversations without apparent errors.

    """

    i_sprecher_id = indices["Sprecher_ID"]
    i_antwort_auf = indices["Antwort_auf"]
    i_reply_time = indices["reply_time_tot-in_s"]
    i_body = indices["body"]

    error1 = False # deleted reply
    error2 = False # minus values
    error3 = False # username not found, often incorrect date
    flag_error2 = []
    conv_error_collection = set()
    for row in conv_list:  # row[18] contains reply speed in seconds, row[12] contains reply_to
        row_errors = []
        if error1:
            row_errors.append("ERR_DEL_REPLY_b")
            conv_error_collection.add("ERR_DEL_REPLY_b")
        if error2:
            row_errors.append("ERR_NEG_REPLY_SPEED_b")
            conv_error_collection.add("ERR_NEG_REPLY_SPEED_b")
        if error3:
            row_errors.append("ERR_CHANGED_USER_b")
            conv_error_collection.add("ERR_CHANGED_USER_b")
        if row[i_antwort_auf] == "deleted_reply":
            error1 = True
            row_errors.append("ERR_DEL_REPLY")
            conv_error_collection.add("ERR_DEL_REPLY")
        if row[i_reply_time] < 0:
            error2 = True
            row_errors.append("ERR_NEG_REPLY_SPEED")
            conv_error_collection.add("ERR_NEG_REPLY_SPEED")
            flag_error2.append(row[i_antwort_auf])
        if row[i_body].startswith("@"):
            if not row[i_body].startswith("@@"):
                if row[i_antwort_auf]== "OC_0":
                    row_errors.append("ERR_CHANGED_USER")
                    conv_error_collection.add("ERR_CHANGED_USER")
                    error3 = True
        row.append(row_errors)

    for x in conv_list:
        if x[i_sprecher_id] in flag_error2:
            x[-1].append("ERR_NEG_SPEED_X")

    if len(conv_error_collection) == 0:
        conv_list[0][-1] = False
    else:
        conv_list[0][-1] = True

    return conv_list


def spam_filter(df_list, indices):
    """
    A few patterns to try filtering out spam messages. The supposed spam rows get stored in a set to be taken out later
    if they turn out not to be anything of importance (e.g. no other commenters reacted to these).
    """

    i_sprecher_id = indices["Sprecher_ID"]
    i_antwort_auf = indices["Antwort_auf"]
    i_reply_time = indices["reply_time_tot-in_s"]
    i_body = indices["body"]
    i_author = indices["author"]
    i_row_id = indices["row_id"]

    assumed_spam = {}
    doubles = {}
    spam_rows = []
    double_rows = []
    for row in df_list:
        if isinstance(row[i_body], str):
            if row[i_body] in doubles:
                if doubles[row[i_body]][i_row_id][i_author] == row[i_author]: # check if the same person wrote the same comment multiple times
                    doubles[row[i_body]] += [row]

            else:
                doubles[row[i_body]] = [row]
            if "https:/" in row[i_body]:
                if row[i_body] in assumed_spam:
                    assumed_spam[row[i_body]] += [row]
                else:
                    assumed_spam[row[i_body]]=[row]

    for key, value in assumed_spam.items():
        if len(value) > 1:
            for row in value:
                spam_rows.append(row[i_row_id])
    for key, value in doubles.items():
        if len(value) > 2:
            for row in value:
                double_rows.append(row[i_row_id])
    spam_set = spam_rows+double_rows

    return set(spam_set)


def add_spam_message(df_list, spams, indices):
    """
    Add a column 'prob_spam' to dataframe with values True (probable spam) and False.
    """
    i_row_id = indices["row_id"]
    i_replies = indices["num_replies"]
    for ele in df_list:
        ele.append(False)
        if ele[i_replies]==0:
            if ele[i_row_id] in spams:
                ele[-1]=True
    return df_list



def create_new_ids(conv_list, indices, thread_nr, video_names, channel_names):
    """
    Create new id for every comment based on pattern: [Mai|M2G|Kurz]_v19_t303_[rep|com]_OC1
    """
    i_vid = indices["video_title"]
    i_sprecher_id = indices["Sprecher_ID"]
    i_channel = indices["channel_title"]
    i_type = indices["type"]

    first_com = conv_list[0]
    vid_nr = video_names[first_com[i_vid]]

    channel_name = channel_names[first_com[i_channel]]
    thread_id = f"{channel_name}_v{vid_nr}_t{thread_nr}"

    new_conv_list = []

    for com in conv_list:
        if com[i_type] == "comment":
            new_id = f"{thread_id}_com_{''.join(com[i_sprecher_id].split('_'))}"
            com.append(new_id)
            new_conv_list.append(com)
        else:
            new_id = f"{thread_id}_rep_{''.join(com[i_sprecher_id].split('_'))}"
            com.append(new_id)
            new_conv_list.append(com)

    return conv_list


####################################################################################################################
def get_reply_information(df_list, indices):
    """
    Separate the conversations (comment and all corresponding replies) and add information to them (who answered whom,
    reply speed etc). This function does some repairing and separates the conversations/threads. Then calls other
    functions which extract information of the individual threads.

    look-up list:
    - row_id = row[0]
    - type = row[1]
    - id = row[2]
    - channel_title = row[3]
    - video_title = row[4]
    - author = row[5]
    - pub_date = row[6]
    - updated = row[7]
    - like_count = row[8]
    - body = row[9]
    - tagged_body = row[10]

    added information in this function:
    *add_reply_info()
    - Sprecher_ID = row[11]
    *add_reply_to()
    - Antwort_auf = row[12]
    - num_replies = row[13]
    - Addressierung_found = row[14]
    *add_reply_speed()
    - reply_time-d = row[15]
    - reply_time-h = row[16]
    - reply_time-s = row[17]
    - reply_time_tot-in_s = row[18]
    *add_reply_type()
    - reply_type = row[19]
    *add_error_messages()
    - error_code = row[20]
    *add_spam_message()
    - prob_spam = row[21]

    """
    current_conversation = []
    updated_df_list = []
    comment_id = "not_started"

    num_columns = len(indices) #11
    indices.update({"Sprecher_ID": num_columns, "Antwort_auf":(num_columns+1), "num_replies": (num_columns+2),
                    "Addressierung_found": (num_columns+3),"reply_time-d": (num_columns+4),
                    "reply_time-h": (num_columns+5), "reply_time-s": (num_columns+6),
                    "reply_time_tot-in_s": (num_columns+7),"reply_time": (num_columns+8),
                    "error_code": (num_columns+9),"prob_spam": (num_columns+10)})

    spam_set = spam_filter(df_list, indices)
    counter = 0
    tot_rows = len(df_list)

    # counters for new id creation, pattern: [Mai|M2G|Kurz]_v19_t303_[rep|com]_OC1
    video_counter = 1
    video_dict = {}
    conv_counter = 1
    channel_shortnames = {"Dinge Erklärt – Kurzgesagt": "Kurz", "MAITHINK X": "Mai", "MrWissen2go": "M2G"}
    repaired=[]
    current_video = ""

    # -------------- repair the ca 600 rows, where tagged_body got lost ------
    for i, row in enumerate(df_list):
        if type(row[10]) == float:

            if type(df_list[i-1][10])!=float:
                try_1 = df_list[i-1][10].split("\n")
                first = True
                for ele in try_1:
                    sent = ele.split("\t")[-1]
                    clean_text = re.sub(r'_[A-Z0-9$]+', '', sent)
                    repaired.append([clean_text, sent])
                    if first:
                        df_list[i - 1][10] = sent
                        first = False

    for row in df_list:
        if type(row[10]) == float:
            found = False
            for sent in repaired:
                ratio = Levenshtein.ratio(sent[0], row[9])
                if ratio > 0.8:
                    found = True
                    row[10]=sent[1]

            if found == False:
                row[10]= "EMPTY"
        # ------------- repairing finished. Move on with actual processing -----------------


        counter += 1
        if counter % 100000 == 0: # just to show work in progress and get an idea of speed of program
            print(f"Finished processing row {counter} of {tot_rows}")


        if row[2] == comment_id:
            current_conversation.append(row)

        else:
            current_conv_counter = conv_counter

            if len(current_conversation)>0:

                # insert here all the functions which involve the individual conversations:
                updated_conv = add_reply_info(current_conversation, indices)
                updated_conv = add_reply_to(updated_conv, indices)
                updated_conv = add_reply_speed(updated_conv, indices)
                updated_conv = add_reply_type(updated_conv, indices)
                updated_conv = add_error_messages(updated_conv, indices)
                updated_conv = add_spam_message(updated_conv, spam_set, indices)
                updated_conv = create_new_ids(updated_conv, indices, current_conv_counter, video_dict, channel_shortnames)

                updated_df_list += updated_conv

            current_conversation=[row]

            if row[4] not in video_dict:
                video_dict[row[4]] = video_counter
                video_counter += 1
                conv_counter = 0
            comment_id = row[2]
            conv_counter += 1


    if len(current_conversation) > 0:
        current_conv_counter = conv_counter
        # insert here all the functions which involve the individual conversations:
        updated_conv = add_reply_info(current_conversation, indices)
        updated_conv = add_reply_to(updated_conv, indices)
        updated_conv = add_reply_speed(updated_conv, indices)
        updated_conv = add_reply_type(updated_conv, indices)
        updated_conv = add_error_messages(updated_conv, indices)
        updated_conv = add_spam_message(updated_conv, spam_set, indices)
        updated_conv = create_new_ids(updated_conv, indices, current_conv_counter, video_dict, channel_shortnames)

        updated_df_list += updated_conv
    return updated_df_list

####################################################################################################################
def double_ids_problem(df):
    """
    We realized late that 11 IDs were assigned to two comments because of some inconsistencies in the corpus.
    To not confuse the other IDs, this is a fix that identifies the double IDs and gives a maximum thread number to
    the second comment (which is an individual top-level comment without replies, which is dropped from the analysis).
    """
    counter = 1970
    for idx in df.index[df["id"].duplicated()]:
        df.loc[idx, "id"] = re.sub(
            r"_t\d+",
            f"_t{counter}",
            df.loc[idx, "id"],
            count=1
        )
        counter += 1

    return df


def create_new_df(df, conversation_list):
    """
    Convert the updated and processed list back to a dataframe.
    """

    columns = list(df.columns.values)
    columns += ["Sprecher_ID", "Antwort_auf", "num_replies", "Adressierung", "reply_time-d", "reply_time-h",
                "reply_time-s", "reply_time_tot-in_s", "reply_type", "error_code", "prob_spam", "id"]
    df_new = pd.DataFrame(conversation_list, columns=columns)

    ##############################
    ## for general use, get rid of this part (no reordering)---------

    df_reordered = df_new.loc[:, ['row_id', 'id', 'type', 'old_id', 'channel_title', 'video_title', 'author', 'Sprecher_ID',
                                  'num_replies', "Adressierung",
                                  'Antwort_auf', 'reply_type', 'reply_time-d', 'reply_time-h', 'reply_time-s',
                                  'reply_time_tot-in_s', 'error_code', 'prob_spam', 'pub_date', 'updated', 'like_count',
                                  'body', 'tagged_body']]

    print("\n", df_reordered.head(10))
    return df_reordered
    ## for general use, get rid of this part (no reordering)---------

####################################################################################################################


def save_df(df, filename):
    df.to_csv(filename, index=False, encoding="utf-8")
    print(f"\nDataframe saved to {filename}\n")

####################################################################################################################


def check_input_data(df):
    """
    Check if the columns necessary to run the script exist and if they have the expected values.
    Rename and drop some columns.
    """

    ####################################################################
    # Deal with weirdly formatted columns from youtube corpus
    ####################################################################
    # Rename columns if they exist
    rename_map = {}
    if 'Unnamed: 0.1' in df.columns:
        rename_map['Unnamed: 0.1'] = 'row_id'
    if 'comments' in df.columns:
        rename_map['comments'] = 'tagged_body'
    if 'id' in df.columns:
        rename_map['id'] = 'old_id'

    if rename_map:
        df.rename(columns=rename_map, inplace=True)

    # Drop column if it exists
    columns_to_drop = ['Unnamed: 0']
    existing_columns_to_drop = [col for col in columns_to_drop if col in df.columns]

    if existing_columns_to_drop:
        df.drop(columns=existing_columns_to_drop, inplace=True)

    #########################################################################
    # Some checks to make sure the provided input data is in the right format
    #########################################################################
    # REQUIRED COLUMNS
    required_columns = [
        'row_id', 'type', 'old_id', 'channel_title', 'video_title',
        'author', 'pub_date', 'updated', 'like_count', 'body', 'tagged_body'
    ]

    # 1. Check all required columns exist
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    # Sample first 10 rows
    sample = df.head(10)

    # 2. Check 'type' values
    valid_types = {'comment', 'reply'}
    invalid_types = set(sample['type'].dropna()) - valid_types
    if invalid_types:
        raise ValueError(f"Invalid 'type' values found: {invalid_types}")

    # 3. Check 'pub_date' format
    def is_valid_date(date_str):
        try:
            date_str = f'{date_str[:10]} {date_str[11:-1]}'
            datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
            return True
        except Exception:
            return False

    invalid_dates = sample['pub_date'].dropna().apply(lambda x: not is_valid_date(str(x)))
    if invalid_dates.any():
        raise ValueError(f"Invalid 'pub_date' format in rows: {sample[invalid_dates].index.tolist()}")

    # 4. Check 'author' starts with '@'
    invalid_authors = sample['author'].dropna().apply(lambda x: not str(x).startswith('@'))
    if invalid_authors.any():
        raise ValueError(f"'author' values not starting with @ in rows: {sample[invalid_authors].index.tolist()}")

    # 5. Check 'row_id' contains integers
    invalid_row_ids = sample['row_id'].dropna().apply(lambda x: not isinstance(x, int))
    if invalid_row_ids.any():
        raise ValueError(f"'row_id' contains non-integer values in rows: {sample[invalid_row_ids].index.tolist()}")
    return df


def process_comments(input_file):
    print("Reading csv file into dataframe.")
    df = pd.read_csv(input_file)

    df = check_input_data(df)
    print(f"Finished reading {input_file}.\nStart preprocessing...")

    data_list = df.values.tolist()  # convert dataframe to list for processing

    indices = {col: i for i, col in enumerate(df.columns)} # automatically generate column indices from the dataframe
    updated_df_list = get_reply_information(data_list, indices)
    updated_df = create_new_df(df, updated_df_list)
    updated_df = double_ids_problem(updated_df)
    return updated_df


###################################################################################################################
# main
###################################################################################################################
def main():
    save_output = True  # save final output to csv file

    # TODO specify path to input folder (containing the CSV file with the comments) and output folder
    input_file = "../1_data/example_data.csv"
    output_file = "../1_data/example_data_out.csv"

    input_file = "../../yt_data/yt_comms_all.csv"
    output_file = "../../yt_data/260823_all_comms_processed.csv"

    #####################################################################

    df_out = process_comments(input_file)

    if save_output:
        save_df(df_out, output_file)

    # save subset for experiments
    # subset = df_out.iloc[500000:700000]
    # subset.to_csv("yt_data/DELETE_subset.csv", index=False)


if __name__ == "__main__":
    main()

