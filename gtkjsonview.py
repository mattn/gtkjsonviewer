import sys
import os
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
try:
  import json
except:
  import simplejson as json
  pass

if len(sys.argv) == 2:
  raw_data = open(sys.argv[1]).read().strip()
else:
  raw_data = sys.stdin.read().strip()
if raw_data[0] == '(' and raw_data[-1] == ')':
  raw_data = raw_data[1:-1]


color_type = 'blue'
color_string = 'pink'
color_integer = 'red'
color_object = 'yellow'
color_array = 'orange'
color_key = 'light green'

def add_item(key, data, model, parent = None):
  if isinstance(data, dict):
    if len(key):
      obj = model.append(parent, ['<span foreground="'+color_object+'">'
                                  + str(key) + '</span>' + ' <b>{}</b>'])
      walk_tree(data, model, obj)
    else:
      walk_tree(data, model, parent)
  elif isinstance(data, list):
    arr = model.append(parent, ['<span foreground="'+color_array+'">"' + key + '"</span>' +' <b>[]</b>'])
    for index in range(0, len(data)):
      add_item('', data[index], model, model.append(arr, ['<b>[</b>' + str(index) + '<b>]</b>']))
  elif isinstance(data, str):
    if len(data) > 256:
      data = data[0:255] + "..."
      model.append(parent, ['<span foreground="'+color_key+'">"' + key + '"</span>' +
                            '<b>:</b> <span foreground="'+color_string+'">"' + data + '"</span>'])
    else:
      model.append(parent, ['<span foreground="'+color_key+'">"' + key + '"</span>' +
                            '  <b>:</b> <span foreground="'+color_string+'">"' + data + '"</span>'])
  elif isinstance(data, int):
    model.append(parent, ['<span foreground="'+color_key+'">"' + key + '"</span>' +
                          '  <b>:</b> <span foreground="'+color_string+'">' + str(data) + '</span>'])
  else:
    model.append(parent, [str(data)])

def walk_tree(data, model, parent = None):
  if isinstance(data, list):
    add_item('', data, model, parent)
  elif isinstance(data, dict):
    for key in data:
      add_item(key, data[key], model, parent)
  else:
    add_item('', data, model, parent)

data = json.loads(raw_data)

class JSONViewerWindow(Gtk.Window):
    def __init__(self):
      Gtk.Window.__init__(self, title="JSon Viewer")
      self.set_default_size(600, 400)
      swin = Gtk.ScrolledWindow()
      model = Gtk.TreeStore(str)
      tree = Gtk.TreeView(model)
      cell = Gtk.CellRendererText()
      tvcol = Gtk.TreeViewColumn('JSON', cell, markup=0)
      tree.append_column(tvcol)
      swin.add(tree)
      self.add(swin)
      walk_tree(data, model)



win = JSONViewerWindow()
win.connect("delete-event", Gtk.main_quit)
win.show_all()
Gtk.main()
