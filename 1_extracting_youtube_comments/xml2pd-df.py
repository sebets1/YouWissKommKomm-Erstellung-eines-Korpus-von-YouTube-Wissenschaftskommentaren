import pandas as pd
import json
import os
from pathlib import Path


"""
This script converts the XML files containing YouTube 
comments into Pandas DataFrames and combines the data 
from all videos in a folder into one large DataFrame. 
It extracts the comment metadata and comment text 
separately before merging them into a single tabular 
dataset.
"""

# TODO please adjust folder name accordingly in line 10 and 12!
filelist = []
for filename in os.listdir('mailab_comments_xml'):
    if filename.endswith(".xml"):
        filelist.append(os.path.join('mailab_comments_xml', filename))



# initialize big dataframe
big_pd = pd.DataFrame()

for file in filelist: 
    file = str(file)
    print(file)
    try:
    # read xml file from one video, once only header items, once only body and merge into one dataframe
        df_meta = pd.read_xml(file, xpath='/corpus/text/header', elems_only=True, encoding = 'utf8')
        df_body = pd.read_xml(file, xpath='/corpus/text', encoding = 'utf8')
        df_body = df_body['body']
        df_whole = pd.merge(df_meta, df_body, left_index=True, right_index=True)
        # concatenate df's per video into one big dataframe - all videofiles from the folder will be in this dataframe 
        big_pd = pd.concat([big_pd, df_whole], ignore_index=True)
    except: 
        continue

big_pd.info()
print(big_pd.head(5))
 