#!/usr/bin/python
'''
Copyright (C) 2012 Mark West.

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at
 
   http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
'''

'''
Information:
  Use this command line utility to manage filestack files.
  
  See usage() below to see what it does and how it is used.
'''

import os
import sys
import elementtree.ElementTree as ET

import util

def main():
  argc = len(sys.argv)
  if argc > 1:
    arg_1 = sys.argv[1].lower()
    if arg_1 == 'trash' and argc == 3:
      path = None
      if sys.argv[2].lower() != 'delete':
        path = os.path.normpath(sys.argv[2])
        if not os.path.exists(path) or \
           not os.path.isdir(path):
          print "Error: Path is not a valid directory.\n"
          return
      trash(path)
      return
  print usage()

def usage():
  return "su.py ACTION ARGUMENT\n" \
    "ACTIONS:\n" \
    "help:  This help text\n" \
    "trash: Remove trash elements from listing\n" \
    "  delete:  Trash files are deleted\n" \
    "  DIRPATH: Trash files are moved to the supplied path"
    
def trash(path):
  catalog_path = util.checkBaseline()
  tree = ET.parse(catalog_path)
  root = tree.getroot()
  items = tree.findall('/trash')
  files_to_trash = []
  for i in items:
    witem = util.ETWrap(i)
    files_to_trash.append(witem.filepath)
    root.remove(i)
  if files_to_trash:
    tree.write(catalog_path, 'UTF-8')
    for f in files_to_trash:
      if path:
        new_path = os.path.join(path, os.path.basename(f))
        os.rename(f, new_path)
      else:
        os.remove(f)
    print "Success: The trash has been taken out."
  else:
    print "Success: Trash was already empty."
  return True
    
if __name__ == "__main__":
  main()
