package main

import (
    "fmt"
    "net/http"
    "log"
    "io/ioutil"
    "encoding/json"
    "strings"
    "os"
)


// func filterCandidateList(playlist []string, candidateList []string) []string {
//   answer := []string{}
//   for i := range candidateList {
//     if strings.Contains(candidateList[i][1], "Commentary") {

//     }  
//   }


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
    items := data.(map[string]interface{})["artists"]
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
      tracksToAdd = []byte("empty")
    } else {
      // tracksToAdd = computeNewTracks(songList)
      tracksToAdd = []byte("empty")
    }
    w.Header().Set("Access-Control-Allow-Origin", "*")
    w.Header().Set("Access-Control-Expose-Headers", "Access-Control-Allow-Origin")
    w.Header().Set("Access-Control-Allow-Headers","Origin, X-Requested-With, Content-Type, Accept")
    w.Write(tracksToAdd)
    
}


func writePlaylistData(f *os.File, data map[string]interface{}, token string) {
  playlists := data["items"].([]interface{})
  client := &http.Client{}
  for i := range playlists {
    playlist := playlists[i].(map[string]interface{}) 
    tracksObj := playlist["tracks"]
    tracksURL := tracksObj.(map[string]interface{})["href"].(string)
    var tracks []interface{}
    for true {
      req, _ := http.NewRequest("GET", tracksURL, nil)
      req.Header.Add("Authorization", "Bearer " + token)
      res, _ := client.Do(req)
      jdata, _ := ioutil.ReadAll(res.Body)
      res.Body.Close()
      var tracklistObj interface{}
      json.Unmarshal(jdata, &tracklistObj)
      tracksList := tracklistObj.(map[string]interface{})["items"].([]interface{})
      for j := range tracksList  {
        track := tracksList[j].(map[string]interface{})["track"]
        trackId := track.(map[string]interface{})["id"]
        tracks = append(tracks, trackId)
      }
      if tracklistObj.(map[string]interface{})["next"] == nil {
        break
      } else {
        tracksURL = tracklistObj.(map[string]interface{})["next"].(string)
      }
    }
    // fmt.Fprintln(f, playlist["id"])
    fmt.Fprintln(f, playlist["id"], tracks)
    fmt.Printf("Writing playlist to file\n")
  }
}


func idHandler(w http.ResponseWriter, r *http.Request) {
  request := strings.TrimSuffix(r.URL.Path[5:], "}")
  idAndToken := strings.Split(request, ",")
  if len(idAndToken) != 2 {
    return
  }
  // id := "spotify"
  id := idAndToken[0]
  token := idAndToken[1] 
  
  url := "https://api.spotify.com/v1/users/" + id + "/playlists"
  client := &http.Client{}
  req, _ := http.NewRequest("GET", url, nil)
  req.Header.Add("Authorization", "Bearer " + token)
  res, _ := client.Do(req)
  jdata, _ := ioutil.ReadAll(res.Body)
  res.Body.Close()
  var obj interface{}
  json.Unmarshal(jdata, &obj)
  data := obj.(map[string]interface{})
  wd, _ := os.Getwd()
  filePath := wd + "/../userData/" + id
  os.Remove(filePath)
  f, _ := os.Create(filePath)
  defer f.Close()
  writePlaylistData(f, data, token)
  for true {
    if data["next"] == nil {
      break
    }
    url = data["next"].(string)
    req, _ = http.NewRequest("GET", url, nil)
    req.Header.Add("Authorization", "Bearer " + token)
    res, _ = client.Do(req)
    jdata, _ = ioutil.ReadAll(res.Body)
    res.Body.Close()
    var obj interface{}
    json.Unmarshal(jdata, &obj)
    data = obj.(map[string]interface{})
    writePlaylistData(f, data, token)
  }
  print("left the loop")
}

func artistHandler(w http.ResponseWriter, r *http.Request) {
    id := r.URL.Path[8:]
    firstDegreeList := fetchRelatedArtist(id)
    type AdjList2D struct {
      ArtistID string
      Neighbors []string
    }
    type AdjList1D struct {
      ArtistID string
      AdjList  []AdjList2D
    }
    var list []AdjList2D
    for i := range firstDegreeList {
      adj_id := firstDegreeList[i]
      list2D := fetchRelatedArtist(adj_id)
      obj2D := new(AdjList2D)
      obj2D.ArtistID = adj_id
      obj2D.Neighbors = list2D
      list = append(list, *obj2D)
    }
    obj1D := new(AdjList1D)
    obj1D.ArtistID = id
    obj1D.AdjList = list
    res, err := json.MarshalIndent(obj1D, "", "\t")
    if err != nil {
      fmt.Println("error:", err)
    }
    os.Stdout.Write(res)
    fmt.Fprintf(w, "%s", res)
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
    http.HandleFunc("/ID/", idHandler)
    http.HandleFunc("/token/", authenticateHandler)
    http.HandleFunc("/refresh/", refreshHandler)
    http.HandleFunc("/artist/", artistHandler)
    fmt.Println("Starting server. Use <Ctrl-C> to exit.")
    http.ListenAndServe(":8080", nil)
}