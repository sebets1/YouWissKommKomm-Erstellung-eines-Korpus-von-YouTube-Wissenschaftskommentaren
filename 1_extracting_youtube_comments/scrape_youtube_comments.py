from googleapiclient.discovery import build
import os
import pandas as pd
import json
from tqdm import tqdm



"""
Script scrapes YT Comments with more than 5 replies. 

It is based on this tutorial: https://www.geeksforgeeks.org/python/how-to-extract-youtube-comments-using-youtube-api-python/

helper website: https://developers.google.com/youtube/v3/docs/commentThreads?hl=de
"""

api_key = 'INSERT API KEY'
VIDEO_LIST = 'videolist_mrwissen.txt'
OUTPUT_FOLDER = 'scrape_mrwissen/'

def video_comments(video_id):
	print(video_id)

	# empty list for storing reply
	replies = []

	# creating youtube resource object
	youtube = build('youtube', 'v3',
					developerKey=api_key)

	# retrieve youtube video results
	video_response=youtube.commentThreads().list(
	part='snippet,replies',
	videoId=video_id
	).execute()


	# iterate video response
	master_list = []
	while video_response:
	
		for item in tqdm(video_response['items']):
			

			comment = item['snippet']['topLevelComment']['snippet']
			# adding id here to make them matchable later
			comment_id = item['id']
			full_comment = {'id': comment_id}
			full_comment.update(comment)
			
			# counting number of reply of comment
			replycount = item['snippet']['totalReplyCount']

			# if reply is there and there are 5 or more 
			if replycount>=5:
			
				print('extracting replies for valid comments ...')
				request = youtube.comments().list(part = 'snippet', parentId = comment_id, maxResults = 100)
				reply_response = request.execute()
				replies = reply_response['items']

			# adding type here, can also be disabled and added when filling into xml if wanted (reply type is filled in when doing xml, see script json2xml.py)
			updict_comment = {'type': 'comment'}
			updict_comment.update(full_comment)
			if len(replies) < 5:
				continue
			else:
				updict_comment['replies'] = replies
				master_list.append(updict_comment)

			# empty reply list
			replies = []

		# Again repeat
		if 'nextPageToken' in video_response:
			# print('yes')
			video_response = youtube.commentThreads().list(
					part = 'snippet,replies',
					videoId = video_id,
					pageToken = video_response['nextPageToken']
				).execute()
		else:
			break 

	json_name = video_id + '.json'
	print('writing to file ...')
	with open(OUTPUT_FOLDER + json_name, "w", encoding = 'utf8') as outfile:
		json_object = json.dumps(master_list, indent = 2)
		outfile.write(json_object + '\n') # TODO hier noch den Ordner für die Videos spezifizieren! Ansonsten schreibt es einfach alle ins working dir!


	
def main():
	with open(VIDEO_LIST, 'r', encoding= 'utf8') as videolistfile:
		for line in videolistfile:
			videoid = str(line.strip())
			video_comments(videoid) 

		
if __name__ == "__main__":
    main()


