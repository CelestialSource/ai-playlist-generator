import customtkinter as ctk
import tkinter as tk
from tkinter import ttk # Correct import for ttk widgets

class Gui:
    """
    Gui wrapper for ctk
    Follows a Material You 3 Dark inspired theme
    """
    
    _gridKeys = ['row', 'column', 'sticky', 'padx', 'pady', 'rowspan', 'columnspan']
    
    def __init__(self, title='App', padding=10):
        ctk.set_appearance_mode('Dark')
        ctk.set_default_color_theme('blue')

        self.window = ctk.CTk()
        self.window.title(title)
        self.window.geometry('800x600')
        self.window.grid_columnconfigure(0, weight=1)
        self.window.grid_rowconfigure(0, weight=1)
        
        self.fixTreeview()

        self.windowFrame = self._createFrame(self.window, corner_radius=10)
        self.windowFrame.grid(column=0, row=0, sticky='nsew', padx=padding, pady=padding)
        
        self.windowFrame.grid_columnconfigure(0, weight=1)
        self.windowFrame.grid_columnconfigure(1, weight=1)
        
        self.gridHandler = GridHandler()
        self.frameData = {}
    
    def _getOptions(self, **options):
        """Separates grid options from widget-specific options."""
        grid_options = {}
        widget_options = {}
        for key, value in options.items():
            if key in self._gridKeys:
                grid_options[key] = value
            else:
                widget_options[key] = value
        return grid_options, widget_options

    def _createFrame(self, parent, **options):
        grid_options, widget_options = self._getOptions(**options)
        frame = ctk.CTkFrame(parent, **widget_options)
        if grid_options:
            frame.grid(**grid_options)
        return frame

    def createButton(self, parent, **options):
        grid_options, widget_options = self._getOptions(**options)
        button = ctk.CTkButton(parent, corner_radius=8, **widget_options)
        button.grid(**grid_options)
        return button

    def createLabel(self, parent, **options):
        grid_options, widget_options = self._getOptions(**options)
        label = ctk.CTkLabel(parent, **widget_options)
        label.grid(**grid_options)
        return label

    def createEntry(self, parent, **options):
        grid_options, widget_options = self._getOptions(**options)
        entry = ctk.CTkEntry(parent, corner_radius=8, **widget_options)
        entry.grid(**grid_options)
        return entry

    def createTreeview(self, parent, **options):
        grid_options, widget_options = self._getOptions(**options)
        # ttk widgets don't accept grid options in constructor
        tree = ttk.Treeview(parent, **widget_options)
        for col in options.get('columns', ()):
            tree.heading(col, text=col.title())
        tree.grid(**grid_options)
        
        # Scrollbar setup
        vsb = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
        # Place scrollbar next to the treeview
        sb_row = grid_options.get('row', 0)
        sb_col = grid_options.get('column', 0) + 1
        sb_rowspan = grid_options.get('rowspan', 1)
        vsb.grid(row=sb_row, column=sb_col, sticky='ns', rowspan=sb_rowspan)
        tree.configure(yscrollcommand=vsb.set)
        return tree
        
    def createCombobox(self, parent, **options):
        grid_options, widget_options = self._getOptions(**options)
        combobox = ctk.CTkComboBox(parent, corner_radius=8, **widget_options)
        combobox.grid(**grid_options)
        return combobox
    
    def createSlider(self, parent, **options):
        grid_options, widget_options = self._getOptions(**options)
        slider = ctk.CTkSlider(parent, **widget_options)
        slider.grid(**grid_options)
        return slider
    
    
    def fixTreeview(self):
        """
        Applies custom styles for ttk.Treeview to match customtkinter's dark theme.
        """
        style = tk.ttk.Style(self.window)

        treeview_bg_color = "#1F1F1F" 
        treeview_fg_color = self.window._apply_appearance_mode(ctk.ThemeManager.theme["CTkLabel"]["text_color"])
        accent_color = self.window._apply_appearance_mode(ctk.ThemeManager.theme["CTkButton"]["fg_color"])
        heading_and_selected_text_color = "white" 

        style.theme_use("default") 
        style.configure("Treeview",
                        background=treeview_bg_color,
                        foreground=treeview_fg_color,
                        fieldbackground=treeview_bg_color,
                        rowheight=28,
                        borderwidth=0,
                        relief="flat",
                        padding=5)
        style.configure("Treeview.Heading",
                        background=accent_color,
                        foreground=heading_and_selected_text_color,
                        font=('Segoe UI', 10, 'bold'),
                        borderwidth=0,
                        relief="flat",
                        padding=(5, 8))
        style.map("Treeview",
                  background=[('selected', accent_color)],
                  foreground=[('selected', heading_and_selected_text_color)])

        style.configure("Vertical.TScrollbar",
                        background=treeview_bg_color,
                        troughcolor=treeview_bg_color,
                        bordercolor=treeview_bg_color,
                        arrowcolor=treeview_fg_color)
        style.map("Vertical.TScrollbar",
                  background=[('active', accent_color)],
                  troughcolor=[('active', treeview_bg_color)])

class GridHandler:
    def __init__(self):
        self.rows = [0]
    
    def nextRow(self):
        self.rows.append(0)

    def getRow(self):
        return len(self.rows) - 1
    
    def getNextColumn(self, row=None):
        target_row = row if row is not None else self.getRow()
        while target_row >= len(self.rows):
            self.nextRow()
        
        col = self.rows[target_row]
        self.rows[target_row] += 1
        return col

class FrameWrapper:
    def __init__(self, guiApi, baseFrame, frameId):
        self.gui = guiApi
        self.gridHandler = GridHandler()
        guiApi.frameData[frameId] = self.gridHandler
        
        guiApi.gridHandler.nextRow()
        self.frame = guiApi._createFrame(baseFrame, fg_color=("#191919"), corner_radius=10,
                                         row=guiApi.gridHandler.getRow(), column=0, columnspan=2, 
                                         sticky="ew", padx=10, pady=10)
        self.frame.grid_columnconfigure(1, weight=1)

    def createCustomTextbox(self, text, textVar, next=False, show=None):
        if next: self.gridHandler.nextRow()
        row = self.gridHandler.getRow()
        label = self.gui.createLabel(self.frame, text=text, row=row, column=self.gridHandler.getNextColumn(row), sticky="w", padx=10, pady=5)
        entry = self.gui.createEntry(self.frame, textvariable=textVar, row=row, column=self.gridHandler.getNextColumn(row), sticky="ew", padx=10, pady=5, show=show)
        return (label, entry)

    def createLabel(self, text, sticky='w' or None, next=False):
        if next: self.gridHandler.nextRow()
        row = self.gridHandler.getRow()
        label = self.gui.createLabel(self.frame, text=text, row=row, column=self.gridHandler.getNextColumn(row), sticky=sticky, padx=10, pady=5)
        return label

    def createEntry(self, textVar, sticky='e' or None, next=False, show=None):
        if next: self.gridHandler.nextRow()
        row = self.gridHandler.getRow()
        entry = self.gui.createEntry(self.frame, textvariable=textVar, row=row, column=self.gridHandler.getNextColumn(row), sticky=sticky, padx=10, pady=5, show=show)
        return entry

    def createSlider(self, args, sticky='w' or None, next=False):
        if next: self.gridHandler.nextRow()
        row = self.gridHandler.getRow()
        col = self.gridHandler.getNextColumn(row)
        slider = self.gui.createSlider(self.frame, from_=args['min'], to=args['max'], number_of_steps=args['steps'], 
                                       variable=args['var'], command=args['function'], 
                                       row=row, column=col, sticky=sticky, padx=10, pady=5)
        if 'default' in args:
            slider.set(args['default'])
        return slider
    
    def createCombobox(self, args, sticky='ew' or None, next=False):
        if next: self.gridHandler.nextRow()
        row = self.gridHandler.getRow()
        col = self.gridHandler.getNextColumn(row)
        
        combobox = self.gui.createCombobox(self.frame, variable=args['var'], values=args['list'], state=args['state'],
                                           row=row, column=col, sticky=sticky, padx=10, pady=5)
        if 'default' in args:
            combobox.set(args['default'])
        return combobox
    
    def createButton(self, args, sticky='ew' or None, next=False):
        if next: self.gridHandler.nextRow()
        row = self.gridHandler.getRow()
        col = self.gridHandler.getNextColumn(row)
    
        button = self.gui.createButton(self.frame, text=args['text'], command=args['function'], state=args.get('state', 'normal'),
                                       row=row, column=col, sticky=sticky, padx=10, pady=5)
        return button
    
    def createTreeview(self, args, sticky='nsew' or None, next=False):
        if next: self.gridHandler.nextRow()
        row = self.gridHandler.getRow()
        col = self.gridHandler.getNextColumn(row)

        columns_tuple = tuple(args['columns'].keys())
        
        treeview = self.gui.createTreeview(self.frame, columns=columns_tuple, show='headings',
                                           row=row, column=col, rowspan=args['rowspan'], sticky=sticky, padx=10, pady=10)
        
        for title, width in args['columns'].items():
            treeview.column(title, width=width, anchor=tk.W)
        return treeview