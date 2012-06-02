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

import elementtree.ElementTree as ET
from django.template import loader
import datetime
import string
import os

from config import Config


class ETWrap:
  '''Wrapper for an ElementTree element.
  
  Allows attribute calls for XML tags.  For example:
    if welement.visible:
      title = welement.title
      
  Allows for accessing namespaced tags as well:
    content = welement.ns('content').encoded
  
  This implementation was inspired by Fredrik Lundh's RSS wrappers on
  his effbot.org site:
    http://effbot.org/zone/element-rss-wrapper.htm
  
  Attributes:
    namespace: (static) Namespace dictionary.
  '''
  namespace = {}
  def __init__(self, element, ns_dict={}, ns_uri=""):
    '''Initializes this puppy.
    
    Args:
      element: Element to wrap.
      ns_dict: Namespace dict for looking up prefixes and URIs.
      ns_uri: Namespace URI to prefix for attribute calls.
    
    Returns:
      A wrapped element.
    '''
    self._element = element
    self._ns_dict = ns_dict if len(ns_dict) > 0 else ETWrap.namespace
    self._ns = ns_uri
    
  def __getattr__(self, tag):
    '''Get an attribute.'''
    if tag.startswith("__"):
      raise AttributeError(tag)
    if tag == 'attrib':
      return self._element.attrib
    if tag == 'text':
      return self._element.text
    if tag == 'tail':
      return self._element.text
    return self._element.findtext(self._ns+tag)
    
  def ns(self, prefix):
    '''Get the element with the namespace set.
    
    Args:
      prefix: The namespace prefix. 
    
    Returns:
      A wrapped element, but with the namespace set.
    '''
    for name, uri in self._ns_dict.iteritems():
      if name == prefix:
        return ETWrap(self._element, self._ns_dict, uri)
    return self
    
  def unwrap(self):
    '''Get the raw ElementTree element.'''
    return self._element
    
def et_sub(element, tag, text=None):
  '''Create a sub-element under element.
  
  Args:
    element: Expecting parent.
    tag: String tag name.
    text: String text for the new child.
  
  Returns:
    The newborn child element.
  '''
  sub = ET.SubElement(element, tag)
  if text != None:
    sub.text = text
  return sub
  
def onlyAlphaNum(dirty, repl=' ', whitelist=''):
  '''Filter/replace non-alphanumeric characters.
  
  Args:
    dirty: A string to filter
    repl: Character used to replace non-alphanumeric characters.  Set to empty
      string to remove instead of replace.
    whitelist: Do not remove or replace characters in this string.
  
  Returns:
    A filtered string.
  '''
  keepers = '%s%s%s'%(string.ascii_letters, string.digits, whitelist)
  replace_chars = string.maketrans(keepers, '\x00'*len(keepers))
  if repl != '':
    replace_chars = string.maketrans(replace_chars, repl*256)
    return dirty.encode('ascii','ignore').translate(replace_chars)
  else:
    return dirty.encode('ascii','ignore').translate(None, replace_chars)
    
def cleanCSV(csv):
  '''Sanitize a comma separated value string.
  
  Args:
    csv: String to clean.
  
  Returns:
    The sparkling new csv string.
  '''
  parts = onlyAlphaNum(csv,'',' ,').split(',')
  parts = [r.strip() for r in parts if r != '']
  return ','.join(set(parts))
    
def parse_and_get_ns(file):
  '''Use ElementTree to parse an XML file, but retain namespace information.
  
  Args:
    file: XML file to parse.
  
  Returns:
    Tuple with this structure: (ElementTree, namespace dict)
    
  Raises:
    KeyError: A duplicate prefix was found that has a different
      URI.  This is perfectly valid XML, but shows how this parser
      is deficient.
  '''
  events = "start", "start-ns"
  root = None
  ns = {}
  for event, elem in ET.iterparse(file, events):
    if event == "start-ns":
      if elem[0] in ns and ns[elem[0]] != elem[1]:
        # NOTE: It is perfectly valid to have the same prefix refer
        #   to different URI namespaces in different parts of the
        #   document. This exception serves as a reminder that this
        #   solution is not robust.  Use at your own peril.
        raise KeyError("Duplicate prefix with different URI found.")
      ns[elem[0]] = "{%s}" % elem[1]
    elif event == "start":
      if root is None:
        root = elem
  return (ET.ElementTree(root), ns)
  
###
### Project specific utility functions
###

def getURL(date, slug, type='post'):
  '''Create a URL string for a page or post.'''
  if date == None or type != 'post':
    return '/%s/'%(slug)
  return '/%04d/%02d/%02d/%s/'%(date.year, date.month, date.day, slug)
    
def getFilepath(filename):
  '''Appends the filename to the to the project directory path.'''
  module_dir = os.path.dirname(__file__)
  return os.path.join(module_dir, filename)
  
def getContentFilepath(date, slug):
  '''Creates a content file path which is located in Config.POST_DIR.'''
  filename = ("%s_%s.xml")%(date.strftime('%Y%m%d'), slug)
  filename = os.path.join(Config.POST_DIR, filename)
  return getFilepath(filename)
  
def checkBaseline():
  '''Checks the filesystem for minimum file requirements and creates
  missing files if needed.
  
  Returns:
    Filepath to catalog file.
  '''
  filepath = getFilepath(Config.POST_DIR)
  if not os.path.exists(filepath):
    os.makedirs(filepath, 0755)
  filename = os.path.join(Config.POST_DIR, Config.CATALOG_FILE)
  filepath = getFilepath(filename)
  if not os.path.exists(filepath):
    root = ET.Element("catalog")
    root.set("version", "0.1")
    tree = ET.ElementTree(root)
    tree.write(filepath, "UTF-8")
  return filepath
  
def getTemplate(filename, isSU=False):
  '''Get a template.'''
  template_dir = Config.SU_TEMPLATES if isSU else Config.THEME_TEMPLATES
  if template_dir:
    filename = os.path.join(template_dir, filename)
  return loader.get_template(filename)
  