# -*- coding: utf-8 -*-

import sys
import os
import os.path
import re
import ConfigParser
from jinja2 import Environment, PackageLoader
from models import *

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
    mins  = secs // 60
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
        sections = meta.sections()
        for album in sections:
            metafiles[album] = meta

def merge_scans(albums, scans):
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

def generate_albuminfo(albums, metafiles, directory):
    filepath = os.path.join(directory, ".albuminfo")
    album_index = ConfigParser.RawConfigParser()
    album_index.read(filepath)
    for album in albums:
        if album not in metafiles:
            sys.stdout.write("++ {0}\n".format(album))
            ripper = raw_input("Ripper: ")
            catalog_no = raw_input("Catalog #: ")
            album_art = raw_input("Album art URL: ")
            try:
                album_index.add_section(album)
                album_index.set(album, "ripper", ripper)
                album_index.set(album, "catalog_no", catalog_no)
                album_index.set(album, "album_art", album_art)
            except DuplicateSectionError:
                # We've got 2 albums with the same name...
                sys.stderr.write("Duplicate album names")
    try:
        fp = open(filepath, "rw+")
        album_index.write(fp)
        fp.close()
        add_metafile(directory, ".albuminfo", metafiles)
    except:
        sys.stderr.write("Unable to write to {0}".format(filepath))

def generate_albums(directory, options):
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
                try:
                    add_track(Track(os.path.join(branch, filename)), albums)
                except TypeError:
                    pass ## Fail silently

    if options.album_info:
        generate_albuminfo(albums, metafiles, directory)

    merge_metafiles(albums, metafiles)
    merge_scans(albums, scans)

    return albums

def render_source(template, albums):
    root_node = albums.values()
    root_node.sort(natural_sort)
    for album in root_node:
        album.tidy()

    env = Environment(loader=PackageLoader("bxt_description_generator", "templates"))
    env.filters["cleanify"] = cleanify
    env.filters["pretty_time"] = pretty_time
    template = env.get_template(template)
    source = template.render(albums=root_node).encode("utf-8")

    return source

def generate_source(template, directory, options):
    return render_source(template, generate_albums(directory, options))

