import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os

class SpotifyClient:
    oauthScope = 'playlist-modify-private playlist-read-private playlist-read-collaborative'
    addRatelimit = 100

    def __init__(self, clientId, clientSecret, username, redirect='http://127.0.0.1:8888/callback'):
        self.clientId = clientId
        self.clientSecret = clientSecret
        self.username = username
        self.redirect = redirect
        self.spHandle = None
        self.statusUpdater = None

    def authenticate(self):
        if self.spHandle:
            return self.spHandle

        # set env variables for spotipy
        os.environ['SPOTIPY_CLIENT_ID'] = self.clientId
        os.environ['SPOTIPY_CLIENT_SECRET'] = self.clientSecret
        os.environ['SPOTIPY_REDIRECT_URI'] = self.redirect
        try:
            OAuth = SpotifyOAuth(scope=self.oauthScope, username=self.username)
            self.spHandle = spotipy.Spotify(auth_manager=OAuth)
            return self.spHandle
        except Exception as e:
            self.spHandle = None
            raise Exception(f'Spotify authentication failed: {e}')

    def getPlaylists(self):
        return self.spHandle.current_user_playlists()

    def _getPlaylistSongs(self, playlistId):
        songs = []
        songList = self.spHandle.playlist_items(playlistId)
        playlistSongs = songList['items']
        while songList['next']:
            songList = self.spHandle.next(songList)
            playlistSongs.extend(songList['items'])
        
        for item in playlistSongs:
            track = item.get('track')
            if track and track.get('name') and track.get('artists'):
                artist_name = len(track['artists']) > 0 and track['artists'][0]['name'] or 'Unknown Artist'
                songs.append({'song': track['name'], 'artist': artist_name})
        return songs

    def _getSongURI(self, song_name, artist_name):
        query = f'track:{song_name} artist:{artist_name}'
        found = self.spHandle.search(q=query, type='track', limit=1)
        if found['tracks']['items']:
            return found['tracks']['items'][0]['uri']
        return None

    def _createPlaylist(self, userId, name, description, public=False):
        return self.spHandle.user_playlist_create(user=userId, name=name, public=public, description=description)

    def _addTracks(self, playlistId, songURIList):
        if songURIList:
            for i in range(0, len(songURIList), self.addRatelimit):
                batch = songURIList[i:i + self.addRatelimit]
                self.spHandle.playlist_add_items(playlistId, batch)

    def _unfollowPlaylist(self, userId, playlistId):
        self.spHandle.user_playlist_unfollow(user=userId, playlist_id=playlistId)
    
    def setUpdater(self, updater):
        self.statusUpdater = updater