import json 
from lxml import etree
import xml.etree.ElementTree as ET
import os

"""
This script converts scraped YouTube comment JSON files into XML, 
creating separate XML text blocks for top-level comments and their 
replies. It enriches each comment with video and channel titles 
from all_titles.txt and includes metadata such as author, publication 
date, update date, and like count.
"""

# Achtung! Vor diesem Skript muss das Skript crawl_youtube_video_details laufen! Ansonsten funktionieren channel_title und video_title nicht!


def get_comment(filename):
    filename = filename
    with open(filename, 'r', encoding = 'utf8') as infile: 
        jsonfile = json.load(infile)

        # yields one dictionary
        for comment in jsonfile: 
            # print(comment)
            yield comment


def make_xml(infile):
        
        root = ET.Element('corpus')
        
        print('iterating through comments ...')
    
        for elem in get_comment(infile):    
            text = ET.SubElement(root, 'text')

            titlefile = open('all_titles.txt', 'r', encoding= 'utf8')
            for line in titlefile:
                line_list = line.split('\t')
                if elem['videoId'] == line_list[0]:
                    channel_name = line_list[1].strip()
                    video_name = line_list[2].strip()

        # fill header 
            header = ET.SubElement(text, 'header')
            type = ET.SubElement(header, 'type')
            type.text = elem['type']
            id = ET.SubElement(header, 'id')
            id.text = elem['id']
            channel_title = ET.SubElement(header, 'channel_title')
            try:
                channel_title.text = channel_name
            except: 
                channel_title.text = 'Dinge Erkl&#228;rt &#8211; Kurzgesagt'
            video_title = ET.SubElement(header, 'video_title')
            video_title.text = video_name
            author = ET.SubElement(header, 'author')
            author.text = elem['authorDisplayName']
            pub_date = ET.SubElement(header, 'pub_date')
            pub_date.text = elem['publishedAt']
            updated = ET.SubElement(header, 'updated')
            updated.text = elem['updatedAt']
            like_count = ET.SubElement(header, 'like_count')
            like_count.text = str(elem['likeCount'])

            


        # fill body 
            body = ET.SubElement(text, 'body')
            body.text = elem['textOriginal']
            
            
            """
        # fill reply into body (can also be moved outside as below)    
            for reply_elem in elem['replies']: 
                reply = ET.SubElement(body, 'reply')
                type = ET.SubElement(reply, 'type')
                type.text = 'reply'
                id = ET.SubElement(reply, 'id')
                id.text = reply_elem['parentId']
                author = ET.SubElement(reply, 'author')
                author.text = reply_elem['authorDisplayName']
                pub_date = ET.SubElement(reply, 'pub_date')
                pub_date.text = reply_elem['publishedAt']
                reply_text = ET.SubElement(reply, 'reply_text')
                reply_text.text = reply_elem['textDisplay']
            """ 

            # fill replies either like this or as above (here as their own texblock with header and body)
            
            for reply_elem in elem['replies']:
                text = ET.SubElement(root, 'text')
                header = ET.SubElement(text, 'header') 
                body = ET.SubElement(text, 'body')
                type = ET.SubElement(header, 'type')
                type.text = 'reply'
                id = ET.SubElement(header, 'id')
                id.text = reply_elem['snippet']['parentId']
                channel_title = ET.SubElement(header, 'channel_title')
                try:
                    channel_title.text = channel_name
                except:
                    channel_title.text = 'Dinge Erkl&#228;rt &#8211; Kurzgesagt'
                video_title = ET.SubElement(header, 'video_title')
                video_title.text = video_name
                author = ET.SubElement(header, 'author')
                author.text = reply_elem['snippet']['authorDisplayName']
                like_count = ET.SubElement(header, 'like_count')
                like_count.text = str(reply_elem['snippet']['likeCount'])
                pub_date = ET.SubElement(header, 'pub_date')
                pub_date.text = reply_elem['snippet']['publishedAt']
                updated = ET.SubElement(header, 'updated')
                updated.text = pub_date.text = reply_elem['snippet']['updatedAt']
                body.text = reply_elem['snippet']['textOriginal']
                 
                 
        print('writing to xml ...')
        tree = ET.ElementTree(root)
        tree.write(infile[:-5] + '.xml')

# TODO disable this and enable main when done testing
#make_xml('crawl_kurzgesagt/Z08nN20KZ4o.json')


def main():
    json_filelist = os.listdir('crawl_neue_vids_alle')
    for file in json_filelist:
        print(file)
        try:
            make_xml('crawl_neue_vids_alle/' + file) 
        except: 
            continue


if __name__ == '__main__':
    main()



