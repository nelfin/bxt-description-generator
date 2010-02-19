# -*- coding: utf-8 -*-

import os
import os.path
import re as _re

# extensions we associate with scans
imageFileExtensions  = ['jpg','jpeg','png','tiff',]
# extensions we know we don't want to deal with
ignoreFileExtensions = ['mood','sfv','txt','nfo','m3u','ini','lnk','md5',
                        'db','desktop','!ut',]

def deduce_name(path):
    """ Deduce a file/directory name from a path """
    head, tail = os.path.split(path)
    return tail if tail else head

def deduce_discnumber(path):
    """ Deduce a disc number from file naming """
    return 1

def lazy_alphabetic(t):
    """ Case insensitive (simplified) dictionary order sort """
    t = t.upper()
    t = t.strip()
    if t.startswith("THE "):
        t = t[4:]
    t = t.replace("&","AND")
    t = _re.sub("[^A-Z0-9 ]"," ",t)
    t = _re.sub("\s{2,}"," ",t)
    t = t.strip()
    return t
    
# Comparisons
def natural_sort(x, y):
    return cmp(lazy_alphabetic(x.name), lazy_alphabetic(y.name))

def track_sort(x, y):
    return cmp(x.tracknumber, y.tracknumber)

def coerce_to_number(x):
    # Try for natural order first, i.e 1,2,3,...
    # vs string order 1,10,11
    try:
        x = int(x.split("/")[0])
    except Exception:
        pass
    return x

# Signals
class ImageFileException(Exception):
    pass

class UnknownFileException(Exception):
    pass

class Album:
    """
    Abstract representation of an album.
    
    name: album name
    artists: list of contributing artists
    ripper: album ripper
    catalog_no: album catalog number
    discs: dictionary of contained Discs
    scans: list of contained scan filenames
    length: total length of Tracks in seconds
    size: total size of Tracks in bytes
    average_bitrate: average bitrate of contained Tracks in kbit/s
    dates: list of dates
    extensions: list of Track file extensions
    album_art: href of album art
    """
    def __init__(self, name):
        self.name = name
        self.ripper = "unknown"
        self.artists = []
        self.catalog_no = "PCCG-70036"
        self.discs = {}
        self.scans = []
        self.length = 0
        self.size = 0
        self.average_bitrate = None
        self.extensions = []
        self.dates = []
        self.album_art = "http://phy-img4.imageshack.us/img4/3372/osto.jpg"
    def attach_disc(self, disc):
        self.discs[disc.number] = disc
    def attach_scans(self, scans):
        self.scans.extend(scans)
    def attach_track(self, track):
        if not track.discnumber:
            track.discnumber = deduce_discnumber(track.path)
        if track.discnumber not in self.discs:
            self.attach_disc(Disc(track.discnumber))
        self.discs[track.discnumber].attach_track(track)
    def tidy(self):
        for disc in self:
            disc.tidy()
            self.length += disc.length
            self.size += disc.size
            disc.tracklist.sort(track_sort)
            b_aggregate = 0; b_count = 0
            for track in disc.tracklist:
                if track.bitrate:
                    b_aggregate += track.bitrate; b_count += 1
                if track.artist and track.artist not in self.artists:
                    self.artists.append(track.artist)
                if track.extension and track.extension not in self.extensions:
                    self.extensions.append(track.extension)
                if track.date and track.date not in self.dates:
                    self.dates.append(track.date)
        self.artists.sort()
        self.extensions.sort()
        self.dates.sort()
    def __iter__(self):
        return iter(self.discs.values())

class Disc:
    """
    Abstract representation of a disc
    number: disc number
    name: disc name
    tracklist: list of child Tracks
    length: total length of child tracks in seconds
    size: total size of child tracks in bytes
    """
    def __init__(self, number, name = None):
        self.number = number
        self.name = name
        self.tracklist = []
    def attach_track(self, track):
        self.tracklist.append(track)
    def tidy(self):
        self.length = 0
        self.size = 0
        for track in self:
            self.length += track.length
            self.size += track.size
    def __iter__(self):
        return iter(self.tracklist)

class Track:
    """
    Abstract representation of a track (essentially a file).
    name: filename
    path: full path
    size: size of file in bytes
    length: length of track in seconds
    bitrate: bitrate of track in kbit/s
    artist: contributing artist
    album: album name
    title: track title
    tracknumber: track number
    discnumber: disc number
    date: supplied year/date of release
    """
    def __init__(self, path):
        self.path = path
        try:
            import mutagen
            _latermutagen = mutagen.version >= (1, 18)
            if _latermutagen:
                tags = mutagen.File(self.path, easy=True)
            else:
                tags = mutagen.File(self.path)
        except Exception as e:
            tags = None
            import sys
            sys.stderr.write("\"{0}\" appears to be malformed! Caught: {1!r}\n".format(self.path, e))
        if not tags: # Bail out early
            import sys
            sys.stderr.write("I don't know what to do with \"{0}\"!\n".format(self.path))
            raise TypeError
        self.name = deduce_name(path)
        self.size = os.path.getsize(self.path)
        self.extension = os.path.splitext(self.name)[1][1:]
        self.bitrate = 0; self.length = 0
        try:
            self.length  = tags.info.length
            self.bitrate = tags.info.bitrate / 1000
        except (AttributeError, ValueError, TypeError):
            pass
        if tags.__class__ == mutagen.mp3.MP3:
            import mutagen.easyid3
            tags = mutagen.easyid3.EasyID3(self.path)
        for prop in ["title", "artist", "album", "tracknumber", "discnumber", "date"]:
            if prop in tags:
                setattr(self, prop, tags[prop][0])
            else:
                setattr(self, prop, None)
        if not self.title:
            self.title  = self.name.rsplit('.', 1)[0].decode("utf-8") # Everything but the extension
        
        self.tracknumber = coerce_to_number(self.tracknumber)
        self.discnumber = coerce_to_number(self.discnumber)
        self.date = coerce_to_number(self.date)

    def __str__(self):
        return self.title if self.title else self.name
