#!/usr/bin/python

import requests
import sys, getopt


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
	
	result = getAudioInfo(getAudioInfo_query,getAudioInfo_variables) # Execute the query



#1. get audio informations
def getAudioInfo(query,variables): 
    request = requests.post("https://ci.alugha.com/graphql", json={"query": query, "variables":variables})#, headers=headers)
    if request.status_code == 200:
        return request.json()
    else:
        raise Exception("Query failed to run by returning code of {}. {}".format(request.status_code, query))
        






  
if __name__== "__main__":
  main(sys.argv[1:])
