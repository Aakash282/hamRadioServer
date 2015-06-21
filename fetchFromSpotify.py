import json
import urllib2


# Take spotify internal id, track/album, list of what to return

def fetchTrackProfile(id):
  URL = 'http://api.spotify.com/v1/tracks/' + id
  data = urllib2.urlopen(URL)
  if data.getcode() != 200:
    return []
  jdata = data.read()
  jsonObj = json.loads(jdata)
  artist = jsonObj['artists'][0]['id']
  songName = jsonObj['name']
  return artist, songName

def fetchArtistAlbums(id):
  URL = 'http://api.spotify.com/v1/artists/' + id + '/albums'
  data = urllib2.urlopen(URL)
  if data.getcode() != 200:
    return []
  jdata = data.read()
  jsonObj = json.loads(jdata)
  albums = []
  for i in jsonObj['items']:
    if 'appears_on' in i['album_type'] and 'compilation' in i['album_type']:
      continue
    else:
      albums += [i['id']]
  return albums

def fetchAlbumTracks(id):
  URL = 'http://api.spotify.com/v1/albums/' + id + '/tracks'
  data = urllib2.urlopen(URL)
  if data.getcode() != 200:
    return []
  jdata = data.read()
  jsonObj = json.loads(jdata)
  tracks = []
  for i in jsonObj['items']:
    tracks += (i['id'],  i['name'])
    print (i['id'],  i['name'])
  return tracks

def fetchRelatedArtists(id):
  URL = 'http://api.spotify.com/v1/artists/' + id + '/related_artists'
  data = urllib2.urlopen(URL)
  if data.getcode() != 200:
    return []
  jdata = data.read()
  jsonObj = json.loads(jdata)
  relatedArtist_id = []
  for i in jsonObj['items']:
    relatedArtist_id += i['id']
  return relatedArtist_id

def fetchFromSpotify(id, type):

  if type == 'track':
    return fetchTrackProfile(id)
  elif type == 'artist':
    return fetchArtistAlbums(id)
  elif type == 'album':
    return fetchAlbumTracks
  elif type == 'seed_artist':
    return fetchRelatedArtists
  else:
    return []
