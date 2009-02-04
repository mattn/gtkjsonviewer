#! /usr/bin/python
# -*- coding: utf-8 -*-
import sys
import os
import gtk
import simplejson

def add_item(key, data, model, parent = None):
  if isinstance(data, dict):
    walk_tree(data, model, parent)
  elif isinstance(data, list):
    arr = model.append(parent, [key + ' (array)'])
    for index in range(0, len(data)-1):
      add_item(index, data[index], model, model.append(arr, ['item:' + str(index)]))
  elif isinstance(data, unicode):
    if len(data) > 256:
      data = data[0:255] + "..."
    model.append(parent, [key + ' : ' + data])
  else:
    model.append(parent, [key + ' : ' + str(data)])

def walk_tree(data, model, parent = None):
  if isinstance(data, list):
    add_item('', data, model, parent)
  else:
    for key in data:
      add_item(key, data[key], model, parent)

win = gtk.Window()
win.connect('destroy', gtk.main_quit)
win.set_title('GtkJsonView')
win.set_default_size(600, 400)

swin = gtk.ScrolledWindow()
swin.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

model = gtk.TreeStore(str)
tree = gtk.TreeView(model)
tvcol = gtk.TreeViewColumn('JSON')
tree.append_column(tvcol)
cell = gtk.CellRendererText()
tvcol.pack_start(cell, True)
tvcol.add_attribute(cell, 'text', 0)
tree.show()

swin.add_with_viewport(tree)
win.add(swin)

win.show_all()

if len(sys.argv) == 2:
  data = open(sys.argv[1]).read().strip()
else:
  data = sys.stdin.read().strip()
if data[0] == '(' and data[-1] == ')':
  data = data[1:-1]
walk_tree(simplejson.loads(data), model)
gtk.main()
