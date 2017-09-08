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

color_array = 'yellow'
color_type = 'orange'
color_string = 'pink'
color_integer = 'red'
color_object = 'yellow'
color_key = 'light green'

def add_item(key, data, model, parent = None):
  if isinstance(data, dict):
    if len(key):
      obj = model.append(parent, ['<span foreground="'+color_object+'">'
                                  + str(key) + '</span>' +
                                  ' <span foreground="'+color_type+'"><b>{}</b></span>'])
      walk_tree(data, model, obj)
    else:
      walk_tree(data, model, parent)
  elif isinstance(data, list):
    arr = model.append(parent, ['<span foreground="'+color_array+'">'+ key + '</span> '
                                '<span foreground="'+color_type+'"><b>[]</b></span> ' +
                                '<span foreground="'+color_integer+'">' + str(len(data)) + '</span>'])
    for index in range(0, len(data)):
      add_item('', data[index], model, model.append(arr, ['<b><span foreground="'+color_type+'">'+'['+'</span></b><span foreground="'+color_integer+'">' + str(index) + '</span><b><span foreground="'+color_type+'">]</span></b>']))
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
                          '  <b>:</b> <span foreground="'+color_integer+'">' + str(data) + '</span>'])
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

#return the json query given a path
def to_jq(path, data):
  indices = path.get_indices()
  jq = ''
  is_array_index = False

  #the expression must begin with identity `.`
  #if the first element is not a dict, add a dot
  if not isinstance(data, dict):
    jq += '.'

  for indice in indices:
    if isinstance(data, dict):
      key = (list(data)[indice])
      jq += '.' + key
      data = data[key]
      if isinstance(data, list):
        jq += '[]'
        is_array_index = True
    elif isinstance(data, list):
      if is_array_index:
        selected_index = indice
        jq = jq[:-2]   #remove []
        jq += '[{}]'.format(selected_index)
        data = data[selected_index]
        is_array_index = False
      else:
        jq += '[]'
        is_array_index = True

  return jq

class JSONViewerWindow(Gtk.Window):
    def __init__(self):
      Gtk.Window.__init__(self, title="JSon Viewer")
      self.set_default_size(600, 400)

      self.label_path = Gtk.Label()
      self.label_path.set_selectable(True)

      self.data = None

      try:
        self.data = json.loads(raw_data)
      except Exception as e:
        self.label_path.set_text("Input error:\n" + str(e))

      model = Gtk.TreeStore(str)
      swintree = Gtk.ScrolledWindow()
      swinpath = Gtk.ScrolledWindow()
      tree = Gtk.TreeView(model)
      cell = Gtk.CellRendererText()
      tvcol = Gtk.TreeViewColumn('JSON', cell, markup=0)

      tree_selection = tree.get_selection()
      tree_selection.connect("changed", self.on_selection_changed)
      tree.append_column(tvcol)

      box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
      box.pack_start(swintree, True, True, 1)
      box.pack_start(swinpath, False, False, 1)
      swintree.add(tree)
      swinpath.add(self.label_path)
      self.add(box)

      if self.data:
        walk_tree(self.data, model)

    def on_selection_changed(self, tree_selection) :
      (model, iter_current) = tree_selection.get_selected()
      path = model.get_path(iter_current)
      jq = to_jq(path, self.data)
      jq_str = ''.join(jq)
      self.label_path.set_text(jq_str)

win = JSONViewerWindow()
win.connect("delete-event", Gtk.main_quit)
win.show_all()
Gtk.main()
