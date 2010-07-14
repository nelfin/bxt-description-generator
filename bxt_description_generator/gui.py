# -*- coding: utf-8 -*-

import sys
import os
import os.path
from optparse import OptionParser
import tempfile
import webbrowser
try:
    import imp
    imp.reload(sys)
except ImportError:
    reload(sys)

import backend as bdg

try:
    import pygtk
    pygtk.require("2.0")
    import gtk
except (AssertionError, ImportError):
    sys.stderr.write("{0} requires PyGTK-2.0\n".format(sys.argv[0]))
    sys.exit(1)


class BDG_GUI:
    preview_path = None
    template = "sandbox2" ## FIXME

    def update_preview_cb(self, file_chooser, preview_pic, preview_lbl):
        filename = file_chooser.get_preview_filename()
        try:
            files = os.listdir(filename)
            preview_lbl.set_text("Path: {0}\nFiles: {1}".format(filename,len(files)))
            cover = os.path.join(filename, "cover.jpg") ## FIXME
            pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(cover, 128, 128)
            preview_pic.set_from_pixbuf(pixbuf)
        except:
            preview_pic.clear()
        return None

    def update_preview_button(self, filepath):
        self.preview_path = filepath
        self.files_btn_preview.set_sensitive(True)
        return None

    def btn_preview_clicked(self, widget, data=None):
        if not self.preview_path:
            self.files_btn_generate.emit("clicked")
        webbrowser.open_new_tab(self.preview_path)
        return None

    def start_generate_source(self, template, directory):
        global parser
        (options, args) = parser.parse_args()
        source = bdg.generate_source(template, directory, options)
        ## suffix = ".htm" for the sake of IE
        with tempfile.NamedTemporaryFile(delete=False,suffix=".htm") as f:
            f.write(source)
        self.update_source(source)
        self.update_preview_button(f.name)
        ## Some progressbar action maybe?

    def btn_generate_clicked(self, widget, data=None):
        directory = self.files_widget.get_filename()
        self.start_generate_source(self.template, directory)
        return None

    def update_source(self, source):
        self.source_tbf.set_text(source)
        return None

    def destroy(self, widget, data=None):
        gtk.main_quit()
        return None

    def __init__(self):
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.connect("destroy", self.destroy)
        self.window.set_border_width(10)

        self.table = gtk.Table(1,2,False)
        self.window.add(self.table)

        ### Left Box
        self.left_box = gtk.Notebook()
        self.left_box.set_tab_pos(gtk.POS_TOP)
        self.table.attach(self.left_box,0,1,0,1)
        self.left_box.show()

        self.files_frm = gtk.Frame("Files")
        self.files_frm.set_border_width(10)
        self.files_frm.set_size_request(700,800)
        self.files_frm.show()

        self.files_tbl = gtk.Table(3,2,False)
        self.files_frm.add(self.files_tbl)
        self.files_tbl.show()

        self.files_widget = gtk.FileChooserWidget(action=gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)
        self.files_tbl.attach(self.files_widget,0,2,1,2,xoptions=gtk.SHRINK|gtk.FILL|gtk.EXPAND,xpadding=10,ypadding=10)
        self.files_widget.set_size_request(500,500)
        self.files_widget.show()

        self.files_lbl = gtk.Label("Files")
        self.left_box.append_page(self.files_frm, self.files_lbl)

        ## Preview Pane
        self.preview_pic = gtk.Image()
        self.files_tbl.attach(self.preview_pic,0,1,0,1)
        self.preview_pic.set_size_request(128,128)
        self.preview_pic.show()

        self.preview_lbl = gtk.Label("")
        self.files_tbl.attach(self.preview_lbl,1,2,0,1)
        self.preview_lbl.set_size_request(400,128)
        self.preview_lbl.set_line_wrap(True)
        self.preview_lbl.show()
        ## End Preview Pane

        ## Button Box
        self.files_btn_box = gtk.HButtonBox()
        self.files_widget.set_extra_widget(self.files_btn_box)
        self.files_btn_box.set_size_request(400, 20)
        self.files_btn_box.set_layout(gtk.BUTTONBOX_END)
        self.files_btn_box.show()

        self.files_btn_generate = gtk.Button("Generate")
        self.files_btn_box.pack_start(self.files_btn_generate)
        self.files_btn_generate.show()

        self.files_btn_preview = gtk.Button("Preview")
        self.files_btn_preview.set_sensitive(False)
        self.files_btn_box.pack_end(self.files_btn_preview)
        self.files_btn_preview.show()
        ## End Button Box

        ### Right Box
        self.right_box = gtk.Notebook()
        self.right_box.set_tab_pos(gtk.POS_TOP)
        self.table.attach(self.right_box,1,2,0,1)
        self.right_box.show()

        self.source_vbx = gtk.VBox(False,0)
        self.source_vbx.set_border_width(10)
        self.source_vbx.set_size_request(700,700)
        self.source_vbx.show()

        self.source_win = gtk.ScrolledWindow()
        self.source_win.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.source_vbx.pack_start(self.source_win)
        self.source_win.show()

        self.source_tvw = gtk.TextView()
        self.source_tbf = self.source_tvw.get_buffer()
        self.source_win.add(self.source_tvw)
        self.source_tvw.set_editable(False)
        self.source_tvw.set_cursor_visible(False)
        self.source_tvw.show()

        self.source_lbl = gtk.Label("Source")
        self.right_box.append_page(self.source_vbx, self.source_lbl)
        ### End Right Box

        ###
        ## SIGNAL HANDLERS

        self.files_btn_generate.connect("clicked", self.btn_generate_clicked)
        self.files_btn_preview.connect("clicked", self.btn_preview_clicked)
        self.files_widget.connect("update-preview", self.update_preview_cb, self.preview_pic, self.preview_lbl)

        ### Finishing up
        self.table.show()
        self.window.show()
        return None

    def main(self):
        gtk.main()
        return 0

if __name__ == "__main__":
    usage = "Usage: %prog <directory> [<template>] [options]"
    parser = OptionParser(usage)
    parser.add_option("-o","--outfile",dest="outfile",default=None,
                      help="output filename",metavar="FILE")
    parser.add_option("-i","--album-info",dest="album_info",default=None,
                      help="interactively prompt for album meta-info",
                      action="store_true")
    parser.add_option("-c","--colour-scheme",dest="colour_scheme",default=None,
                      help="colour scheme filename",metavar="FILE")
    gui = BDG_GUI()
    exit(gui.main())

