import customtkinter as ctk
import tkinter as tk

class Gui:
    """
    Gui wrapper for ctk
    Follows a Material You 3 Dark inspired theme
    """
    
    _gridKeys = ['row', 'column', 'sticky', 'padx', 'pady', 'rowspan', 'columnspan']
    
    def __init__(self, title='App', padding=10):
        ctk.set_appearance_mode('Dark')
        ctk.set_default_color_theme('blue')

        self.core = ctk.CTk()
        self.core.title(title)
        self.core.geometry('800x600')
        self.core.grid_columnconfigure(0, weight=1)
        self.core.grid_rowconfigure(0, weight=1)

        self.mainFrame = self.createFrame(self.core, corner_radius=10)
        self.mainFrame.grid(column=0, row=0, sticky='nsew', padx=padding, pady=padding)
        
        self.mainFrame.grid_columnconfigure(0, weight=1)
        self.mainFrame.grid_columnconfigure(1, weight=1)
    
    def _getOptions(self, **options):
        grid_options = {}
        for key in self._gridKeys:
            if key in options:
                value = options.pop(key)
                grid_options[key] = value
        return grid_options

    def createFrame(self, parent, **options):
        frame = ctk.CTkFrame(parent, **options)
        return frame

    def createButton(self, parent, text='Button', command=None, state='normal', fg_color=None, hover_color=None, text_color='white', **grid_options):
        button = ctk.CTkButton(parent, text=text, command=command, state=state, corner_radius=8, fg_color=fg_color, hover_color=hover_color, text_color=text_color)
        button.grid(**grid_options)
        return button

    def createLabel(self, parent, text='', **options):
        label = ctk.CTkLabel(parent, text=text, **options)
        label.grid(**self._getOptions(**options))
        return label