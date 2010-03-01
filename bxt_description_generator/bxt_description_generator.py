#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This software is licensed under version 2.0 of the WTFPL (see COPYING for details)
"""

import sys
import os
import os.path
import re
import ConfigParser
from models import *
from jinja2 import Environment, PackageLoader
from optparse import OptionParser
try:
    import imp
    imp.reload(sys)
except ImportError:
    reload(sys)

sys.setdefaultencoding("utf-8")

def absolute_path(path):
    """ Get the absolute path of a file, from this script """
    root = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(root,path)

def cleanify(name):
    """ Strip out some things that don't play well in element ids """
    return re.sub(r"\W","_", name)

def pretty_time(secs, format = "{h:01.0f}:{m:02.0f}:{s:02.0f}"):
    """ Format a time according to a supplied format string """
    hours = secs // 3600
    secs -= 3600 * hours
    mins = secs // 60
    secs -= 60 * mins
    return format.format(h = hours, m = mins, s = secs)

def add_track(track, albums):
    if track.album:
        if track.album not in albums:
            albums[track.album] = Album(track.album)
        albums[track.album].attach_track(track)

def add_scan(path, scan, scans):
    guess = os.path.split(path)[1]
    if guess not in scans:
        scans[guess] = []
    scans[guess].append(os.path.join(path, scan))

def add_metafile(path, file, metafiles):
    full_path = os.path.join(path, file)
    meta = ConfigParser.RawConfigParser()
    if meta.read(full_path):
        album = meta.sections()[0]
        metafiles[album] = meta

def merge_scans(albums, scans):
    for album in albums:
        if album.name in scans:
            album.attach_scans(scans[album.name])

def merge_scans2(albums, scans):
    for seq in scans.values():
        for path in seq:
            bits = path.split(os.sep)
            name = bits.pop()
            for bit in reversed(bits):
                if bit in albums:
                    albums[bit].attach_scans([name])
                    break

def merge_metafiles(albums, metafiles):
    for name, item in metafiles.items():
        name = unicode(name)
        if name in albums:
            albums[name].attach_metafile(item)

# are we running this standalone, rather than as a module?
def main():
    global parser
    (options, args) = parser.parse_args()
    # Check to see if we have all the information we need
    try:
        directory = args[0]
        template = args[1]
    except IndexError:
        try:
            import easygui
            # get directory from user
            while not directory:
                directory = easygui.diropenbox("Where are the files?")
            # get template from user
            while not template:
                template = easygui.choicebox(
                    "What template do you want?",
                    choices=os.listdir(absolute_path("templates")))
        except ImportError:
            sys.stderr.write("Usage: " + sys.argv[0] + " <directory> <template>\n")
            return 1
    
    scans = {}
    albums = {}
    metafiles = {}
    for branch, dirs, files in os.walk(directory):
        for filename in files:
            if filename == ".albuminfo":
                add_metafile(branch, filename, metafiles)
                continue
            extension = os.path.splitext(filename)[1][1:]
            if extension in ignoreFileExtensions:
                continue
            elif extension in imageFileExtensions:
                add_scan(branch, filename, scans)
            else:
                add_track(Track(os.path.join(branch, filename)), albums)

    merge_metafiles(albums, metafiles)
    merge_scans2(albums, scans)
    
    root_node = albums.values()
    root_node.sort(natural_sort)
    #merge_scans(root_node, scans)
    for album in root_node:
        album.tidy()
    
    env = Environment(loader=PackageLoader("bxt_description_generator", "templates"))
    env.filters["cleanify"] = cleanify
    env.filters["pretty_time"] = pretty_time
    template = env.get_template(template)
    output = template.render(albums=root_node).encode("utf-8")

    if options.outfile:
        try:
            f = open(options.outfile,"wb")
            f.write(output)
            f.close()
        except IOError:
            sys.stderr.write("Unable to write to {0}".format(options.outfile))
            return 1
    else:
        try:
            easygui.codebox(text=output)
        except NameError:
            sys.stdout.write(output)
    return 0

if __name__ == "__main__":
    usage = "Usage: %prog <directory> [<template>] [options]"
    parser = OptionParser(usage)
    parser.add_option("-o","--outfile",dest="outfile",default=None,
                      help="output filename",metavar="FILE")
    sys.exit(main())
