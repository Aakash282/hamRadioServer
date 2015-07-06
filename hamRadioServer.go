package main

import (
    "fmt"
    "net/http"
    "log"
    "io/ioutil"
    "encoding/json"
    // "strings"
)


// func filterCandidateList(playlist []string, candidateList []string) []string {
//   answer := []string{}
//   for i := range playlist


//   return answer
// }

// Code for fetching from Spotify.
func fetchTrackProfile(id string) (r []string) {
    URL := "http://api.spotify.com/v1/tracks/" + id
    res, err := http.Get(URL)
    if err != nil {
      log.Fatal(err)
    }
    jprofile, err := ioutil.ReadAll(res.Body)
    res.Body.Close()
    if err != nil {
      log.Fatal(err)
    }
    var data interface{}
    err = json.Unmarshal(jprofile, &data)
    if err != nil {
      log.Fatal(err)
    }
    profile := data.(map[string]interface{})
    artistObj := profile["artists"]
    artistMap := artistObj.([]interface{})[0]
    artist := artistMap.(map[string]interface{})["id"].(string)  
    songName := profile["name"].(string)
    return []string{artist, songName}
}

func fetchArtistAlbums(id string) (r []string) {
    URL := "http://api.spotify.com/v1/artists/" + id + "/albums?album_type=single,album"
    res, err := http.Get(URL)
    if err != nil {
      log.Fatal(err)
    }
    jdata, err := ioutil.ReadAll(res.Body)
    res.Body.Close()
    if err != nil {
      log.Fatal(err)
    }
    var data interface{}
    err = json.Unmarshal(jdata, &data)
    if err != nil {
      log.Fatal(err)
    }
    albums := []string{}
    items := data.(map[string]interface{})["items"]
    for i := range items.([]interface{}) {
      albumMap := items.([]interface{})[i].(map[string]interface{})
      albumId := albumMap["id"].(string)
      albums = append(albums, albumId)
    }
    return albums
}

func fetchAlbumTracks(id string) (r []string) {
    URL := "http://api.spotify.com/v1/albums/" + id + "/tracks"
    res, err := http.Get(URL)
    if err != nil {
      log.Fatal(err)
    }
    jdata, err := ioutil.ReadAll(res.Body)
    res.Body.Close()
    if err != nil {
      log.Fatal(err)
    }
    var data interface{}
    err = json.Unmarshal(jdata, &data)
    if err != nil {
      log.Fatal(err)
    }
    tracks := []string{}
    items := data.(map[string]interface{})["items"]
    for i := range items.([]interface{}) {
      trackMap := items.([]interface{})[i].(map[string]interface{})
      trackId := trackMap["id"].(string)
      trackName := trackMap["name"].(string)
      tracks = append(tracks, trackId)
      tracks = append(tracks, trackName)
    }
    return tracks
}

func fetchRelatedArtist(id string) (r []string) {
    URL := "http://api.spotify.com/v1/artists/" + id + "/related-artists"
    res, err := http.Get(URL)
    if err != nil {
      log.Fatal(err)
    }
    jdata, err := ioutil.ReadAll(res.Body)
    res.Body.Close()
    if err != nil {
      log.Fatal(err)
    }
    var data interface{}
    err = json.Unmarshal(jdata, &data)
    if err != nil {
      log.Fatal(err)
    }
    relateds := []string{}
    items := data.(map[string]interface{})["items"]
    for i := range items.([]interface{}) {
      relatedMap := items.([]interface{})[i].(map[string]interface{})
      relatedId := relatedMap["id"].(string)
      relateds = append(relateds, relatedId)
    }
    return relateds
}

// This function handles getting unknown data from Spotify
func fetchFromSpotify(id string, t string) (r []string) {
    switch t {
    case "track": return fetchTrackProfile(id)
    case "artist": return fetchArtistAlbums(id)
    case "album": return fetchAlbumTracks(id)
    case "seed_artist": return fetchRelatedArtist(id)
    default: return []string{}
    }

}

//
// Here is the server code itself
// 

//  This handler takes care of adding a new song
func requestHandler(w http.ResponseWriter, r *http.Request) {
    // songList := strings.Split(r.URL.Path[6:], ",")
    var tracksToAdd []byte
    if len(r.URL.Path) == 6 {
      tracksToAdd = []byte("empty\n")
    } else {
      // tracksToAdd = computeNewTracks(songList)
      tracksToAdd = []byte("string\n")
    }
    w.Header().Set("Access-Control-Allow-Origin", "*")
    w.Header().Set("Access-Control-Expose-Headers", "Access-Control-Allow-Origin")
    w.Header().Set("Access-Control-Allow-Headers","Origin, X-Requested-With, Content-Type, Accept")
    w.Write(tracksToAdd)
    
}

// This handler takes care of the initial authorization token
func authenticateHandler(w http.ResponseWriter, r *http.Request) {
    fmt.Fprintf(w, "Authenticating %s!", r.URL.Path[0:])
}

// This handler takes care of handling refresh tokens
func refreshHandler(w http.ResponseWriter, r *http.Request) {
    fmt.Fprintf(w, "Refreshing token")
}

// This is the main function for the server
func main() {
    http.HandleFunc("/song/", requestHandler)
    http.HandleFunc("/token/", authenticateHandler)
    http.HandleFunc("/refresh/", refreshHandler)
    http.ListenAndServe(":8080", nil)
}