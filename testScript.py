from requests import Session
import json
import urllib2
session = Session()

artistLib = {}
artistBuffer = []
genres = ["alternative%20rock", "blues", "christian%20rock", "country", "christmas", "deep%20house", "dubstep", "edm", "electro", "electronica", "folk", "funk", "hip%20hop", "house", "indie%20pop", "jazz", "k-pop", "latin", "metal", "pop", "pop%20rock", "rap", "rap%20rock", "soul", "soundtrack", "trap%20music"]

# use echonest to fill artist buffer initially
for seed_genre in genres:
    URL = 'https://developer.echonest.com/api/v4/genre/artists?api_key=VBFP0ICNRRIKKKQO6&format=json&bucket=hotttnesss&bucket=id:spotify&results=5&name=' + seed_genre
    jsonGenre = json.loads(urllib2.urlopen(URL).read())
    for artist in jsonGenre['response']['artists']:
        artist_id = str(artist['foreign_ids'][0]['foreign_id'])
        artistBuffer.append(artist_id[15:])


output = 'spotify_track_ids.txt'
processed_artists = 'processed_artists.txt'

file_o = open(output, 'w')
file_pa = open(processed_artists, 'w') #processed artists for easy resume
file_o.write('test pls work\n')
file_pa.write('test bootleg work\n')

c = 0
while len(artistBuffer) > 0:
    artist = artistBuffer.pop(0)
    if artist not in artistLib:
        c += 1
        artistLib[artist] = 1
        #file_pa.write('test bootleg work\n')

        URL = 'http://api.spotify.com/v1/artists/' + artist + '/albums'
        data = urllib2.urlopen(URL)
        if data.getcode() != 200:
            continue
        jdata = data.read()
        jsonObj = json.loads(jdata)
        for i in jsonObj['items']:
            if 'appears_on' in i['album_type'] or 'compilation' in i['album_type']:
                continue
            URL = "http://api.spotify.com/v1/albums/" + str(i['id']) + "/tracks"
            tracks = urllib2.urlopen(URL)
            if tracks.getcode() != 200:
                continue
            jtracks = tracks.read()
            jsonTracks = json.loads(jtracks)
            for j in jsonTracks['items']:
                file_o.write(j['id'] + '\n')

        URL = "http://api.spotify.com/v1/artists/" + artist + "/related-artists"
        rel = urllib2.urlopen(URL)
        if rel.getcode() != 200:
            continue
        jrel = rel.read()
        jsonObj = json.loads(jrel)
        for relArtist in jsonObj['artists']:
            artistBuffer.append(str(relArtist['id']))
        print "artists processed:", c, "buffer size:", len(artistBuffer)
file_o.close()
file_pa.close()


# var url = "https://api.spotify.com/v1/artists/" + artists[0].id + "/related-artists"
# https://api.spotify.com/v1/artists/2gsggkzM5R49q6jpPvazou/related-artists
# spotify:artist:2gsggkzM5R49q6jpPvazou