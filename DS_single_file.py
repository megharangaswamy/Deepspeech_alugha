#!/usr/bin/python

import requests
import sys, getopt
import json, ast
import os
import wget 
import pandas as pd
import ffmpy
from pydub import AudioSegment

DOWNLOAD_DIR = '/home/megha/1_audio_current/download_19-10-2018_test'
SPLIT_DIR = '/home/megha/1_audio_current/download_19-10-2018_test/wave_files_audio_split'

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
			segment_info = pd.DataFrame(columns=['audio_id','dubbrSegemnt_start','dubbrSegemnt_duration','segemntId','trackId','langCode'])
			segment_info = getSegmentInfo(audioInfo_JSON)
			split_status = splitAudio(segment_info)
			if(split_status == True):
				# call next method
			else:
				print("Spliting of audio files was not success")
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
	    my_json = audioInfo_JSON
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
	                    print(a)o
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
	#DOWNLOAD_DIR = '/home/megha/1_audio_current/download_19-10-2018_test'
	DOWNLOAD_DIR = '/home/megha/1_audio_current/download_19-10-2018_test'
	if(len(os.listdir(DOWNLOAD_DIR)) == 2): # >2 means their are 2 mp4 audio or 1 mp4 and wav file, in both the case its not correct. 2 bcz I will have 1 folder for split audio and 1 mp4 audio
	    for filename in os.listdir(DOWNLOAD_DIR):    
	        actual_filename = filename[:-4]
	        if(filename.endswith(".mp4")):  #filename.endswith(".m4a") or       
	            os.system('ffmpeg -i {} -acodec pcm_s16le -ac 1 -ar 16000 {}/{}.wav'.format(DOWNLOAD_DIR+'/'+filename, DOWNLOAD_DIR, actual_filename))
	            return True
	        else:
	            return False
	else:
	    print("converted file already exist")
	            return True


#4, Get segment info
def getSegmentInfo(audioInfo_JSON):
	df = pd.DataFrame(columns=['A','B','C','D','E','F'])
	my_json = audioInfo_JSON
	if(my_json['data']['video']['track']['langCode'] == 'eng'):# restricting videos whithout english tracks
	    if len(my_json['data']['video']['dubbrSegments'])>0:    
	        audio_id = my_json['data']['video']['id']
	        dubbrSeg_start_array = []
	        dubbrSeg_duration_array = []
	        segmentId_array = []
	        for j in range(len(my_json['data']['video']['dubbrSegments'])):
	            dubbrSeg_start = my_json['data']['video']['dubbrSegments'][j]['start']
	            dubbrSeg_duration =  my_json['data']['video']['dubbrSegments'][j]['duration']
	            for k in range(len(my_json['data']['video']['dubbrSegments'][j]['meta'])):
	                if(my_json['data']['video']['dubbrSegments'][j]['meta'][k]['track']['langCode'] == 'eng'):
	                    segmentId = my_json['data']['video']['dubbrSegments'][j]['meta'][k]['id'] 
	            dubbrSeg_start_array.append(dubbrSeg_start)
	            dubbrSeg_duration_array.append(dubbrSeg_duration)
	            segmentId_array.append(segmentId)
	            segmentId_array = ast.literal_eval(json.dumps(segmentId_array)) # to remove u'
	                #print('segmentId = ' , segmentId)
	                #print('start =', dubbrSeg_start)
	                #print('duration',dubbrSeg_duration)
	        track = my_json['data']['video']['track']
	        langCode = track['langCode']
	        trackId = track['id']
	        """
	        print('--------------------------------------------------------')
	        print(audio_id)
	        print(dubbrSeg_start_array)
	        print(dubbrSeg_duration_array)
	        print(segmentId_array)
	        print(trackId)
	        print(langCode)
	        print('--------------------------------------------------------')
	        """

	        df2 = pd.DataFrame([[audio_id,dubbrSeg_start_array,dubbrSeg_duration_array,segmentId_array,trackId,langCode]], columns=list('ABCDEF'))
	        df = df.append(df2) 
	        #print(df)
	        df = df.rename(index=str, columns={"A": "audio_id", "B": "dubbrSegemnt_start","C" : "dubbrSegemnt_duration","D" : "segemntId","E" : "trackId","F": "langCode"})
	return df

#5. Splitting audio wrt segment informations
def splitAudio():
	#DOWNLOAD_DIR = '/home/megha/1_audio_current/download_19-10-2018_test'    
	#outputdir_split = '/home/megha/1_audio_current/download_19-10-2018_test/wave_files_audio_split'
	for filename in os.listdir(DOWNLOAD_DIR):
	    if(filename.endswith(".wav")):
	        print("-----------------------------------"+filename+"--------------------------------------")
	        actual_filename = filename[:-4]
	        for i in range(0, len(df)): 
	            if(df.audio_id[i] == actual_filename):
	                myaudio = AudioSegment.from_file(DOWNLOAD_DIR+"/"+filename, "wav")
	                array_dubbrSegemnt_start = df['dubbrSegemnt_start'].iloc[i]
	                array_dubbrSegemnt_duration = df['dubbrSegemnt_duration'].iloc[i]
	                array_segemntId = df['segemntId'].iloc[i]
	                for k in range(0, len(array_dubbrSegemnt_start)):    
	                    chunk= myaudio[array_dubbrSegemnt_start[k]:array_dubbrSegemnt_start[k]+array_dubbrSegemnt_duration[k]]
	                    chunk_name =  array_segemntId[k]+"_"+actual_filename+".wav".format(k) #  chunk_name = segmentId_audioId
	                    file_destination = SPLIT_DIR+"/"+chunk_name 
	                    if not os.path.exists(file_destination):
	                        print("exporting", chunk_name)
	                        chunk.export(file_destination , format="wav")
	                        return True
	                    else:
	                        print("File already exist")
	                        return True
	            else:
	            	print("No segment information found")
	            	return False
	    else:
	    	print("No wav file to split")
	    	return False











  
if __name__== "__main__":
  main(sys.argv[1:])
