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

import os
import elementtree.ElementTree as ET
from django.template import Context, loader

import util
from config import Config

def loadXML():
  '''Load the WordPress XML export file and return an ElementTree.

  Returns:
    ElementTree for the WordPress XML export file.
  '''
  if not Config.WP_XML_FILE:
    return None
  filepath = os.path.join(Config.POST_DIR, Config.WP_XML_FILE)
  filepath = util.getFilepath(filepath)
  if not os.path.exists(filepath):
    return None
  tree, ns = util.parse_and_get_ns(filepath)
  util.ETWrap.namespace = ns
  return tree
  
def cleanContent(content):
  '''Clean and insert proper HTML 'newlines'.
    
  Args:
    content: Content string.
    
  Returns:
    The cleaned string.
  '''
  ret = content.replace("\n\n", "<hr class='hr_0' style='visibility:hidden;'/>")
  return ret

def getCatTags(element):
  '''Get the categories and tags for an element.
    
  Args:
    element: Element to search.
    
  Returns:
    Tuple containing a category string list and a tag string list.
  '''
  cats = []
  tags = []
  foundcats = element.findall('category')
  for cat in foundcats:
    cat = util.ETWrap(cat)
    if cat.attrib.get('domain') == 'post_tag':
      tags.append(cat.text)
    else:
      cats.append(cat.text)
  return (cats, tags)

def elementToItem(welement):
  '''Get the dict representation of an element.
    
  Args:
    welement: util.ETWrap of the element to convert.
    
  Returns:
    The item.
  '''
  cats, tags = getCatTags(welement.unwrap())
  item = {
    'title': welement.title,
    'name': welement.ns('wp').post_name,
    'url': welement.link,
    'date': welement.ns('wp').post_date,
    'categories': cats,
    'tags': tags,
    'content': cleanContent(welement.ns('content').encoded),
    'type': welement.ns('wp').post_type,
    'status': 'visible'
  }
  if item['type'] == 'page':
    item['parent'] = welement.ns('wp').post_parent
    item['post_id'] = welement.ns('wp').post_id
  return item
  
def filterElements(elements, type):
  '''Filter a list of elements by type (and status).
    
  Args:
    elements: Elements to filter.
    type: Only keep elements of given type.
    
  Returns:
    Filtered and sorted (by date) list of elements.
  '''
  ret = {}
  for element in elements:
    welement = util.ETWrap(element)
    if welement.ns('wp').post_type == type and \
      (welement.ns('wp').status == "publish" or \
      welement.ns('wp').status == "future"):
      ret[welement.ns('wp').post_date] = element
  ret = sorted(ret.items(), reverse=True)
  final = [i[1] for i in ret]
  return final
      
def getItems(wp_tree, type='posts', filter_lambda=None):
  '''Get all the items from the XML tree of a certain type.
  
  Args:
    wp_tree: WordPress XML tree as an ElementTree object.
    type: Type of elements to search for (posts or pages).
    filter_lambda: Additional filter called before adding item to
      list.  The lambda is passed a single dict argument and should
      return True if the item should be added to the list.
  
  Returns:
    A list of items, which are simple dicts.
  '''
  if not wp_tree:
    return []
  paths = {'posts': 'post', 'pages': 'page'}
  all = wp_tree.findall("/channel/item")
  items = filterElements(all, paths[type])
  ret = []
  for i in items:
    d = elementToItem(util.ETWrap(i))
    if not filter_lambda or filter_lambda(d):
      ret.append(d)
  return ret
  