#!/usr/bin/env python3
"""GtkJsonView

A simple JSON viewer written in GTK.

Author: mattn
URL: https://github.com/mattn/gtkjsonviewer

Classes
-------

JSONViewerWindow()
    The window.

JSONTreeStore()
    A store that can be used with JSONTreeView. Derived from Gtk.TreeStore.

JSONTreeView()
    A widget for displaying JSON. Derived from Gtk.TreeView.


Functions
---------

to_jq(path, data)
    Return the JSON query given a path.
"""

import numbers
import json
import re
import sys
import gi

gi.require_version('Adw', '1')
gi.require_version("Gtk", "4.0")
from gi.repository import Adw, Gtk, Gdk, Gio

# Key/property names which match this regex syntax may appear in a
# JSON path in their original unquoted form in dotted notation.
# Otherwise they must use the quoted-bracked notation.
jsonpath_unquoted_property_regex = re.compile(r"^[a-zA-Z][a-zA-Z0-9_]*$")

def to_jq(path, data) -> str:
    """Return the JSON query given a path."""
    indices = path.get_indices()
    jq = ""
    is_array_index = False

    # the expression must begins with identity `.`
    # if the first element is not a dict, add a dot
    if not isinstance(data, dict):
        jq += "."

    for index in indices:
        if isinstance(data, dict):
            key = list(sorted(data))[index]
            if len(key) == 0 or not jsonpath_unquoted_property_regex.match(key):
                jq += "['{}']".format(key)  # bracket notation (no initial dot)
            else:
                jq += "." + key  # dotted notation
            data = data[key]
            if isinstance(data, list):
                jq += "[]"
                is_array_index = True
        elif isinstance(data, list):
            if is_array_index:
                selected_index = index
                jq = jq[:-2]  # remove []
                jq += "[{}]".format(selected_index)
                data = data[selected_index]
                is_array_index = False
            else:
                jq += "[]"
                is_array_index = True

    return jq


class JSONTreeStore(Gtk.TreeStore):
    """A tree-like data structure that can be used with the JSONTreeView."""

    def __init__(self):
        super().__init__(str)
        is_dark = Gtk.Settings.get_default().get_property(
            "gtk-application-prefer-dark-theme"
        )
        if is_dark:
            self.color_array = "#f9f06b"  # Yellow
            self.color_type = "#ffbe6f"  # Orange
            self.color_string = "#dc8add"  # Purple
            self.color_number = "#f66151"  # Red
            self.color_object = "#99c1f1"  # Blue
            self.color_key = "#8ff0a4"  # Green
        else:
            self.color_array = "#e5a50a"  # Yellow
            self.color_type = "#c64600"  # Orange
            self.color_string = "#613583"  # Purple
            self.color_number = "#a51d2d"  # Red
            self.color_object = "#1a5fb4"  # Blue
            self.color_key = "#26a269"  # Green

    def walk_tree(self, data, parent=None) -> None:
        if isinstance(data, list):
            self._add_item(None, data, parent)
        elif isinstance(data, dict):
            for key in sorted(data):
                self._add_item(key, data[key], parent)
        else:
            self._add_item(None, data, parent)

    def _add_item(self, key, data, parent=None):
        if isinstance(data, dict):
            if key is not None:
                obj = self.append(
                    parent,
                    [
                        self._format_item(
                            self.color_object, self.color_type, str(key), "{}"
                        )
                    ],
                )
                self.walk_tree(data, obj)
            else:
                self.walk_tree(data, parent)
        elif isinstance(data, list):
            item = self._format_item(
                self.color_array, self.color_number, key, str(len(data))
            )
            arr = self.append(parent, [item])
            for index in range(0, len(data)):
                item = '<b><span foreground="{}">[</span></b><span foreground="{}">{}</span><b><span foreground="{}">]</span></b>'.format(
                    self.color_type, self.color_number, str(index), self.color_type
                )
                self._add_item(None, data[index], self.append(arr, [item]))
        elif isinstance(data, str):
            if len(data) > 256:
                data = data[0:255] + " <i>…</i> "
                if key is not None:
                    item = self._format_item(
                        self.color_key, self.color_string, key, f'"{data}"'
                    )
                    self.append(parent, [item])
                else:
                    item = self._span(self.color_string, data)
                    self.append(parent, [item])
            else:
                if key is not None:
                    item = self._format_item(
                        self.color_key, self.color_string, key, f'"{data}"'
                    )
                    self.append(parent, [item])
                else:
                    item = self._span(self.color_string, data)
                    self.append(parent, [item])

        elif isinstance(data, numbers.Real):
            item = self._format_item(self.color_key, self.color_number, key, str(data))
            self.append(parent, [item])
        elif data is None:
            item = '<span foreground="{}">{}</span> <span foreground="{}"><i>{}</i></span>'.format(
                self.color_key, key, self.color_type, "null"
            )
            self.append(parent, [item])
        else:
            print(
                "Warning: do not know how to format {} of type {}".format(str(data)),
                data.__class__.__name__,
            )
            self.append(parent, [repr(data)])

    def _format_item(self, color_key, color_value, key, value):
        if key is None:
            return '<span foreground="{}">[…]</span> <span foreground="{}">{}</span>'.format(
                color_key, color_value, value
            )
        return '<span foreground="{}">"{}"</span>: <span foreground="{}">{}</span>'.format(
            color_key, key, color_value, value
        )

    def _span(self, color, value):
        return '<span foreground="{}">"{}"</span>'.format(color, value)


class JSONTreeView(Gtk.TreeView):
    """A widget for displaying JSON.

    Args:
      title -- The column title."""

    def __init__(self, title=None):
        super().__init__()
        cell = Gtk.CellRendererText()
        self.column = Gtk.TreeViewColumn(title, cell, markup=0)
        self.append_column(self.column)

    def set_title(self, title: str) -> None:
        """Set the column title."""
        self.column.set_title(title)


class JSONViewerWindow(Gtk.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_default_size(600, 400)

        self.label_info = Gtk.Label()
        self.label_info.set_selectable(True)

        self.data = None

        raw_data = ""
        from_stdin = not (sys.stdin.isatty())

        if len(sys.argv) == 2:
            raw_data = open(sys.argv[1]).read().strip()
        elif from_stdin:
            raw_data = sys.stdin.read().strip()

        if raw_data and raw_data[0] == "(" and raw_data[-1] == ")":
            raw_data = raw_data[1:-1]

        column_title = ""

        if raw_data:
            try:
                self.parse_json(raw_data)
            except Exception as e:
                self.label_info.set_text(str(e))

            if from_stdin:
                column_title = "<input stream>"
            else:
                column_title = sys.argv[1]

        else:
            self.label_info.set_text("No data loaded")

        open_button = Gtk.Button()
        open_button.set_label('_Open')
        open_button.set_tooltip_text('Open a JSON file')
        open_button.set_use_underline(True)
        open_button.connect('clicked', self.open_callback)
        
        header = Gtk.HeaderBar()
        header.set_show_title_buttons(True)
        header.pack_start(open_button)
        self.set_titlebar(header)

        self.model = JSONTreeStore()
        swintree = Gtk.ScrolledWindow()
        swintree.set_vexpand(True)
        swinpath = Gtk.ScrolledWindow()
        self.treeview = JSONTreeView(column_title)
        self.treeview.set_model(self.model)

        gesture = Gtk.GestureClick.new()
        gesture.connect("pressed", self.on_treeview_button_press_event)
        gesture.set_button(Gdk.BUTTON_SECONDARY)
        self.treeview.add_controller(gesture)

        tree_selection = self.treeview.get_selection()
        tree_selection.connect("changed", self.on_selection_changed)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.append(swintree)
        box.append(swinpath)
        swintree.set_child(self.treeview)
        swinpath.set_child(self.label_info)
        self.set_child(box)

        if self.data:
            self.model.walk_tree(self.data)

    def copy_path_to_clipboard(self, action, param):
        tree_selection = self.treeview.get_selection()
        jq = self._tree_selection_to_jq(tree_selection)
        clipboard = Gdk.Display.get_clipboard(Gdk.Display.get_default())
        clipboard.set_content(Gdk.ContentProvider.new_for_value(jq))

    def parse_json(self, data):
        self.data = json.loads(data)

    def open_callback(self, action):
        filefilter = Gtk.FileFilter()
        filefilter.add_suffix("json")
        dialog = Gtk.FileChooserDialog(
            title="Select a JSON file",
            action=Gtk.FileChooserAction.OPEN,
            transient_for=self
        )
        dialog.add_buttons(
            '_Cancel',
            Gtk.ResponseType.CANCEL,
            '_Open',
            Gtk.ResponseType.ACCEPT,
        )
        dialog.set_filter(filefilter)
        dialog.connect("response", self.open_response_cb)
        dialog.present()

    def open_response_cb(self, dialog, response_id):
        if response_id == Gtk.ResponseType.ACCEPT:
            try:
                file = dialog.get_file()
                [success, content, etags] = file.load_contents(None)
                if success:
                    self.parse_json(content.decode("utf-8"))
                    self.model.clear()
                    self.model.walk_tree(self.data)
                    self.label_info.set_text("")
                    self.treeview.set_title(dialog.get_file().get_path())
                    dialog.destroy()
                else:
                    raise ValueError("Error while opening " + dialog.get_file().get_path())
            except Exception as e:
                self.label_info.set_text(str(e))
        else:
            dialog.destroy()

    def on_selection_changed(self, tree_selection):
        jq = self._tree_selection_to_jq(tree_selection)
        self.label_info.set_text(jq)

    def on_treeview_button_press_event(self, event, clicks, x, y):
        pathinfo = self.treeview.get_path_at_pos(x, y)

        if pathinfo is not None:
            path, col, cellx, celly = pathinfo
            self.treeview.grab_focus()
            self.treeview.set_cursor(path, col, 0)

            menu = Gio.Menu.new()
            action = Gio.SimpleAction.new("copy-path", None)
            action.connect("activate", self.copy_path_to_clipboard)
            self.add_action(action)
            menu.append("Copy Path to Clipboard", "win.copy-path")

            rect = Gdk.Rectangle()
            rect.x = x
            rect.y = y

            context_menu = Gtk.PopoverMenu()
            context_menu.set_has_arrow(False)
            context_menu.set_menu_model(menu)
            context_menu.set_parent(self.treeview)
            context_menu.set_pointing_to(rect)
            context_menu.popup()

    def _tree_selection_to_jq(self, tree_selection):
        (model, iter_current) = tree_selection.get_selected()
        jq = ""
        if iter_current:
            path = model.get_path(iter_current)
            jq = to_jq(path, self.data)
        return jq

def on_activate(app):
    win = JSONViewerWindow(application=app, title="JSON Viewer")
    win.present()


if __name__ == "__main__":
    app = Adw.Application()
    app.connect('activate', on_activate)
    app.run(None)
