#! /usr/bin/env python3
################################################################################
"""piki.cgi: Quick-quick implementation of WikiWikiWeb in Python """
__version__ = '$Revision: 2.1 $'[11:-2];
#
# Modified by Daniel C. Nygren
# 
# Copyright (C) 1999, 2000 Martin Pool <mbp@humbug.org.au>
# Copyright (C) 2019 Daniel C. Nygren <dan.nygren@gmail.com>
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 59 Temple
# Place, Suite 330, Boston, MA 02111-1307 USA
#
# INSTALLATION
#
#           For simplicity, all of the configurable settings for PikiPiki are
#           in this CGI script itself.  The installation procedure is:
#
# 1. Make sure you have a web server that will let you run CGIs.
#
# 2. Make sure Python 3.5.3 or greater is installed.
#    Check by typing "python --version" in a command window.
#  
# 3. Configure the script:
#
#   a) On Unix or Apache on Windows systems, set the very first line to refer
#   to the location of your Python program. For example:
#
#       i) for Unix #! /usr/local/bin/python3
#          or       #! /usr/bin/env python3
#
#       ii) for Apache on Windows #! c:/python/python3.exe
#
#       iii) for IIS on Windows see below
#        
#   b)  On IIS, ensure the CGI module is installed, and rename the script to
#   piki.py and associate .py with Python:
#
#        Install the CGI module on IIS:
#        Control Panel -> Programs -> Turn Windows features on and off
#        Internet Information Services -> World Wide Web Services ->
#        Application Development Features -> CGI
#
#        Add web application for Python: In IIS Manager, right click Default Web
#        Site -> Add Application, setting Alias e.g.: PythonApp, and make it
#        pointing to some folder like C:\netpub\wwwroot\CGI-BIN, then click OK
#
#        Double click the Default Web Site's Handler Mappings, right click to
#        Add Script Map.
#
#        In Request path, put "*.py" as the script files extension.
#        In Executable, select
#        For a Cygwin Installation:
#        "C:\cygwin\bin\python3.exe %s %s" or
#        "C:\cygwin64\bin\python3.exe %s %s"
#        For a Python Windows Installation "C:\Python3\python.exe %s %s" 
#        Give the script mapping an appropriate name, like "PythonHandler".
#        Click OK. 
#
#        Test locally on IIS with:
#        http://localhost/CGI-BIN/piki.py
#        http://127.0.0.1/CGI-BIN/piki.py
#
#   c) Set 'data_dir' to the directory that will hold the page files.
#      It is a serious security hole to put them in a directory containing
#      CGIs or other files.
#
#   d) Copy the default pages into data_dir/text.
#
#   e) Copy the CSS stylesheet piki.css to an appropriate directory on the
#      web server, and make css_url point to it.
#
#   f) Copy the icon pikipiki-logo.png to an appropriate directory on the 
#      web server, and make logo_string point to it.
#
# 4. Set permissions
#
#   There is more than one way of setting permissions depending upon how your
#   web server is configured. One method is to add a user (with a public_html
#   directory) to the apache www-data group and start apache with a umask of
#   002 so that files modified or created by apache can still be modified by
#   the user. In that case, directories and executable files should be 
#   chmod 770 (rwxrwx---), and other files 660 (rw-rw----).
#
# === Example ===
# $ pwd
# /etc/systemd/system/multi-user.target.wants
# 
# $ cat apache2.service
# [Unit]
# Description=The Apache HTTP Server
# After=network.target remote-fs.target nss-lookup.target
# 
# [Service]
# Type=forking
# Environment=APACHE_STARTED_BY_SYSTEMD=true
# ExecStart=/usr/sbin/apachectl start
# ExecStop=/usr/sbin/apachectl stop
# ExecReload=/usr/sbin/apachectl graceful
# PrivateTmp=true
# Restart=on-abort
# UMask=0117
# 
# [Install]
# WantedBy=multi-user.target
# 
# 
# $ sudo systemctl daemon-reload
# $ sudo systemctl restart apache2
# 
# $ pwd
# /home/nygren/public_html/index/Template/CGI-BIN/text
# 
# $ ls -la
# -rw-rw---- 1 www-data www-data   58 Dec 16 12:31 DanNygren
# 
# $ sudo usermod -a -G www-data nygren
# (Logout and back in or temporarily enter group with)
# $ newgrp www-data
#
#
# CALLING SEQUENCE piki.cgi needs to go to the CGI-BIN directory,
#                  or similar Windows directory 
#
# EXAMPLES      http://www.example.com/~dnygren/index/project/CGI-BIN/piki.cgi
#               http://dnygren-pc.example.com/CGI-BIN/piki.py
#
# TARGET SYSTEM         Python
#
# DEVELOPED ON      (Original) Python 2.7.3, Solaris 10, Windows 7 Professional 
#                   Python 3.5.3
#
# CALLS             (List of modules this routine calls)
#   ./piki.css 
#   ./editlog.txt
#   ./Images/pikipiki-logo.png
#   ./text/EditingTips
#   ./text/FindPage
#   ./text/FrontPage
#   ./text/PikiConventions
#   ./text/PikiPiki
#   ./text/PikiSandBox
#   ./text/RecentChanges
#   ./text/TitleIndex
#   ./text/WikiWords
#   ./text/WordIndex
# and all the unique Wiki pages created by the users.
#
# Python calls:

import cgi, sys, os, re, errno, time, stat
from cgi import log
from os import path, environ
from socket import gethostbyaddr
from time import localtime, strftime
from io import StringIO

#
# CALLED BY         Web server
#
# INPUTS            User data
#
# OUTPUTS           HTML web pages
#
# RETURNS           (Type and meaning of return value, if any)
#
# ERROR HANDLING    Redirect stderr to a file.
#                   'a'ppend errors to the error file.
#
# WARNINGS          (1. Describe anything a maintainer should be aware of)
#                   (2. Describe anything a maintainer should be aware of)
#                   (N. Describe anything a maintainer should be aware of)
#
################################################################################

# Start Configurable parts -----------------------------------------

# Comment out Windows or Unix section depending upon the operating system used.

## Unix
## Hardcode these values, or try to get locations depending upon the installation directory
#data_dir = '/home/dnygren/public_html/index/Template/CGI-BIN/'
data_dir = os.getcwd()
#logo_string = '<img src="/~dnygren/index/Template/CGI-BIN/Images/pikipiki-logo.png" border=0 title="pikipiki $Revision: 2.1 $">'
logo_string = '<img src="/~nygren/' + str.replace(data_dir, '/home/nygren/public_html/', '') + '/Images/pikipiki-logo.png" border=0 title="pikipiki $Revision: 2.1 $">'
# stylesheet link, or ''
#css_url = '/~dnygren/index/Template/CGI-BIN/piki.css'    # stylesheet link, or ''
css_url = '/~nygren/' + str.replace(data_dir, '/home/nygren/public_html/', '') + '/piki.css'

## Windows
#data_dir = 'c:/inetpub/wwwroot/CGI-BIN/'
#logo_string = '<img src="/CGI-BIN/Images/pikipiki-logo.png" border=0 title="pikipiki $Revision: 2.1 $">'
#css_url = '/CGI-BIN/piki.css'    # stylesheet link, or ''


# Shared
stderr_name = path.join(data_dir, 'pikipiki_stderr.txt')
sys.stderr = open(stderr_name, 'at')
text_dir = path.join(data_dir, 'text')
editlog_name = path.join(data_dir, 'editlog.txt')
changed_time_fmt = ' . . . . [%I:%M %p]'
date_fmt = '%a %d %b %Y'
datetime_fmt = '%a %d %b %Y %I:%M %p'
show_hosts = 0          # Show hostnames in RecentChanges page?
nonexist_qm = 0         # Set this to 1 to show a '?' for nonexistent links.
text_area_rows = 24     # Define editing area text rows
text_area_cols = 132    # Define editing area text columns
# End Configurable parts -------------------------------------------


# Regular expression defining a WikiWord
# (but this definition is also assumed in other places)
# The expression reads CamelCaseWord OR regular wiki words' with brackets stripped off"
word_re_str = r"(\b([A-Z][a-z]+){2,}\b)|([\w| |'|\-|_|\.|/]+)"


# Editlog ----------------------------------------------------------

# Functions to keep track of when people have changed pages, so we can
# do the recent changes page and so on.
# The editlog is stored with one record per line, as tab-separated
# words: page_name, host, time

# TODO: Check values written in are reasonable

def editlog_add(page_name, host):
    editlog = open(editlog_name, 'a+')
    try: 
        # fcntl.flock(editlog.fileno(), fcntl.LOCK_EX)
        editlog.seek(0, 2)                  # to end
        editlog.write('\t'.join((page_name, host, repr(time.time()), repr(time.strftime(datetime_fmt)))) + "\n")
    finally:
        # fcntl.flock(editlog.fileno(), fcntl.LOCK_UN)
        editlog.close()


def editlog_raw_lines():
    editlog = open(editlog_name, 'rt')
    try:
        # fcntl.flock(editlog.fileno(), fcntl.LOCK_SH)
        return editlog.readlines()
    finally:
        # fcntl.flock(editlog.fileno(), fcntl.LOCK_UN)
        editlog.close()


# Formatting stuff -------------------------------------------------

def get_scriptname():
    return environ.get('SCRIPT_NAME', '')


def send_title(text, link=None, msg=None):
    print("<head><title>%s</title>" % text)
    print('''<link rel="shortcut icon" href="favicon.ico" >''')
    if css_url:
        print('<link rel="stylesheet" type="text/css" href="%s">' % css_url)
    print("</head>")
    print('<body><h1>')
    if logo_string:
        print(link_tag('FrontPage', logo_string))
    if link:
        #print '<a href="%s">%s</a>' % (link, text)
        #Changed the above line to the below to make it easy to grab
        #the URL to a page from its title.
        print(link_tag(link, text))
    else:
        print(text)
    print('</h1>')
    if msg: print(msg)
    print('<hr>')



def link_tag(params, text=None, ss_class=None):
    if text is None:
        text = params                   # default
    if ss_class:
        classattr = 'class="%s" ' % ss_class
    else:
        classattr = ''
    return '<a %s href="%s/%s">%s</a>' % (classattr, get_scriptname(),
                                         params, text)


# Search ----------------------------------------------------------

def do_fullsearch(needle):
    send_title('Full text search for "%s"' % (needle))

    needle_re = re.compile(needle, re.IGNORECASE)
    hits = []
    all_pages = page_list()
    for page_name in all_pages:
        body = Page(page_name).get_raw_body()
        count = len(needle_re.findall(body))
        if count:
            hits.append((count, page_name))

    # The default comparison for tuples compares elements in order,
    # so this sorts by number of hits
    hits.sort()
    hits.reverse()

    print("<UL>")
    for (count, page_name) in hits:
        print('<LI>' + Page(page_name).link_to())
        print(' . . . . ' + repr(count))
        print(['match', 'matches'][count != 1])
    print("</UL>")

    print_search_stats(len(hits), len(all_pages))


def do_titlesearch(needle):
    # TODO: check needle is legal -- but probably we can just accept any
    # RE

    send_title("Title search for \"" + needle + '"')
    
    needle_re = re.compile(needle, re.IGNORECASE)
    all_pages = page_list()
    hits = list(filter(needle_re.search, all_pages))

    print("<UL>")
    for filename in hits:
        print('<LI>' + Page(filename).link_to())
    print("</UL>")

    print_search_stats(len(hits), len(all_pages))


def print_search_stats(hits, searched):
    print("<p>%d hits " % hits)
    print(" out of %d pages searched." % searched)


def do_edit(pagename):
    Page(pagename).send_editor()


def do_savepage(pagename):
    global form
    pg = Page(pagename)
    pg.save_text(form['savetext'].value)
    msg = """<b>Thank you for your changes.  Your attention to
    detail is appreciated.</b>"""
    
    pg.send_page(msg=msg)


def make_index_key():
    s = '<p><center>'
    links = ['<a href="#%s">%s</a>' % (ch, ch) for ch in str.lowercase]
    s = s + str.join(links, ' | ')
    s = s + '</center><p>'
    return s


def page_list():
    return os.listdir(text_dir)


def print_footer(name, editable=1, mod_string=None):
    base = get_scriptname()
    print('<hr>')
    if editable:
        print(link_tag('?edit='+name, 'EditText'))
        print("of this page")
        if mod_string:
            print("(last modified %s)" % mod_string)
        print('<br>')
    print(link_tag('FindPage', 'FindPage'))
    print(" by browsing, searching, or an index")
    print('<br>')
    print(" Or return to the ")
    print(link_tag('FrontPage'))


# Macros -----------------------------------------------------------

def _macro_TitleSearch():
    return _macro_search("titlesearch")

def _macro_FullSearch():
    return _macro_search("fullsearch")

def _macro_search(type):
    if 'value' in form:
        default = form["value"].value
    else:
        default = ''
    return """<form method=get>
    <input name=%s size=30 value="%s"> 
    <input type=submit value="Go">
    </form>""" % (type, default)

def _macro_GoTo():
    return """<form method=get><input name=goto size=30>
    <input type=submit value="Go">
    </form>"""
    # isindex is deprecated, but it gives the right result here

def _macro_WordIndex():
    s = make_index_key()
    pages = list(page_list())
    map = {}
    #word_re = re.compile('[A-Z][a-z]+')
    #word_re = re.compile('[A-Z][a-z]+|[\w| |'')
    word_re = re.compile('[A-Z][a-z]+|[\w| |\'|\-|_|\.]+')
    for name in pages:
        for word in word_re.findall(name):
            try:
                map[word].append(name)
            except KeyError:
                map[word] = [name]

    all_words = list(map.keys())
    all_words.sort()
    last_letter = None
    for word in all_words:
        letter = str.lower(word[0])
        if letter != last_letter:
            s = s + '<a name="%s"><h3>%s</h3></a>' % (letter, letter)
            last_letter = letter
            
        s = s + '<b>%s</b><ul>' % word
        links = map[word]
        links.sort()
        last_page = None
        for name in links:
            if name == last_page: continue
            s = s + '<li>' + Page(name).link_to()
        s = s + '</ul>'
    return s


def _macro_TitleIndex():
    s = make_index_key()
    pages = list(page_list())
    pages.sort()
    current_letter = None
    for name in pages:
        letter = str.lower(name[0])
        if letter != current_letter:
            s = s + '<a name="%s"><h3>%s</h3></a>' % (letter, letter)
            current_letter = letter
        else:
            s = s + '<br>'
        s = s + Page(name).link_to()
    return s


def _macro_RecentChanges():
    lines = editlog_raw_lines()
    lines.reverse()

    ratchet_day = None
    done_words = {}
    buf = StringIO()
    for line in lines:
        page_name, addr, ed_time, readable_time = str.split(line, '\t')
        # year, month, day, DoW
        time_tuple = localtime(float(ed_time))
        day = tuple(time_tuple[0:3])
        if day != ratchet_day:
            buf.write('<h3>%s</h3>' % strftime(date_fmt, time_tuple))
            ratchet_day = day

        if page_name in done_words:
            continue

        done_words[page_name] = 1
        buf.write(Page(page_name).link_to())
        if show_hosts:
            buf.write(' . . . . ')
            try:
                buf.write(gethostbyaddr(addr)[0])
            except:
                buf.write("(unknown)")
        if changed_time_fmt:
            buf.write(time.strftime(changed_time_fmt, time_tuple))
        buf.write('<br>')

    return buf.getvalue()



# Pageformatter ---------------------------------------------------
class PageFormatter:
    """Object that turns Wiki markup into HTML.

    All formatting commands can be parsed one line at a time, though
    some state is carried over between lines.
    """
    def __init__(self, raw):
        self.raw = raw
        self.is_em = self.is_b = self.is_bold = self.is_ital = 0
        self.in_table = self.in_tablerow = self.in_tableheader = self.in_tabledata = 0
        self.in_pre = 0
        self.in_uli = 0
        self.in_oli = 0
        self.oli_level = 0
        self.uli_level = 0

    def _emph_repl(self, word): # Original '''bold''' and ''italic'' markup
        if len(word) == 3:
            self.is_b = not self.is_b
            return ['</b>', '<b>'][self.is_b]
        else:
            self.is_em = not self.is_em
            return ['</em>', '<em>'][self.is_em]

    def _emf_repl(self, word):  # **Bold** added for Wiki Creole compliance
        asterisks = re.search("\*+",word)
        length = len(asterisks.group(0))
        if length == 2:
            self.is_bold = not self.is_bold
            return ['</strong>', '<strong>'][self.is_bold]
        else:
            return word

    def _ital_repl(self, word):  # //Italic// added for Wiki Creole compliance
        self.is_ital = not self.is_ital
        return ['</em>', '<em>'][self.is_ital]

    def _brk_repl(self, word):  # \\ Line break added for Wiki Creole compliance
        return '<br/>'

    def _heading_repl(self, word):          # == Heading and == Heading == added for Wiki Creole compliance
        regex_eq = re.compile('={2,}')      # Make a regular expression to match two or more equals signs
        regex_heading = re.compile('[^=]+') # Make a regular expression to match one or more occurrences
                                            # of something other than equals signs
        equals = regex_eq.findall(word)
        text_heading = regex_heading.findall(word)
        # Determine heading size from length of first set of = characters in list
        # Since a minimum of two equal signs are needed, subtract one from length so
        # two equals signs correspond to <h1>.
        s = '<h%d>' % (len(equals[0])-1) + text_heading[0] + '</h%d>' % (len(equals[0])-1)
        return s

    def _wikilink_repl(self, word):
        # Make a regex to match one or more occurrences of other than an open 
        # or closed square bracket and its leading or trailing spaces
        #regex_wikiword = re.compile('[^\[|^\]]+')
        regex_wikiword = re.compile('[^\[\s*|^\]\s*]+')
        text_wikiword = regex_wikiword.findall(word)
        # Join wiki word into one big string
        text_wikiwordii = ''.join(text_wikiword)
        return Page(text_wikiwordii).link_to()

    def _namedurl_repl(self, word):
        # Make a regular expression to match one or more occurrence of other than open or closed
        # square bracket that also contains a pipe character.
        regex_namedurl = re.compile('[^\[|^\]]+')
        text_namedurl = regex_namedurl.findall(word)
        return '<a href="%s">%s</a>' % (text_namedurl[0], text_namedurl[1])

    def _image_repl(self, word):
        # Make a regular expression to match one or more occurrence of other than open or closed
        # curly braces that also contains a pipe character.
        regex_image = re.compile('[^\{|^\}]+')
        text_image = regex_image.findall(word)
        return '<img src="%s" title="%s" />' % (text_image[0], text_image[1])

    def _tableheader_repl(self, word):
        s = ""
        if self.in_table == 0: # If not in table mode
            self.in_table = 1  # Set table mode on
            s = "\n<table>\n"  # Print table tag

        if self.in_tablerow == 0:# If not in table row mode    
            self.in_tablerow = 1 # Set table row mode on
            s = s + "\n<tr>\n"   # Print table row tag

        if self.in_tableheader == 0: # If not in table header mode    
            self.in_tableheader = 1  # Set tableheader mode on
            s = s + "<th>"           # Print table header tag
        else:
            s = s + "</th>" + "<th>" # Print table header close tag

        return s

            
    def _tabledata_repl(self, word):
        s = ""
#        if self.in_table == 0: # If not in table mode
#            self.in_table = 1  # Set table mode on
#            s = "\n<table>\n"  # Print table tag

        if self.in_table == 1: # If already in table mode

            if self.in_tablerow == 0:# If not in table row mode    
                self.in_tablerow = 1 # Set table row mode on
                s = s + "\n<tr>\n"   # Print table row tag

            if self.in_tabledata == 0:# If not in table data mode    
                self.in_tabledata = 1 # Set table data mode on
                s = s + "<td>"        # Print table data tag
            else:
                self.in_tableheader = 0  # Set table data mode off
                s = s + "</td>" + "<td>" # Print table data close tag

        return s


    def _tablerowend_repl(self, word):
        s = ""
        if self.in_table == 1:         # If in table mode
            if self.in_tabledata == 1: # If in table data mode    
                self.in_tabledata = 0  # Set table data mode off
                s = s + "</td>"        # Print table data close tag

            if self.in_tableheader == 1: # If in table header mode 
                self.in_tableheader = 0  # Set table header mode off
                s = s + "</th>"          # Print table header close tag

            if self.in_tablerow == 1: # If in table row mode    
                self.in_tablerow = 0  # Set table row mode off
                s = s + "\n</tr>\n"   # Print table row close tag

        return s
     
    def _rule_repl(self, word):
        s = ""
        if len(word) <= 4:
            s = s + "\n<hr>\n"
        else:
            s = s + "\n<hr size=%d>\n" % (len(word) - 2 )
        return s

    def _word_repl(self, word):
        return Page(word).link_to()


    def _url_repl(self, word):
        return '<a href="%s">%s</a>' % (word, word)


    def _email_repl(self, word):
        return '<a href="mailto:%s">%s</a>' % (word, word)


    def _ent_repl(self, s):
        return {'&': '&amp;',
                '<': '&lt;',
                '>': '&gt;'}[s]
    

    def _uli_repl(self, string):
        asterisks = re.search("\*+",string)
        length = len(asterisks.group(0))
        if self.in_uli == 0 and length == 1:
            self.in_uli = 1
            self.uli_level =  1
            return '<ul>\n<li>'
        elif self.in_uli == 1:
            if length > self.uli_level: 
                self.uli_level = self.uli_level + 1
                return '</li>\n<ul>\n<li>'
            elif length < self.uli_level: 
                s = '</li>'
                while length < self.uli_level:
                      s = s + "\n</ul>\n"  # Print uli close tag
                      self.uli_level = self.uli_level - 1
                return s + '<li>'
            else:
                return '</li>\n<li>'
        elif self.in_uli == 0 and length == 2:   # If we encounter a ** at the beginning of a line, 
                                                 # and we're not it uli mode
              self.is_bold = not self.is_bold    # then this is bold markup. Handle this just like bold markup.
              return ['</strong>', '<strong>'][self.is_bold]
        else:
                return string


    def _oli_repl(self, string):
        poundsigns = re.search("#+",string)
        length = len(poundsigns.group(0))
        if self.in_oli == 0 and length == 1:
            self.in_oli = 1
            self.oli_level =  1
            return '<ol>\n<li>'
        elif self.in_oli == 1:
            if length > self.oli_level: 
                self.oli_level = self.oli_level + 1
                return '</li>\n<ol>\n<li>'
            elif length < self.oli_level: 
                s = '</li>'
                while length < self.oli_level:
                      s = s + "\n</ol>\n"  # Print oli close tag
                      self.oli_level = self.oli_level - 1
                return s + '<li>'
            else:
               return '</li>\n<li>'
        else:
                return ''


    def _pre_repl(self, word):
        if word == '{{{' and not self.in_pre:
            self.in_pre = 1
            return '<pre>'
        elif self.in_pre:
            self.in_pre = 0
            return '</pre>'
        else:
            return ''

    def _macro_repl(self, word):
        macro_name = word[2:-2]
        # TODO: Somehow get the default value into the search field
        return globals()['_macro_' + macro_name](*())


    def replace(self, match):
        for type, hit in list(match.groupdict().items()):
            if hit:
                return getattr(self, '_' + type + '_repl')(*(hit,))
        else:
            raise "Can't handle match " + repr(match)
        

    def print_html(self):
        # For each line, we scan through looking for magic
        # strings, outputting verbatim any intervening text.
        scan_re = re.compile(
            r"(?P<ital>(?<!:)//)"                       # //Italic// markup added for Wiki Creole
                                                        # (No colons before the slashes to prevent :// on
                                                        # undefined urls from matching).
            + r"|(?P<brk>\\{2})"                        # \\ Line break added for Wiki Creole
            # == Heading and == Heading == added for Wiki Creole
            + r"|(?P<heading>={2,}[[\w| |'|,|\-|\.|/|\?|\!]+)"
            # Slashes aren't allowed in WikiWords because they affect the directory path
            + r"|(?P<wikilink>\[\[[\w| |'|\-|\.]+\]\])" # [[wiki word]] added for Wiki Creole
            + r"|(?P<namedurl>\[\[([^|]*)\|[\w| |'|\-|\.|/]+\]\])" # [[URL|linkname]] added for Wiki Creole
            + r"|(?P<pre>\{{3}|\}{3})"                  # Replace {{{ and }}} with preformatted HTML tag
            + r"|(?P<image>\{\{([^|]*\|[\w| |'|\-|.|/]+)\}\})" # {{image.jpg|title}} added for Wiki Creole
            + r"|(?P<tableheader>\|=)"                  # |= Table header markup added for Wiki Creole
            + r"|(?P<tablerowend>\|\s*$)"               # | Table row end markup added for Wiki Creole
            + r"|(?P<tabledata>\|(?!\=))"               # | Table data markup added for Wiki Creole
            + r"|(?P<ent>[<>&])"                        # Replace <, >, and & with appropriate HTML tags
            + r"|(?P<rule>-{4,})"                       # Replace dashes with HTML horitonal rule tag.
            + r"|(?P<url>(http|https|ftp|nntp|news|mailto|file)\:[^\s'\"]+\S)"
            + r"|(?P<email>[\w\-\.+]+@(\w[\w\-]+\.)+[\w\-]+)"
            + r"|(?P<oli>^\s*#+)"
            + r"|(?P<uli>^\s*\*+)"
            + r"|(?P<emf>\*+)"                          # **Bold** markup added for Wiki Creole
                                                        # Give uli precedence over bold
                                                        # to prevent ** uli sub bullet
                                                        # items from being confused with
                                                        # the start of bold markup.
            + r"|(?:(?P<emph>'{2,3})"                   # Original '''bold''' and ''italic'' markup
            + r"|(?P<word>\b(?:[A-Z][a-z]+){2,}\b)"     # Original CamelCase wiki word
            + r"|(?P<macro>\(\((TitleSearch|FullSearch|WordIndex"
                            + r"|TitleIndex|RecentChanges|GoTo)\)\))"
            + r")")

        # When in preformatted mode, only look for a subset of
        # magic strings, outputting verbatim any intervening text.
        scan_pre = re.compile(
            r"(?:(?P<pre>\{{3}|\}{3})"
            + r"|(?P<ent>[<>&])"
            + r"|(?P<macro>\(\((TitleSearch|FullSearch|WordIndex"
                            + r"|TitleIndex|RecentChanges|GoTo)\)\))"
            + r")")

        blank_re = re.compile("^\s*$")
        eol_re = re.compile(r'\r?\n')
        no_table_re = re.compile("[^|]")
        no_oli_re = re.compile("^\s*#+")
        no_uli_re = re.compile("^\s*\*+")

        raw = str.expandtabs(self.raw)
        for line in eol_re.split(raw):
            if self.in_table:
                 # Table scan mode
                 # If the next line doesn't have a | character in it,
                 # assume table is complete.
                 if no_table_re.match(line):
                    self.in_table = 0  # Set table mode off
                    print("\n</table>\n")  # Print table close tag
            if self.in_oli == 1:
                 # Ordered list scan mode
                 # If the next line doesn't have a # character in it,
                 # assume list is complete.
                 if no_oli_re.match(line) == None:
                     self.in_oli = 0  # Set oli mode off
                     s = '</li>'
                     while self.oli_level != 0:
                         s = s + "\n</ol>\n"  # Print oli close tag
                         self.oli_level = self.oli_level - 1
                     print(s)
            if self.in_uli == 1:
                 # Unordered list scan mode
                 # If the next line doesn't have a * character in it,
                 # assume list is complete.
                 if no_uli_re.match(line) == None:
                     self.in_uli = 0  # Set uli mode off
                     s = '</li>'
                     while self.uli_level != 0:
                         s = s + "\n</ul>\n"  # Print uli close tag
                         self.uli_level = self.uli_level - 1
                     print(s)
            # Normal scan mode
            if not self.in_pre:
            # XXX: Should we check these conditions in this order?
                        if blank_re.match(line):
                            print('<p>')
                            continue
                        print(re.sub(scan_re, self.replace, line))   #Normal scan
            else:
                        print(re.sub(scan_pre, self.replace, line))  #Preformatted scan

# When we reach here, the last line in the page has already been processed.
# Clean up any preformatting, tables, or lists left open.
        if self.in_pre: print('</pre>') # If user forgets closing braces, put </pre> at end of page.
        if self.in_table:
                 # Assume table is complete.
                    self.in_table = 0  # Set table mode off
                    print("\n</table>\n")  # Print table close tag
        if self.in_oli == 1:
                 # Assume ordered list is complete.
                     self.in_oli = 0  # Set oli mode off
                     s = '</li>'
                     while self.oli_level != 0:
                         s = s + "\n</ol>\n"  # Print oli close tag
                         self.oli_level = self.oli_level - 1
                     print(s)
        if self.in_uli == 1:
                 # Assume unordered list is complete.
                     self.in_uli = 0  # Set uli mode off
                     s = '</li>'
                     while self.uli_level != 0:
                         s = s + "\n</ul>\n"  # Print uli close tag
                         self.uli_level = self.uli_level - 1
                     print(s)

# Page ------------------------------------------------------------
class Page:
    def __init__(self, page_name):
        self.page_name = page_name


    def split_title(self):
        # If the wiki word is CamelCase, 
        # look for the end of words and the start of a new word,
        # and insert a space there
        return re.sub('([a-z])([A-Z])', r'\1 \2', self.page_name)


    def _text_filename(self):
        return path.join(text_dir, self.page_name)


    def _tmp_filename(self):
        return path.join(text_dir, ('#' + self.page_name + '.' + repr(os.getpid()) + '#'))


    def exists(self):
        try:
            os.stat(self._text_filename())
            return 1
        except OSError as er:
            if er.errno == errno.ENOENT:
                return 0
            else:
                raise er
        

    def link_to(self):
        word = self.page_name
        if self.exists():
            return link_tag(word, word)
        else:
            if nonexist_qm:
                return link_tag(word, '?', 'nonexistent') + word
            else:
                return link_tag(word, word, 'nonexistent')


    def get_raw_body(self):
        try:
            return open(self._text_filename(), 'rt').read()
        except IOError as er:
            if er.errno == errno.ENOENT:
                # just doesn't exist, use default
                return 'Describe %s here.' % self.page_name
            else:
                raise er
    

    def send_page(self, msg=None):
        ##link = get_scriptname() + '?fullsearch=' + self.page_name
        #Changed the above line to the below to make it easy to grab
        #the URL to a page from its title. I didn't find the previous
        #use of searching for this WikiWord in other documents helpful,
        #plus it was duplicated in the find page section at the bottom.
        link = self.page_name
        send_title(self.split_title(), link, msg)
        PageFormatter(self.get_raw_body()).print_html()
        print_footer(self.page_name, 1, self._last_modified())


    def _last_modified(self):
        if not self.exists():
            return None
        modtime = localtime(os.stat(self._text_filename())[stat.ST_MTIME])
        return strftime(datetime_fmt, modtime)


    def send_editor(self):
        send_title('Edit ' + self.split_title())
        print('<form method="post" action="%s">' % (get_scriptname()))
        print('<input type=hidden name="savepage" value="%s">' % (self.page_name))
        raw_body = (self.get_raw_body()).replace('\r\n', '\n')
        print("""<textarea wrap="virtual" name="savetext" rows=%s
                 cols=%s>%s</textarea>""" % (text_area_rows , text_area_cols,  raw_body))
        print("""<br><input type=submit value="Save">
                 <input type=reset value="Reset">
                 """)
        print("<br>")
        print("</form>")
        print("<p>" + Page('EditingTips').link_to())
                 

    def _write_file(self, text):
        tmp_filename = self._tmp_filename()
        open(tmp_filename, 'wt').write(text)
        text = self._text_filename()
        if os.name == 'nt':
            # Bad Bill!  POSIX rename ought to replace. :-(
            try:
                os.remove(text)
            except OSError as er:
                if er.errno != errno.ENOENT: raise er
        os.rename(tmp_filename, text)


    def save_text(self, newtext):
        self._write_file(newtext)
        remote_name = environ.get('REMOTE_ADDR', '')
        editlog_add(self.page_name, remote_name)
        
# Main Program ----------------------------------------------------

print("Content-type: text/html")
print()

try:
    form = cgi.FieldStorage()

    handlers = { 'fullsearch':  do_fullsearch,
                 'titlesearch': do_titlesearch,
                 'edit':        do_edit,
                 'savepage':    do_savepage }

    for cmd in list(handlers.keys()):
        if cmd in form:
            handlers[cmd](*(form[cmd].value,))
            break
    else:
        path_info = environ.get('PATH_INFO', '')
        # On Apache, PATH_INFO will be set to /wikipage .
        # On IIS, PATH_INFO is /piki.py/wikipage . The latter won't work.
        # Get IIS & Apache to both say /wikipage by using 
        # path.basename to get foo and adding a / .
        path_info = '/' + os.path.basename(path_info)

        # On IIS, PATH_INFO of / is /piki.py. The latter won't work.
        # Change /piki.py to just / .
        scriptname  = os.path.basename( get_scriptname() )
        if re.search( scriptname , path_info ): path_info = '/'

        if 'goto' in form:
            query = form['goto'].value
        elif len(path_info) and path_info[0] == '/':
            query = path_info[1:] or 'FrontPage'
        else:       
            query = environ.get('QUERY_STRING', '') or 'FrontPage'

        word_match = re.match(word_re_str, query)
        if word_match:
            word = word_match.group(0)
            Page(word).send_page()
        else:
            print("<p>Can't work out query \"<pre>" + query + "</pre>\"")

except:
    cgi.print_exception()

sys.stdout.flush()
