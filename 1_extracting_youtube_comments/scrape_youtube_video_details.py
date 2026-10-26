import json
import os
import xml.etree.ElementTree as ET

from googleapiclient.discovery import build

"""
This script retrieves metadata for YouTube videos via the YouTube Data API, 
including titles, publication dates, channel information, tags, language, 
statistics, duration, and descriptions. It temporarily stores the API responses 
as JSON files and converts them into XML files containing structured video 
metadata and the video description.
"""



API_KEY = "INSERT API KEY"
INPUT_FILE = "videolist_mailab.txt"
JSON_OUTPUT_DIR = "details_mailab"
XML_OUTPUT_DIR = "details_mailab_xml"
TITLES_OUTPUT_FILE = "all_titles.txt"

# -----------------------------------------------
# Retrieve video metadata from YouTube API
# -----------------------------------------------
def video_metadata(video_id):
    print(f"Retrieving metadata for {video_id}...")

    youtube = build(
        "youtube", "v3", developerKey=API_KEY
    )

    request = youtube.videos().list(
        part="snippet,contentDetails,statistics",
        id=video_id
    )
    response = request.execute()

    # Skip videos that are no longer available
    if not response.get("items"):
        print(f"No metadata found for {video_id}")
        return None

    os.makedirs(JSON_OUTPUT_DIR, exist_ok=True)

    json_name = video_id + "_details.json"
    json_path = os.path.join(JSON_OUTPUT_DIR, json_name)

    print(f"Writing JSON to {json_path}...")

    with open(json_path, "w", encoding="utf8") as outfile:
        json.dump(
            response,
            outfile,
            indent=2,
            ensure_ascii=False
        )
    return response

# -----------------------------------------------
# Extract basic video information
# -----------------------------------------------
def get_video_title(response):
    item = response["items"][0]

    with open(TITLES_OUTPUT_FILE, "a", encoding="utf8") as titlefile:
        titlefile.write(
            item["id"]
            + "\t"
            + item["snippet"]["channelTitle"]
            + "\t"
            + item["snippet"]["title"]
            + "\n"
        )


# -----------------------------------------------
# Convert JSON metadata to XML
# -----------------------------------------------
def desc2xml(filename):

    filename = filename
    with open(filename, 'r', encoding = 'utf8') as infile: 
        response = json.load(infile)

    #print(type(response))
    root = ET.Element('corpus')
    text = ET.SubElement(root, 'text')
    header = ET.SubElement(text, 'header')
    id = ET.SubElement(header, 'id')
    id.text = response['items'][0]['id']
    pub_date = ET.SubElement(header, 'pub_date')
    pub_date.text = response['items'][0]['snippet']['publishedAt']
    title = ET.SubElement(header, 'video_title')
    title.text = response['items'][0]['snippet']['title']
    channel_title = ET.SubElement(header, 'channel_title')
    channel_title.text = response['items'][0]['snippet']['channelTitle']
    tags = ET.SubElement(header, 'tags')
    try:
        tags.text = ','.join(response['items'][0]['snippet']['tags'])
    except: 
         tags.text = '-'
    lang = ET.SubElement(header, 'lang')
    try:
        lang.text = response['items'][0]['snippet']['defaultAudioLanguage']
    except: 
         lang.text = '-'
    view_count = ET.SubElement(header, 'view_count')
    view_count.text = response['items'][0]['statistics']['viewCount']
    like_count = ET.SubElement(header, 'like_count')
    like_count.text = response['items'][0]['statistics']['likeCount']
    comment_count = ET.SubElement(header, 'comment_count')
    comment_count.text = response['items'][0]['statistics']['commentCount']
    duration = ET.SubElement(header, 'duration')
    duration.text = response['items'][0]['contentDetails']['duration']

    

    body = ET.SubElement(text, 'body')
    body.text = response['items'][0]['snippet']['description']

    tree = ET.ElementTree(root)
    id_name = response['items'][0]['id'] + '_details.xml'

    tree.write(XML_OUTPUT_DIR + id_name)


##################################################################################

def main():
    with open(INPUT_FILE, 'r', encoding= 'utf8') as videolistfile:
        for line in videolistfile:
            video_id = line.strip()
            if not video_id:
                continue
            try:
                # Retrieve metadata from YouTube API
                response = video_metadata(video_id)
                if response is None:
                    continue

                # Extract video title and channel information
                get_video_title(response)

                # Convert JSON file to XML
                json_file = os.path.join(JSON_OUTPUT_DIR, video_id + "_details.json")
                desc2xml(json_file)

            except Exception as error:
                print(f"Could not process video {video_id}: {error}")


if __name__ == '__main__':
     main()



