#!/usr/bin/python

import requests
import sys, getopt
import json, ast
import os
import wget 


def main(audio_id):
	getAudioInfo_query = """	
	query($id:ID!)
	{
	  video(id:$id)
	  {
	    id
	    created    
	    dubbrSegments
	    {
	      start
	      duration
	      meta
	      {
	        id
	        track
	        {
	          langCode
	        }
	        trackId
	        text
	      }
	    }
	    track(preferredLanguages: ["eng"]) {
	      id
	            langCode
	            title
	            asset {
	                representations(type: "audio") {
	                format
	                    href
	                }
	            }
	        }
	  }
	}
	"""
	getAudioInfo_variables={"id":audio_id}


	# Function calls
	audioInfo_JSON = ast.literal_eval(json.dumps(getAudioInfo(getAudioInfo_query,getAudioInfo_variables)))# Execute the query
	download_status = download_audio(audioInfo_JSON)
	if(download_status == True):
		convert_status = convert_audio()
		if(convert_status == True):
			#do call some thing else
		else:
			print("Audio did not get converted correctly")
	else:
		print('Audio did not get downloaded')





#1. get audio informations
def getAudioInfo(query,variables): 
    request = requests.post("https://ci.alugha.com/graphql", json={"query": query, "variables":variables})#, headers=headers)
    if request.status_code == 200:
        return request.json()
    else:
        raise Exception("Query failed to run by returning code of {}. {}".format(request.status_code, query))
        

#2. Download the audio
def download_audio(audioInfo_JSON):
	if(True):
	    my_json = abcd
	    print("id=",my_json['data']['video']['id'])
	    if my_json['data']['video']['track']['asset'] is not None:
	        for j in range(len(my_json['data']['video']['track']['asset']['representations'])):
	            audio_format = my_json['data']['video']['track']['asset']['representations'][j]['format']
	                #...consider only mp4 
	            if(audio_format == "mp4"):#or audio_format == "m4a" 
	                #print "format =",audio_format 
	                url_path = my_json['data']['video']['track']['asset']['representations'][j]['href']
	                    #print "link   = ",url_path
	                DOWNLOAD_DIR = '/home/megha/1_audio_current/download_19-10-2018_test' #...replace this with the destination for the audio files to download 
	                    #...FN = file name
	                if(False):
	                    FN_firstPart = url_path.split('/')[-2]
	                    FN_lastPart = url_path.split('/')[-1]
	                        #print FN_firstPart
	                        #print FN_lastPart
	                    FN = FN_firstPart + "_" + FN_lastPart
	                    #...FP = file path
	                FN = my_json['data']['video']['id']+".mp4"
	                    #FP_src = os.path.join(DOWNLOAD_DIR, FN_lastPart)
	                FP_des = os.path.join(DOWNLOAD_DIR, FN)
	                if not os.path.exists(FP_des):
	                    a = wget.download(url=url_path, out=DOWNLOAD_DIR)# every thing from this path will get downloaded with m4a format and with default audio name which is in the link
	                    print(a)
	                    os.rename(a, FP_des) # renaming m4a to mp4
	                    return True
	                else:
	                    print("file alreday exist")
	                    return True
	        else:
	            print("no files to download")
	            return False

#3, Convert the audio
def convert_audio():
	"""
	converting all mp4 audio to wav file with the following specification. 
    -WAVE files with 16-bit
    -16 kHz
    -mono 
	"""
	inputdir_convert = '/home/megha/1_audio_current/download_19-10-2018_test'
	outputdir_convert = '/home/megha/1_audio_current/download_19-10-2018_test'
	if(len(os.listdir(inputdir_convert)) == 1): # >1 means their are 2 mp4 audio or 1 mp4 and wavg file, in both the case its not correct
	    for filename in os.listdir(inputdir_convert):    
	        actual_filename = filename[:-4]
	        if(filename.endswith(".mp4")):  #filename.endswith(".m4a") or       
	            os.system('ffmpeg -i {} -acodec pcm_s16le -ac 1 -ar 16000 {}/{}.wav'.format(inputdir_convert+'/'+filename, outputdir_convert, actual_filename))
	            return True
	        else:
	            return False
	else:
	    print("converted file already exist")
	            return True
            










  
if __name__== "__main__":
  main(sys.argv[1:])
