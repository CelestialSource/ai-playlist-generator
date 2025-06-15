import customtkinter as ctk
from ai.Gemini import GeminiClient
from providers.Spotify import SpotifyClient
from gui import Gui, FrameWrapper
import console
import threading
import messagebox

class AppState:
    '''A simple class to hold all application variables.'''
    def __init__(self, appWidgets):
        # API and User Credentials
        # appWidgets is passed for cross-thread functionality (Threading.Thread())
        # The following keys (geminiKey, clientSecret) should never be readable these values are temporary and not for prod
        self.geminiKey = ctk.StringVar(value='AIzaSyBhR-n9lF353FXJZBtGtQhAOwOa-_0H9aQ')
        self.clientId = ctk.StringVar(value='69287e1a7be34994a28dfb2893cf8deb')
        self.clientSecret = ctk.StringVar(value='0b3db5dd4256485d92a95eba3420a8cc')
        self.spotifyUsername = ctk.StringVar(value='31vuaqgukgtreawaemkpaxjh5miy')

        # User Input and App Logic
        self.promptText = ctk.StringVar(value='chill 2010s songs')
        self.playlistName = ctk.StringVar(value='New Playlist')
        self.playlistLength = ctk.IntVar(value=15)
        self.playlistLengthCustom = ctk.StringVar(value='15')
        self.seedPlaylist = ctk.StringVar(value='-- No seed playlist selected --')

        # Internal State
        self.musicClient = None
        self.aiClient = None
        self.previewedTracks = []
        self.latestPlaylistId = None
        self.latestPlaylistName = None
        self.playlistsMap = None
        
        self.appWidgets = appWidgets


if __name__ == '__main__':#
    guiApp = Gui(title='AI Music Playlist Generator')
    # All widgets will be stored in the 'appWidgets' dictionary
    appWidgets = {}
    # All variables are now encapsulated in the 'appState' instance
    appState = AppState(appWidgets)

    def setupGUI(gui, appState, appWidgets):
        windowFrame = gui.windowFrame
        appWidgets['root'] = gui.window
        # appWidgets structure:
        '''
            appWidgets: {
                root: gui.window (ctk.CTk)
                importButton: (ctk.CTkButton)
                seedDropdown: (ctk.CTkCombobox)
                previewButton: (ctk.CTkButton)
                createPlaylistButton: (ctk.CTkButton)
                deletePlaylistButton: (ctk.CTkButton)
                previewList: (ctk.CTkLabel)
                statusLabel: (ctk.CTkLabel)
            }
            utilizes Threading
        '''
        
        windowFrame.grid_columnconfigure(1, weight=1)

        apiFrame = FrameWrapper(gui, windowFrame, 'apiFrame')
        apiFrame.createCustomTextbox('Gemini API Key:', appState.geminiKey, next=True, show='*')
        apiFrame.createCustomTextbox('Spotify Client ID:', appState.clientId, next=True, show='*')
        apiFrame.createCustomTextbox('Spotify Client Secret:', appState.clientSecret, next=True, show='*')
        apiFrame.createCustomTextbox('Spotify Username:', appState.spotifyUsername, next=True)
        
        promptFrame = FrameWrapper(gui, windowFrame, 'promptFrame')
        promptFrame.createCustomTextbox('Theme prompt:', appState.promptText, next=True)
        promptFrame.createCustomTextbox('Playlist Name:', appState.playlistName, next=True)
        promptFrame.createLabel('Playlist Length:', 'w', True)

        def onPlaylistSliderChange(value):
            appState.playlistLengthCustom.set(str(int(round(float(value)))))
        
        lengthRange = [5, 50]

        playlistSlider = promptFrame.createSlider({
            'min': lengthRange[0], 'max': lengthRange[1], 'steps': lengthRange[1] - lengthRange[0],
            'var': appState.playlistLength,
            'function': onPlaylistSliderChange,
            'default': appState.playlistLength.get()
        }, 'ew', False)
        
        def onlengthEntryChange(event=None):
            try:
                newValueStr = appState.playlistLengthCustom.get()
                if not newValueStr:
                    appState.playlistLength.set(lengthRange[0])
                    playlistSlider.set(lengthRange[0])
                    return
                newValue = max(lengthRange[0], min(int(newValueStr), lengthRange[1]))
                appState.playlistLength.set(newValue)
                playlistSlider.set(newValue)
            except ValueError:
                appState.playlistLengthCustom.set(str(appState.playlistLength.get()))

        lengthEntry = promptFrame.createEntry(appState.playlistLengthCustom, 'e', False)
        lengthEntry.bind('<KeyRelease>', onlengthEntryChange)
        
        seedFrame = FrameWrapper(gui, windowFrame, 'seedFrame')
        seedFrame.createLabel('Seed Playlist: ', 'w', True)
        
        # Store widgets in the dictionary
        appWidgets['seedDropdown'] = seedFrame.createCombobox({
            'list': [appState.seedPlaylist.get()], 'var': appState.seedPlaylist, 'state': 'disabled'
        }, 'ew', False)

        def startLoadPlaylistsThread():
            appWidgets['importButton'].configure(state='disabled')
            appWidgets['seedDropdown'].configure(state='disabled')
            appWidgets['root'].after(0, lambda: appWidgets['statusLabel'].configure(text='Status: Loading Spotify playlists...'))
            threading.Thread(target=loadPlaylists, args=(appState, appWidgets), daemon=True).start()

        appWidgets['importButton'] = seedFrame.createButton({'text': 'Import Playlists', 'function': startLoadPlaylistsThread}, 'ew', False)
            
        actionFrame = FrameWrapper(gui, windowFrame, 'actionFrame')
        actionFrame.frame.grid_columnconfigure((0,1,2), weight=1)

        def startPreviewThread():
            _resetButtonsForNewOperation()
            appWidgets['previewButton'].configure(state='disabled')
            appWidgets['root'].after(0, lambda: appWidgets['statusLabel'].configure(text=('Status: Starting song preview...')))
            threading.Thread(target=previewSongs, args=(appState, appWidgets), daemon=True).start()
        
        def startCreatePlaylistThread():
            appWidgets['createPlaylistButton'].configure(state='disabled')
            appWidgets['previewButton'].configure(state='disabled')
            appWidgets['root'].after(0, lambda: appWidgets['statusLabel'].configure(text=('Status: Creating playlist on Spotify...')))
            threading.Thread(target=createActualPlaylist, args=(appState, appWidgets), daemon=True).start()

        def startDeletePlaylistThread():
            if not appState.latestPlaylistId: return
            if messagebox.askyesno('Confirm Deletion', f'Delete \'{appState.latestPlaylistName}\'?'):
                appWidgets['deletePlaylistButton'].configure(state='disabled')
                appWidgets['root'].after(0, lambda: appWidgets['statusLabel'].configure(text=('Status: Deleting playlist...')))
                threading.Thread(target=deleteGeneratedPlaylist, args=(appState, appWidgets), daemon=True).start()

        appWidgets['previewButton'] = actionFrame.createButton({'text': 'Preview Songs', 'function': startPreviewThread}, None, True) # type: ignore
        appWidgets['createPlaylistButton'] = actionFrame.createButton({'text': 'Create Playlist', 'function': startCreatePlaylistThread, 'state': 'disabled'}, None, False) # type: ignore
        appWidgets['deletePlaylistButton'] = actionFrame.createButton({'text': 'Delete Playlist', 'function': startDeletePlaylistThread, 'state': 'disabled'}, None, False) # type: ignore
        appWidgets['deletePlaylistButton'].configure(fg_color=('#B00020', '#CF6679'), hover_color=('#800018', '#FF8B8B'))

        previewFrame = FrameWrapper(gui, windowFrame, 'previewFrame')
        previewFrame.frame.grid_columnconfigure(0, weight=1)
        previewFrame.frame.grid_rowconfigure(0, weight=1)
        previewFrame.frame.grid_columnconfigure(1, weight=0)
        windowFrame.grid_rowconfigure(gui.gridHandler.getRow(), weight=1)

        appWidgets['previewList'] = previewFrame.createTreeview({'columns': {'song': 200, 'artist': 200, 'status': 100}, 'rowspan': 1}, 'nsew', False)
        
        gui.gridHandler.nextRow()
        # Create and store the status label
        appWidgets['statusLabel'] = ctk.CTkLabel(windowFrame, text='Status: Ready', anchor='w')
        appWidgets['statusLabel'].grid(row=gui.gridHandler.getRow(), column=0, columnspan=2, sticky='ew', padx=10, pady=5)

        # Redefine _resetButtonsForNewOperation to use appWidgets
        def _resetButtonsForNewOperation():
            appWidgets['previewButton'].configure(state='normal')
            appWidgets['createPlaylistButton'].configure(state='disabled')
            appWidgets['deletePlaylistButton'].configure(state='disabled')
            appState.latestPlaylistId = None
            appState.latestPlaylistName = None
            appState.previewedTracks = []
            if hasattr(appWidgets['previewList'], 'get_children'):
                for i in appWidgets['previewList'].get_children():
                    appWidgets['previewList'].delete(i)
    
    # --- Helper functions are now outside setupGUI ---
    # _initializeApiClients
    # previewSongs
    # createActualPlaylist
    # deleteGeneratedPlaylist

    def _initializeApiClients(appState):
        '''
            Calls:
            ↳ musicClient → SpotifyClient
            ↳ aiClient → GeminiClient
        '''
        if not appState.musicClient:
            appState.musicClient = SpotifyClient(clientId=appState.clientId.get(), clientSecret=appState.clientSecret.get(), username=appState.spotifyUsername.get())
        if not appState.aiClient:
            appState.aiClient = GeminiClient(apiKey=appState.geminiKey.get())

    def loadPlaylists(appState, appWidgets):
        '''
            Calls:
            ↳ _initializeApiClients
            ↳ musicClient.authenticate
            ↳ musicClient.getPlaylists
                ↳ playlistsMap: dict
                    ↳ playlist['name'] → playlist['id'] (uri)
                ↳ playlistNames: list
                    ↳ playlist['name]
        '''
        try:
            _initializeApiClients(appState)
            appState.musicClient.authenticate()
            appWidgets['root'].after(0, lambda: appWidgets['statusLabel'].configure(text=('Status: Fetching user playlists...')))
            playlistsData = appState.musicClient.getPlaylists()
            
            playlistNames = ['-- No seed playlist selected --']
            appState.playlistsMap = {'-- No seed playlist selected --': None}
            for playlist in playlistsData.get('items', []):
                appState.playlistsMap[playlist['name']] = playlist['id']
                playlistNames.append(playlist['name'])

            appWidgets['root'].after(0, lambda: appWidgets['seedDropdown'].configure(values=playlistNames))
            appWidgets['root'].after(0, lambda: appWidgets['statusLabel'].configure(text=('Status: Spotify playlists loaded.')))
        except Exception as e:
            ex = e
            appWidgets['root'].after(0, lambda: appWidgets['statusLabel'].configure(text=(f'Status: Error loading playlists - {ex}')))
        finally:
            appWidgets['root'].after(0, lambda: appWidgets['importButton'].configure(state='normal'))
            if appState.musicClient and hasattr(appState.musicClient, 'spHandle'):
                appWidgets['root'].after(0, lambda: appWidgets['seedDropdown'].configure(state='readonly'))

    def previewSongs(appState, appWidgets):
        '''
            Calls:
            ↳ _initializeApiClients
            ↳ musicClient._getPlaylistSongs (playlistsMap[seedPlaylist.get()])
            ↳ aiClient.generateSongs (promptText.get(), playlistLength.get(), seedSongs)
                ↳ songName, artistName → suggest.song, suggest.artist
                ↳ trackUri →  musicClient._getSongURI
        '''
        _initializeApiClients(appState)
        seedSongs = appState.musicClient._getPlaylistSongs(appState.playlistsMap[appState.seedPlaylist.get()])
        songIdeas = appState.aiClient.generateSongs(
            description=appState.promptText.get(), 
            length=appState.playlistLength.get(),
            seedSongs=seedSongs
        )

        for idea in songIdeas:
            songName, artistName = idea.get('song'), idea.get('artist')
            trackUri = appState.musicClient._getSongURI(songName, artistName)
            
            # Use a separate lambda for each case (Found/Not Found)
            # to correctly capture the loop variables.
            if trackUri:
                appState.previewedTracks.append(trackUri)
                if hasattr(appWidgets['previewList'], 'insert'):
                    # FIX: Correctly call insert using a lambda to pass keyword arguments
                    appWidgets['root'].after(
                        0, 
                        lambda s=songName, a=artistName: 
                        appWidgets['previewList'].insert('', 'end', values=(s, a, 'Found'))
                    )
                    appWidgets['root'].after(0, lambda: appWidgets['statusLabel'].configure(text=(f'Status: Starting song preview ({len(appState.previewedTracks)}/{appState.playlistLength.get()})')))
            else:
                # Add the 'Not Found' case back for better UI feedback
                if hasattr(appWidgets['previewList'], 'insert'):
                    appWidgets['root'].after(
                        0, 
                        lambda s=songName, a=artistName: 
                        appWidgets['previewList'].insert('', 'end', values=(s, a, 'Not Found'))
                    )
        
        appWidgets['root'].after(0, lambda: appWidgets['statusLabel'].configure(text=(f'Status: Preview complete. Found ({len(appState.previewedTracks)}/{appState.playlistLength.get()})')))
        if appState.previewedTracks:
            appWidgets['root'].after(0, lambda: appWidgets['createPlaylistButton'].configure(state='normal'))

        appWidgets['root'].after(0, lambda: appWidgets['previewButton'].configure(state='normal'))

    def createActualPlaylist(appState, appWidgets):
        '''
            Calls:
            ↳ _initializeApiClients
            ↳ musicClient.spHandle.current_user()['id']
            ↳ musicClient._createPlaylist
            ↳ musicClient._addTracks
            ↳ latestPlaylistId → playlistData['id']
            ↳ latestPlaylistName →  musicplaylistData['name']
        '''
        try:
            if not appState.previewedTracks: return
            _initializeApiClients(appState)
            userId = appState.musicClient.spHandle.current_user()['id']
            playlistData = appState.musicClient._createPlaylist(userId=userId, name=appState.playlistName.get(), description=appState.promptText.get())
            appState.latestPlaylistId = playlistData['id']
            appState.latestPlaylistName = playlistData['name']
            
            appState.musicClient._addTracks(appState.latestPlaylistId, appState.previewedTracks)
            
            appWidgets['root'].after(0, lambda: appWidgets['statusLabel'].configure(text=(f'Status: Done! Playlist \'{appState.latestPlaylistName}\' created.')))
            messagebox.showinfo('Success', f'Playlist \'{appState.latestPlaylistName}\' created!')
            appWidgets['root'].after(0, lambda: appWidgets['deletePlaylistButton'].configure(state='normal'))
        except Exception as e:
            ex = e
            appWidgets['root'].after(0, lambda: appWidgets['statusLabel'].configure(text=(f'Status: Error creating playlist - {ex}')))
        finally:
            appWidgets['root'].after(0, lambda: appWidgets['previewButton'].configure(state='normal'))
            appWidgets['root'].after(0, lambda: appWidgets['createPlaylistButton'].configure(state='disabled'))

    def deleteGeneratedPlaylist(appState, appWidgets):
        '''
            Calls:
            ↳ _initializeApiClients
            ↳ musicClient.spHandle.current_user()['id']
            ↳ musicClient._unfollowPlaylist
        '''
        try:
            _initializeApiClients(appState)
            userId = appState.musicClient.spHandle.current_user()['id']
            appState.musicClient._unfollowPlaylist(userId=userId, playlistId=appState.latestPlaylistId)
            appWidgets['root'].after(0, lambda: appWidgets['statusLabel'].configure(text=(f'Status: Playlist \'{appState.latestPlaylistName}\' deleted.')))
        except Exception as e:
            ex = e
            appWidgets['root'].after(0, lambda: appWidgets['statusLabel'].configure(text=(f'Status: Error deleting playlist - {ex}')))
        finally:
            appState.latestPlaylistId = None
            appState.latestPlaylistName = None
            appWidgets['root'].after(0, lambda: appWidgets['deletePlaylistButton'].configure(state='disabled'))


    # Pass the application state and widgets objects to the setup function
    setupGUI(guiApp, appState, appWidgets)
    guiApp.window.mainloop()