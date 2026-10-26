import scrapetube

"""
get_videoids() retrieves all video IDs from a specified YouTube channel 
using the 'scrapetube' library. It then saves the IDs to a text file named 
according to the channel ID, with one video ID per line.
"""

def get_videoids(channelid):
    CHANNELID = channelid
    videos = scrapetube.get_channel(CHANNELID)

    file = 'videolist_' + CHANNELID + '.txt'
    with open(file, 'a', encoding = 'utf8') as outfile:
        for video in videos:
            print(video['videoId']) 
            outfile.write(video['videoId'] + '\n')


def main():
    get_videoids('UCwRH985XgMYXQ6NxXDo8npw')


# channelid mailab: UCyHDQ5C6z1NDmJ4g6SerW8g
# channelid kurzgesagt: UCwRH985XgMYXQ6NxXDo8npw
# channelid mrwissen2go: UCZHpIFMfoJJ_1QxNGLJTzyA
    
    
if __name__ == "__main__":
    main()