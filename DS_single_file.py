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
SPLIT_DIR    = '/home/megha/1_audio_current/download_19-10-2018_test/wave_files_audio_split'
#you should change the token number always 
Authorization = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE1NDA5OTA4NTgsImlhdCI6MTU0MDM4NjA1OCwianRpIjoiZDlkNGNmNTMtZDc4Yy0xMWU4LWFlOTEtMWJhMDcwNDM5ZmQzIiwicm9sZSI6MSwidXNlcmlkIjoiYTM4NDdkMmQtYzMwMi0xMWU3LWE0ZjUtYzllN2E1MmViZTY5In0.-CXYig811mUsY6ummmHWkJF3N1MOpDSRbg07W4toi2A"


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
				toCSV_status = splitAudioToCSV()
				if(toCSV_status == True):
					DS_output = pd.read_csv(SPLIT_DIR+'/deepspeech_prediction.csv', sep=',')
					updateMutationStatus = updateText(DS_output,Authorization)
					if(updateMutationStatus == True):
						print("Done")
					else:
						print("Updating unsuccessful")

				else:
					print("Extracting segment audios to csv not successful") 
			else:
				print("Spliting of audio files was not successful")
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
	#DOWNLOAD_DIR = '/home/megha/1_audio_current/download_19-10-2018_test'
	DOWNLOAD_DIR = '/home/megha/1_audio_current/download_19-10-2018_test'
	if(len(os.listdir(DOWNLOAD_DIR)) <= 2): # >2 means their are 2 mp4 audio or 1 mp4 and wav file, in both the case its not correct. 2 bcz I will have 1 folder for split audio and 1 mp4 audio
		if(len(os.listdir(DOWNLOAD_DIR))== 1):
			print("Could not find mp4 audio")
		else:
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
def splitAudio(segment_info):
	#DOWNLOAD_DIR = '/home/megha/1_audio_current/download_19-10-2018_test'    
	#outputdir_split = '/home/megha/1_audio_current/download_19-10-2018_test/wave_files_audio_split'
	for filename in os.listdir(DOWNLOAD_DIR):
	    if(filename.endswith(".wav")):
	        print("-----------------------------------"+filename+"--------------------------------------")
	        actual_filename = filename[:-4]
	        for i in range(0, len(segment_info)): 
	            if(segment_info.audio_id[i] == actual_filename):
	                myaudio = AudioSegment.from_file(DOWNLOAD_DIR+"/"+filename, "wav")
	                array_dubbrSegemnt_start = segment_info['dubbrSegemnt_start'].iloc[i]
	                array_dubbrSegemnt_duration = segment_info['dubbrSegemnt_duration'].iloc[i]
	                array_segemntId = segment_info['segemntId'].iloc[i]
	                for k in range(0, len(array_dubbrSegemnt_start)):    
	                    chunk = myaudio[array_dubbrSegemnt_start[k]:array_dubbrSegemnt_start[k]+array_dubbrSegemnt_duration[k]]
	                    chunk_name =  array_segemntId[k]+"_"+actual_filename +".wav" #  chunk_name = segmentId_audioId
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
	
#6. Extracting split audio info to csv file
def splitAudioToCSV():
	df_excel = pd.DataFrame(columns=['A','B'])
	if(len(os.listdir(SPLIT_DIR)) > 1):
		for eachfile in os.listdir(SPLIT_DIR):
			if eachfile.endswith(".wav"):
				#file_Path = SPLIT_DIR + "/" +eachfile
				processed_data = "Transcript has not been generated for this segment"
				df2 = pd.DataFrame([[eachfile,processed_data]], columns=list('AB'))
				df_excel = df_excel.append(df2)
	else:
		print("There are no wav files to extract to csv")
		return False
	df_excel = df_excel.sort_values(by=['A'])
	df_excel = df_excel.rename(index=str, columns={"A": "audio_segments", "B": "audio_segment_transcript"})
	df_excel["segmentMetaId"] = "" #adding empty column
	df_excel = df_excel[['audio_segments','audio_segment_transcript','segmentMetaId']]#ignoring unwanted coulmn
	for i in range(len(df_excel['audio_segments'])):
		segmentMetaId = df_excel['audio_segments'][i].split('_')[0]#you are taking 0 bcz u decided that you will save segmentmetaId as the first part in the file naming.
		df_excel['segmentMetaId'][i] = segmentMetaId
	#df_excel
	df_excel.to_csv(SPLIT_DIR+ "/deepspeech_prediction.csv", sep=',') #in the "SPLIT_DIR" folder, the csv file will be saved
	return True


#7. Mutation function
def updateText(DS_output,Authorization):
	for i in range(len(DS_output['audio_segments'])):
		#updateMutation = """mutation($segmentMetaId: ID!,$accessKey: String!,$data: UpdateSegmentMetaInput!){updateSegmentMeta(segmentMetaId:$segmentMetaId,data:$data, accessKey: $accessKey){id}}"""
		updateSegmentMetaQuery = """
		mutation($segmentMetaId: ID!,$accessKey: String!,$data: UpdateSegmentMetaInput!)
		{
			updateSegmentMeta(segmentMetaId:$segmentMetaId,data:$data, accessKey: $accessKey)
			{
				id
				text
			}
		}
		"""
		updateMutation_variables= {"segmentMetaId": DS_output['segmentMetaId'][i],"data": {"text":  DS_output['audio_segment_transcript'][i]},"accessKey": "mrDepUi6iWbrU8JL6RnEcgBPASIdhqudrSeFnYxynGJ1HxVy2lF7djznSR3AGHLF"}
		#Authorization = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE1NDA5OTA4NTgsImlhdCI6MTU0MDM4NjA1OCwianRpIjoiZDlkNGNmNTMtZDc4Yy0xMWU4LWFlOTEtMWJhMDcwNDM5ZmQzIiwicm9sZSI6MSwidXNlcmlkIjoiYTM4NDdkMmQtYzMwMi0xMWU3LWE0ZjUtYzllN2E1MmViZTY5In0.-CXYig811mUsY6ummmHWkJF3N1MOpDSRbg07W4toi2A"
		request = requests.post("https://ci.alugha.com/graphql",json={"query":updateSegmentMetaQuery, "variables":updateMutation_variables}, headers={"Authorization" : Authorization })
		if request.status_code == 200:
			#return request.json()
			print(request.json())
			return True
		else:
			#raise Exception("Query failed to run by returning code of {}. {}".format(request.status_code, query))
			print("Query failed to run by returning code of {}. {}".format(request.status_code, updateSegmentMetaQuery))
			return False

 
if __name__== "__main__":
  main(sys.argv[1:])
