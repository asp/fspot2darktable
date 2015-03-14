#!/usr/bin/python
# encoding: utf-8
#
# Copyright (C) 2012 Lars Michelsen <lm@larsmichelsen.com>,
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307,
#
# GNU General Public License: http://www.gnu.org/licenses/gpl-2.0.txt
#
# Report bugs to: lm@larsmichelsen.com
 
import os, sys, urllib2
 
fspot_db = '%s/.config/f-spot/photos.db' % os.getenv('HOME')
 
opt_verbose = '-v' in sys.argv or '--verbose' in sys.argv
opt_help    = '-h' in sys.argv or '--help' in sys.argv
 
def help():
    sys.stderr.write('''
 fspot2darktable
 
 This script helps migrating your photo library from F-Spot to Darktable.
 It extracts assigned tags from the F-Spot SQLite database and creates
 .xmp files for each image with the tag information. The script cares
 about and preserves the tag hierarchy structure.
 
 The script must be executed as user which F-Spot DB should be migrated.
 
 The script will query the SQLite database of F-Spot and extract all tags
 and hierarchical tag information from the database for images which do
 exist on your harddrive and do not have an associated xmp file yet. It
 will write those information in a basic xmp file.
 
 This script has been developed to be executed only once for a photo
 library. The cleanest way is to execute it before you import your images
 into Darktable. This way you can ensure all the new tags are really loaded
 correctly into Darktable.
 
 During development I removed the images again and again from the Darktable
 database and also removed all *.xmp files in my photo folders to have a
 clean start. After cleaning up those things I ran fspot2darktable, then
 started Darktable and imported all the fotos.
 
 After executing the script you can import single images or the whole
 photo library to Darktable. You should see your tag definitions in
 Darktable now.
 
 The script has been developed with
   - F-Spot 0.8.2
   - Darktable 1.0
 
 Please report bugs to <lm@larsmichelsen.com>.
''')
 
def err(s):
    sys.stderr.write('%s\n' % s)
    sys.exit(1)
 
def log(s):
    sys.stdout.write('%s\n' % s)
 
def verbose(s):
    if opt_verbose:
        sys.stdout.write('%s\n' % s)
 
if opt_help:
    help()
    sys.exit(3)
 
try:
    import sqlite3
except Exception, e:
    err('Unable to import sqlite3 module (%s)' % e)
 
if not os.path.exists(fspot_db):
    err('The F-Spot database at %s does not exist.' % fspot_db)
 
conn = sqlite3.connect(fspot_db)
cur  = conn.cursor()
 
# Loop all images, get all tags for each image
cur.execute('SELECT id, base_uri, filename FROM photos')
num_files = 0
num_not_existing = 0
num_xmp_existing = 0
num_created = 0
for id, base_uri, filename in cur:
    num_files += 1
    # F-Spot URLs are url encoded. Decode them here. There seem to be
    # some encoding mixups possible. Damn. Try simple utf-8 then latin-1
    # vs utf-8. This works for me but might not for others... let me know
    # if you got a better way solving this
    path = urllib2.unquote(base_uri.replace('file://', ''))
    try:
        path = path.decode('utf8')
    except UnicodeEncodeError:
        path = path.encode('latin-1').decode('utf-8')
    path += '/' + filename
    xmp_path = path + '.xmp'
 
    if not os.path.exists(path):
        verbose('Skipping non existant image (%s)' % path)
        num_not_existing += 1
        continue
 
    if os.path.exists(xmp_path):
        verbose('Skipping because of existing XMP file (%s)' % path)
        num_xmp_existing += 1
        continue
 
    # Walks the tag categories upwards to find all the parent tags to
    # build a list of parent tags. This will be used later to build
    # hierarchical tags in the XMP files instead simple tags
    def parent_tags(category_id):
        cur = conn.cursor()
        cur.execute(
            'SELECT id, name, is_category, category_id '
            'FROM tags WHERE id=\'%d\'' % category_id
        )
        tag_id, tag, is_category, category_id = cur.fetchone()
 
        parent_tags_list = []
        if category_id != 0:
            parent_tags_list += parent_tags(category_id)
 
        return parent_tags_list + [ tag ]
 
    hierarchical_tags = []
    simple_tags       = []
 
    cur2 = conn.cursor()
    cur2.execute(
        'SELECT tag_id, name, is_category, category_id '
        'FROM tags, photo_tags WHERE photo_id=\'%d\' AND id=tag_id' % id)
    for tag_id, tag, is_category, category_id in cur2:
        if category_id:
            hierarchical_tags.append('|'.join(parent_tags(category_id) + [ tag ]))
        else:
            simple_tags.append(tag)
 
    def xml_fmt(tags):
        return ''.join([ '      <rdf:li>%s</rdf:li>' % \
                        t.encode('utf-8') for t in tags ])
 
    # Now really create the xmp file
    file(xmp_path, 'w').write('''<?xpacket begin="<feff>" id="W5M0MpCehiHzreSzNTczkc9d"?>
<x:xmpmeta xmlns:x="adobe:ns:meta/" x:xmptk="XMP Core 4.4.0-Exiv2">
 <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
  <rdf:Description rdf:about=""
    xmlns:xmp="http://ns.adobe.com/xap/1.0/"
    xmlns:darktable="http://darktable.sf.net/"
    xmlns:lr="http://ns.adobe.com/lightroom/1.0/"
    xmlns:dc="http://purl.org/dc/elements/1.1/"
   xmp:Rating="1"
   darktable:xmp_version="1"
   darktable:raw_params="0">
   <darktable:colorlabels>
    <rdf:Seq/>
   </darktable:colorlabels>
   <darktable:history_modversion>
    <rdf:Bag/>
   </darktable:history_modversion>
   <darktable:history_enabled>
    <rdf:Bag/>
   </darktable:history_enabled>
   <darktable:history_operation>
    <rdf:Bag/>
   </darktable:history_operation>
   <darktable:history_params>
    <rdf:Bag/>
   </darktable:history_params>
   <darktable:blendop_params>
    <rdf:Bag/>
   </darktable:blendop_params>
   <lr:hierarchicalSubject>
    <rdf:Seq>
%s
    </rdf:Seq>
   </lr:hierarchicalSubject>
   <dc:subject>
    <rdf:Seq>
%s
    </rdf:Seq>
   </dc:subject>
  </rdf:Description>
 </rdf:RDF>
</x:xmpmeta>
<?xpacket end="w"?>''' % (xml_fmt(hierarchical_tags),
                          xml_fmt(simple_tags)))
 
    num_created += 1
 
log('FINISHED! - Summary:')
log(' %-10s images in total' % num_files)
log(' %-10s images do not exist' % num_not_existing)
log(' %-10s images already have xmp files' % num_xmp_existing)
log(' %-10s created xmp files' % num_created)
