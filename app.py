#!/usr/bin/python
import time
import subprocess
import os
from configParser import Config
from os import listdir
from os.path import isfile, join, isdir

# __file__ refers to the file settings.py
APP_ROOT = os.path.dirname(os.path.abspath(__file__)) + '/'  # refers to application_top
SUPPORT_PATH = APP_ROOT + 'support/'
HTML_PATH = SUPPORT_PATH + 'html/'
DATA_PATH = APP_ROOT + 'data/'
HOST_DIR = DATA_PATH + 'dst/'
BASE_DIR = DATA_PATH + 'source/'

CSS_DIR = SUPPORT_PATH + 'css'

MARKDOWN = APP_ROOT + 'Markdown.pl'

HOME_PAGE_HEADER = ""
HOME_PAGE_TRAILER = ""

def translateMdFileToHtml( mdFile, outFileName ):
    tmpFileName = outFileName + ".tmp"
    tmpFile = open(outFileName + ".tmp" , "w")
    inFile = open( mdFile, 'r' )

    p = subprocess.Popen(MARKDOWN,
              shell=True, stdout=tmpFile, stdin=inFile)
    p.wait()
    tmpFile.close()
    tmpFile = open(outFileName + ".tmp" , "r")
    tmpFile.seek(0)
    lines = tmpFile.read()
    tmpFile.close()
    inFile.close()

    header = '<!doctype html>\n '
    header += '<title> BYJ </title >\n'
    header += '<head> <link rel="stylesheet" type="text/css" href="/path/bootstrap/css/bootstrap.css"> </head>\n'
    header += '<body>\n <div class=mainContent>\n'
    trailer = '</div>\n</body>\n'
    with open(outFileName, "w") as outFile:
        outFile.write(header)
        with open(tmpFileName ) as addFile:
            for line in addFile:
                outFile.write(line)
        outFile.write(trailer)
        os.remove(tmpFileName)

def copyFile( src, dst ):
    with open(src, "r") as inFile:
        with open(dst, "w") as outFile:
            for line in inFile:
                outFile.write(line)

def findMdFilesInternal( dirname, cfg ):
    MdFileList = list()
    myPath = BASE_DIR + dirname
    for root, dirs, files in os.walk( myPath ):
        for name in files:
            if name.endswith(cfg.extn):
                MdFileList.append( os.path.join( root, name ) )

    httpLinks = list()
    for mdFile in MdFileList:
        outFileName = mdFile.replace(BASE_DIR, '')
        outFileName = outFileName.replace('/', '___').rsplit('.yj.md.html', 1)[0] + ".html"
        httpLink = outFileName.rsplit('.yj.md.html', 1)[0]
        httpLinks.append(httpLink)
        outFileName = HOST_DIR + 'pages/' + outFileName
        translateMdFileToHtml( mdFile, outFileName )
        copyFileName = outFileName.replace('.yj.md.html', '.ymd')
        copyFile( mdFile, copyFileName)

    mySet = dict()
    mySet["mdFiles"] = httpLinks
    return mySet

"""
Each Node represents a directory and could contain sub-directories and
files. A node also has a complete pathname, class and other meta data
associated with it. This meta data is useful for expanding/collapsing
the node in the html rendering.
"""
class Node:
    def __init__(self, path, parentPath=""):
        self.dirs = dict()
        self.files = list()
        self.name = path
        self.fullName = parentPath + "/" + path

    def __str__(self):
        return "Node: " + self.fullName

    def addSubNode(self, name):
        if name not in self.dirs:
            self.dirs[name] = Node(name, self.fullName)
        return self.dirs[name]

    def getSubNode(self, name):
        if name in self.dirs:
            return self.dirs[name]
        else:
            return None

    def getMyClassTags(self):
        return self.fullName.replace("/", "___") + ("___");

    def getSubClasses(self):
        subClasses = ""
        names = self.fullName.split("/")[1:]
        # Take the name, split it and add subclasses ending with ___.
        # If name is a/b/c, the subclasses will be
        # ___a___ ___a___b___ ___a___b___c___
        # These are used for collapsing
        for i in range(1, len(names) + 1):
            className = "___"
            for j in range(i):
                className += names[j] + "___"
            subClasses += ( className + " " )
        # Finally add the subclass
        # ___a___b___c
        # This one is used for expanding (showing)
        subClasses += className.rstrip("___")
        print self.fullName, ":", subClasses
        return subClasses

    def getMyAbsClassTag(self):
        return self.fullName.replace("/", "___") + ("___");

"""
This function takes in the list of files and creates
a hierarchical Node structure that represents how
data is present in the directory.
"""
def formRecursiveDict( names, separator='___' ):
    dictRoot = Node("root")
    for pathName in names:
        pathList = pathName.split( '___' )
        # Run once through the list and create all the dirs.
        # Use only upto path[:-1]
        subNode = dictRoot
        for nodeName in pathList[:-1]:
            subNode = subNode.addSubNode( nodeName )
        # Run once more through the list and create all the files.
        subNode = dictRoot
        for nodeName in pathList:
            if nodeName not in subNode.dirs:
                #subNode.files.append(nodeName)
                subNode.files.append(pathName)
            else:
                subNode = subNode.dirs[nodeName]
    return dictRoot

"""
This function takes the hierarchical Node structure and forms html
elements that are used to provide the navigation panel
"""
def pretty_items(htmlText, inpData, nametag="<strong>%s </strong>",
             itemtag="<li  id='%s' onclick='%s' class='%s' >%s</li>",
             itemtagCollapse="<li  id='%s' onclick='%s' class='%s collapse'>%s</li>",
             valuetag="  %s", blocktag=('<ul>', '</ul>')):
    if len(inpData.files) > 0:
        htmlText.append(blocktag[0])
        for i in inpData.files:
            link = i.split('___')[-1]
            htmlText.append(itemtagCollapse % ( i, \
                        "changeContent(this)", \
                        inpData.getSubClasses(), \
                        link ) )
        htmlText.append(blocktag[1])
    if len(inpData.dirs) > 0:
        htmlText.append(blocktag[0])
        for k, v in inpData.dirs.iteritems():
            name = nametag % k
            htmlText.append(itemtagCollapse % ( inpData.getMyAbsClassTag() + k, \
                        "collapse(this)", \
                        inpData.getSubClasses(), \
                        name) )
            pretty_items(htmlText, v)
        htmlText.append(blocktag[1])
    return htmlText

"""
pretty_items is a tricky function. We need the list we pass to the function. But
the pretty_items function uses recursion and hence cannot return it directly.
So we hold a reference.
"""
def formHtmlText( inpData ):
    reference = list()
    pretty_items( reference, inpData )
    return '\n'.join(reference)

def createHtmlDivOfFiles( files ):
    rDict = formRecursiveDict( files )
    htmlDiv = formHtmlText( rDict )
    return htmlDiv
"""
CreateHomePage does all the work of finding all the MD files
converting them. Forming a Node Hierarchy, converting that
to a navigation section and creating the home page.
"""
def createHomePage(cfg):
   files = findMdFilesInternal( '', cfg )[ 'mdFiles' ]
   files.sort()
   htmlFile = DATA_PATH + 'dst/index.html'
   with open(HTML_PATH + "home_page_header.html") as f:
       HOME_PAGE_HEADER = "".join( f.readlines() )
   with open(HTML_PATH + "home_page_trailer.html") as f:
       HOME_PAGE_TRAILER = "".join( f.readlines() )
   with open( htmlFile, 'w' ) as homePage:
       homePage.write(HOME_PAGE_HEADER)
       lines = createHtmlDivOfFiles(files)
       homePage.write(lines)
       homePage.write(HOME_PAGE_TRAILER)


def cleanup():
    pass

def parseConfig():
    pass

def init():
    cfg = Config(".config")
    createHomePage(cfg)


if __name__ == '__main__':
    cleanup()
    init()
