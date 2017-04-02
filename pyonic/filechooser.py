
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import Screen
from kivy.uix.recycleview import RecycleView
from kivy.uix.behaviors import ButtonBehavior
from kivy.properties import (StringProperty, OptionProperty,
                             BooleanProperty, NumericProperty,
                             ObjectProperty)
from kivy.lang import Builder
from kivy import platform

import os
from os.path import (isdir, join, abspath, split, expanduser)

Builder.load_file('filechooser.kv')

class FileLabel(ButtonBehavior, BoxLayout):
    file_type = OptionProperty('file', options=('folder', 'file'))
    filename = StringProperty()
    shade = BooleanProperty(False)
    selected = BooleanProperty(False)
    
    @property
    def recycleview(self):
        return self.parent.parent

    def on_release(self):
        selected = not self.selected
        if selected:
            self.recycleview.select(self)
            if self.file_type == 'folder':
                self.recycleview.folder = abspath(
                    join(self.recycleview.folder, self.filename))
        else:
            self.recycleview.select(None)
        self.selected = selected

    def on_selected(self, instance, value):
        if self.file_type == 'folder':
            self.selected = False

class FileView(RecycleView):
    folder = StringProperty(abspath('.'))
    python_only = BooleanProperty(False)
    selection_instance = ObjectProperty(allownone=True)
    selection_filename = StringProperty()


    def __init__(self, *args, **kwargs):
        super(FileView, self).__init__(*args, **kwargs)
        self.on_folder(self, self.folder)

    def on_python_only(self, instance, value):
        self.on_folder(self, self.folder)

    def on_folder(self, instance, value):
        filens = os.listdir(self.folder)
        filens.append('..')

        file_types = ['folder' if isdir(join(self.folder, filen)) else 'file' for filen in filens]

        filens = [filen + ('/' if file_type == 'folder' else '')
                  for filen, file_type in zip(filens, file_types)]

        files = zip(filens, file_types)

        if self.python_only:
            files = [filen for filen in files if filen[0].endswith('.py') or filen[1] == 'folder']
        files = sorted(files, key=lambda row: row[0].lower())
        files = sorted(files, key=lambda row: (row[1] != 'folder'))

        indices = range(len(files))

        files = [(filen[0], filen[1], index) for filen, index in zip(files, indices)]

        self.data = [{'filename': name,
                      'file_type': file_type,
                      'shade': index % 2}
                     for (name, file_type, index) in files]
        print('data is', self.data)

        self.reset_scroll()

    def select(self, widget):
        if self.selection_instance is not None:
            self.selection_instance.selected = False
        self.selection_instance = widget
        if widget is not None and widget.file_type == 'file':
            self.selection_filename = widget.filename
        else:
            self.selection_filename = ''

    def reset_scroll(self):
        self.scroll_y = 1

    def go_up_folder(self):
        self.select(None)
        self.folder = abspath(self.folder + '/..')

    def go_home(self):
        self.select(None)
        if platform == 'android':
            # TODO: use pyjnius to get external storage dir
            home = '/storage/emulated/0'
        else:
            home = expanduser('~')
        self.folder = home

    def reset(self, go_home=True):
        self.select(None)
        if go_home:
            self.go_home()
        self.scroll_y = 1


class PyonicFileChooser(BoxLayout):
    folder = StringProperty(abspath('.'))
    python_only = BooleanProperty(False)

    current_selection = ObjectProperty(allownone=True)

    open_method = ObjectProperty()
    # The open_method should accept a single filepath as an argument.

    def return_selection(self):
        if self.open_method is None:
            return
        self.open_method(join(self.folder, self.current_selection.filename))
        from kivy.app import App
        App.get_running_app().manager.go_back()

class FileChooserScreen(Screen):
    open_method = ObjectProperty()
    current_filename = StringProperty()

    def on_pre_enter(self):
        self.ids.pyonicfilechooser.ids.fileview.reset(go_home=False)
