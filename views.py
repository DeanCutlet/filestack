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

from django.http import HttpResponse, HttpResponseNotFound
from django.template import Context, RequestContext
from django.shortcuts import redirect
from django import forms

import elementtree.ElementTree as ET
import random
import datetime
import os

import util
import wp
from config import Config
  
###
### XML operations
###  

def findElement(xml_tree, slug):
  '''Find an element in the XML tree with the given slug.
  
  Args:
    xml_tree: XML tree as an ElementTree object.
    slug: Name/ID of the item to find.
  
  Returns:
    The found element or None if no element was found.
  '''
  types = ['/post', '/page', '/trash']
  for t in types:
    elements = xml_tree.findall(t)
    for e in elements:
      iwrap = util.ETWrap(e)
      if iwrap.name == slug:
        return e
  return None
  
def elementToItem(element):
  '''Convert an XML element into a item (a simple dict).
  
  Args:
    element: Element to convert.
  
  Returns:
    A dict representation of the XML element.
  '''
  welem = util.ETWrap(element)
  ret = {
    'type': welem.type,
    'name': welem.name,
    'date': welem.date,
    'url': welem.url,
    'title': welem.title,
    'status': welem.status,
    'filepath': welem.filepath,
    'parent': welem.parent,
    'content': welem.content,
    'tags': welem.tags.split(',') if welem.tags else [],
    'categories': welem.categories.split(',') if welem.categories else [],
    'trash': welem.trash
    }
  return ret
  
def getItems(xml_tree, what='posts', filter_lambda=None):
  '''Get all the items from the XML tree of a certain type.
  
  Args:
    xml_tree: XML tree as an ElementTree object.
    what: Type of elements to search for (posts, pages, or trash).
    filter_lambda: Additional filter called before adding item to
      list.  The lambda is passed a single dict argument and should
      return True if the item should be added to the list.
  
  Returns:
    A list of items, which are simple dicts.
  '''
  ret = []
  paths = {'posts': '/post', 'pages': '/page', 'trash': '/trash'}
  elements = xml_tree.findall(paths[what])
  for e in elements:
    item = elementToItem(e)
    if not filter_lambda or filter_lambda(item):
      ret.append(addDates(item))
  ret = sorted(ret, key=lambda i: i['date'], reverse=True)
  return ret
  
def newElem(type='post'):
  '''Create a new XML element.
  
  Args:
    type: The type of element to create (post or page).
  
  Returns:
    A default XML element of the given type.
  '''
  now = datetime.datetime.utcnow()
  now = now.replace(microsecond = 0)
  nowSpace = now.isoformat(' ')
  slug = util.onlyAlphaNum(now.isoformat('_'),'-')
  filepath = util.getContentFilepath(now, slug)
  while os.path.exists(filepath):
    nowSpace = "%s0"%(nowSpace)
    slug = "%s0"%(slug)
    filepath = util.getContentFilepath(now, slug)
  item = {
      'date': nowSpace,
      'name': slug,
      'title': nowSpace,
      'type': type,
      'status': 'hidden',
      'filepath': util.getContentFilepath(now, slug),
      'url': util.getURL(now, slug, type),
      'parent': '',
      'trash': ''
    }
  new_elem = ET.Element(type)
  updateElem(new_elem, item)
  return new_elem

def updateElem(element, item):
  '''Update the contents of the element with the contents of the item.
  
  Note: Everything in the element will be removed before saving the
    content from item.
    
  Args:
    element: The XML element to update.
    item: The source item with the data saved to the element.  It must
      have: date, name, url, type, and filepath.
  
  Returns:
    The updated element.
  '''
  if 'date' not in item or \
     'name' not in item or \
     'url' not in item or \
     'type' not in item or \
     'filepath' not in item:
    raise Exception('Dict parameter is missing required key')
  element.clear()
  for key, value in item.iteritems():
    if value and not isinstance(value, basestring):
      value = ','.join(value)
    if key == 'tag':
      element.tag = value
    elif key != 'content':
      util.et_sub(element, key, value)
  # Defaults for optional arguments
  if 'title' not in item:
    util.et_sub(element, 'title', item['date'])
  if 'status' not in item:
    util.et_sub(element, 'status', 'hidden')
  return element
  
###
### XML Content file operations
###

def toContentElement(element, content=None):
  '''Convert an element to a content element.
    
  Args:
    element: The XML element to convert.
    content: String to save as the element's content instead of the default.
  
  Returns:
    The converted element.
  '''
  element.tag = 'item'
  if not content:
    content = 'Add content <b>here</b>...'
  util.et_sub(element, 'content', content)
  return element

def writeContentFile(element):
  '''Write an element to a file.
    
  Args:
    element: The element used to write the content file.
  '''
  welement = util.ETWrap(element)
  xml_tree = ET.ElementTree(element)
  xml_tree.write(welement.filepath, 'UTF-8')
  
def save(slug, item=None):
  '''Write an item to the filesystem (both catalog and content file).
    
  Args:
    slug: The original slug of the item.  item['name'] will become the new slug.
      NOTE - Set slug to 'post' or 'page' to create and save a new item.
    item: The item to save to the filesystem.
    
  Returns:
    True on success; False on error.
    
  Raises:
    Exception: If the item is None and the slug isn't "post" or "page".
  '''
  catalog_path = util.checkBaseline()
  xml_tree = ET.parse(catalog_path)
  root = xml_tree.getroot()
  new_elem = None
  content = None
  oldFilepath = None
  if slug != 'post' and slug != 'page':
    if item == None:
      raise Exception('Argument cannot be None')
    if slug != item['name']:
      if findElement(xml_tree, item['name']):
        return False  # Name collision
    # Update old element (delete and recreate)
    element = findElement(xml_tree, slug)
    if element:
      welement = util.ETWrap(element)
      os.remove(welement.filepath)
      root.remove(element)
    new_elem = ET.Element(item['type'])
    updateElem(new_elem, item)
    content = item['content']
  else: # Create new element
    new_elem = newElem(slug)
  root.append(new_elem)
  xml_tree.write(catalog_path, 'UTF-8')
  writeContentFile(toContentElement(new_elem, content))
  return True
  
def trash(request, slug, delete=True):
  '''Mark or unmark an item for trash and save it to the filesystem.
    
  Args:
    request: The view request object.
    slug: The slug for the item.
    delete: Send the item to the trash if True; Restore otherwise.
    
  Returns:
    True on success; False on error.
  '''
  catalog_path = util.checkBaseline()
  xml_tree = ET.parse(catalog_path)
  root = xml_tree.getroot()
  element = findElement(xml_tree, slug)
  if not element:
    return False
  welement = util.ETWrap(element)
  item = elementToItem(element)
  item['tag'] = 'trash' if delete else welement.type
  item['trash'] = 'true' if delete else 'false'
  root.remove(element)
  updateElem(element, item)
  root.append(element)
  xml_tree.write(catalog_path, 'UTF-8')
  return True
  
def loadContent(item, force=False):
  '''Load the content into an item from the filesystem.
    
  Args:
    item: Item to load the content into.  Uses item['filepath'].
    force: If true, overwrite item['content'] even if it already exists.
    
  Returns:
    The content string.
  '''
  if force or not item['content']:
    if not os.path.exists(item['filepath']):
      return ""
    xml_tree = ET.parse(item['filepath'])
    wroot = util.ETWrap(xml_tree.getroot())
    return wroot.content
  else:
    return item['content']
  
###
### Item operations
###

def isVisible(item):
  '''Should the item be shown to the site visitor?
    
  Args:
    item: Item to test.
    
  Returns:
    True if the item is visible; false otherwise.
  '''
  if item['status'].lower() != 'visible':
    return False
  now = datetime.datetime.utcnow().isoformat(' ')
  if item['date'] > now:
    return False
  return True
  
def addDates(item):
  '''Add additional date fields to an item.
    
  Args:
    item: Item to update.
    
  Returns:
    The updated item.
  '''
  date_size = len("YYYY-MM-DD")
  item['date_short'] = item['date'][0:date_size]
  (item['year'], item['month'], item['day']) = item['date_short'].split('-')
  item['time'] = item['date'][date_size+1:date_size+9]
  return item
  
def findContext(items, slug):
  '''Find an item with the slug in items (a list of items).
    
  Args:
    items: List of items to search.
    slug: Item with a matching slug will be returned.
    
  Returns:
    A found item or None if not found.
  '''
  slug = slug.upper()
  item = next((i for i in items if i['name'].upper().endswith(slug)), None)
  return item
  
def getCategories(items):
  '''Get all the categories in the list of items.
    
  Args:
    items: List of items to get categories.
    
  Returns:
    A set of all the categories.
  '''
  cats = set()
  for i in items:
    if i['categories']:
      cats.update(i['categories'])
  return cats

###
### Template context operations
###
  
def getDefaultContext(request):
  '''Get the default context for templates.
    
  Args:
    request: View request object.
    
  Returns:
    A RequestContext object with default values.
  '''
  c = RequestContext(request, {
    'version': 0.1,
    'username': '' if not request else request.user,
    'SITE_NAME': Config.SITE_NAME,
    'SITE_MOTTO': Config.SITE_MOTTO,
    'title': Config.SITE_TITLE,
    'site_discription': Config.SITE_DESCRIPTION,
    'SITE_KEYWORDS': Config.SITE_KEYWORDS,
    'menu': [],
    'posts': [],
    'pages': [],
    'trash': [],
    'recent': [],
    'random': [],
    'categories':[],
    'now':datetime.datetime.utcnow().isoformat(' ')
  })
  return c
  
def assembleContext(context, xml_tree, wp_tree):
  '''Update a template context with info from both XML trees.
  
  Updated fields: posts, menu, recent, random, and categories.
    
  Args:
    context: Context to update (usually a default context).
    xml_tree: Standard XML tree object.
    wp_tree:  Wordpress XML tree object.
  '''
  context['posts'] = getItems(xml_tree, 'posts', isVisible) + \
    wp.getItems(wp_tree, 'posts', isVisible)
  context['menu'] = getMenu(xml_tree, wp_tree)
  context['recent'] = context['posts'][0:Config.POSTS_PER_PAGE]
  rdm_posts = len(context['posts'])
  if rdm_posts > Config.POSTS_PER_PAGE:
    rdm_posts = Config.POSTS_PER_PAGE
  context['random'] = random.sample(context['posts'], rdm_posts)
  context['categories'] = getCategories(context['posts'])
  
def getSUContext(request, xml_tree):
  '''Get the context for the SU pages.
    
  Args:
    request:  View request object.
    xml_tree: XML tree object used to build the context.
    
  Returns:
    A context with posts, pages, and trash already set.
  '''
  context = getDefaultContext(request)
  context['posts'] = getItems(xml_tree, 'posts')
  context['pages'] = getItems(xml_tree, 'pages')
  context['trash'] = getItems(xml_tree, 'trash')
  return context
  
###
### Menu Operations
###
  
def getChildren(family_tree, id='0'):
  '''Get the list of children for an id in the tree.
    
  Args:
    family_tree: Dict with key=id, value=list of children (title,slug,id)
    wp_tree:  WordPress tree used to build the menu.
    
  Returns:
    A list of tuples structred like: (title, slug, [child tuples])
  '''
  ret = []
  if id not in family_tree or len(family_tree[id]) <= 0:
    return ret
  for member in family_tree[id]:
    ret.append((member[0], member[1], getChildren(family_tree, member[2])))
  return ret
  
def getMenu(xml_tree, wp_tree=None):
  '''Build a menu using the XML trees.
    
  Args:
    xml_tree: XML tree object used to build the menu.
    wp_tree:  WordPress tree used to build the menu.
    
  Returns:
    A list of tuples structred like: (title, slug, [child tuples])
  '''
  pages = getItems(xml_tree, 'pages', isVisible)
  if wp_tree:
    pages.extend(wp.getItems(wp_tree, 'pages'))
  family_tree = {}
  for p in pages:
    id = p['post_id'] if 'post_id' in p else p['name']
    parent = p['parent'] if 'parent' in p and p['parent'] else '0'
    if parent not in family_tree:
      family_tree[parent] = [(p['title'], p['name'], id)]
    else:
      family_tree[parent].append((p['title'], p['name'], id))
    if id not in family_tree:
      family_tree[id] = []
  return getChildren(family_tree)
  
def flattenMenu(menu):
  '''Get a list of all the slugs in a menu.
    
  Args:
    menu: Menu to flatten.
    
  Returns:
    List of slugs.
  '''
  if not menu:
    return []
  ret = []
  for i in menu:
    ret.append(i[1])
    ret.extend(flattenMenu(i[2]))
  return ret
  
###
### Form operations
###

class EditForm(forms.Form):
  '''Form used to edit an item in the SU pages.

  Attributes:
    ...See below...
  '''
  title = forms.CharField()
  date = forms.DateField(input_formats=['%Y-%m-%d', '%Y/%m/%d', '%m/%d/%Y', '%m-%d-%Y'])
  time = forms.TimeField(input_formats=['%H:%M:%S', '%H:%M', '%H'])
  status = forms.ChoiceField(choices=[('visible', 'visible'),('hidden', 'hidden')])
  name = forms.SlugField()
  categories = forms.CharField(required=False)
  tags = forms.CharField(required=False)
  content = forms.CharField()
  parent = forms.ChoiceField(choices=(), required=False)
  
  def __init__(self, *args, **kwargs):
    '''Initializes EditForm.
      
    Args:
      parents: Choices tuple for parent selection.
    '''
    parents = kwargs.pop('parents', None)
    forms.Form.__init__(self, *args, **kwargs)
    if parents:
      self.fields['parent'].choices = parents
      
class UploadFileForm(forms.Form):
  '''Form used to upload a file.

  Attributes:
    ...See below...
  '''
  file  = forms.FileField()
  
def itemToForm(item, parent_choices):
  '''Convert an item to an EditForm object.
    
  Args:
    item: Item to convert.
    parent_choices: Tuple of parent choices selection.
    
  Returns:
    An EditForm.
  '''
  parent = item['parent'] if item['parent'] else '0'
  form = EditForm({
      'title': item['title'],
      'date': item['date_short'],
      'time': item['time'],
      'status': item['status'],
      'name': item['name'],
      'categories': ','.join(item['categories']),
      'tags': ','.join(item['tags']),
      'content': item['content'],
      'parent': parent
      }, parents=parent_choices)
  return form

def formToItem(form, orig_item):
  '''Convert an EditForm object to an item.
    
  Args:
    form: Form to convert.
    orig_item: Original item to use for default values.
    
  Returns:
    An item.
  '''
  keys = ['status','categories','name','title','tags','content']
  if orig_item['type'] == 'page':
    keys.append('parent')
  item = dict((k, form.cleaned_data[k]) for k in keys)
  date = datetime.datetime.combine(form.cleaned_data['date'], form.cleaned_data['time'])
  item['date'] = date.isoformat(' ')
  item['url'] = util.getURL(date, item['name'], orig_item['type'])
  item['categories'] = util.cleanCSV(item['categories'])
  item['tags'] = util.cleanCSV(item['tags'])
  item['type'] = orig_item['type']
  item['filepath'] = util.getContentFilepath(date, item['name'])
  return item
  
###
### View operations
###
  
def handleUpload(request):
  '''Handle a file upload.
  
  All files will be saved in Config.UPLOAD_DIR inside the
    Django /media directory.
    
  Args:
    request: View request object.
    
  Returns:
    A tuple with (UploadFileForm, message title, message body).
  '''
  if request.method == 'POST':
    form = UploadFileForm(request.POST, request.FILES)
    if form.is_valid():
      f = request.FILES['file']
      filename = os.path.basename(f.name)
      filepath = os.path.join('public', 'media', Config.UPLOAD_DIR)
      if not os.path.exists(filepath):
        os.makedirs(filepath, 0755)
      filepath = os.path.join(filepath, filename)
      if os.path.exists(filepath):
        return (form, 'Upload failed', 'The file \'%s\' already exists.'%(filename))
      destination = open(filepath, 'wb+')
      for chunk in f.chunks():
          destination.write(chunk)
      destination.close()
      msg = 'The file has been successfully uploaded.  Congrats!<br/><br/> \
             See for yourself:<br/> \
             <a href=\'/media/%s/%s\'>.../media/%s/%s</a>' % (Config.UPLOAD_DIR, \
             filename, Config.UPLOAD_DIR, filename)
      return (form, 'Upload successful', msg)
    return (form, 'Upload failed', 'Unable to upload the file.  Try again.')
  else:
    form = UploadFileForm()
  return (form, '', '')
  
def showList(request, category=None, tag=None):
  '''Get response for showing a list of posts.
    
  Args:
    request: View request object.
    category: Show only items containing this category string.
    tag: Show only items containing this tag string.
    
  Returns:
    A post list response.
  '''
  p = int(request.GET.get('p', 0))
  itemsPerPage = Config.POSTS_PER_PAGE
  xml_tree = ET.parse(util.checkBaseline())
  wp_tree = wp.loadXML()
  c = getDefaultContext(request)
  filter = isVisible
  if category:
    filter = lambda d: category in d['categories'] and isVisible(d)
  if tag:
    filter = lambda d: tag in d['tags'] and isVisible(d)
  all_posts = getItems(xml_tree, 'posts', filter) + \
    wp.getItems(wp_tree, 'posts', filter)
  posts = all_posts[p*itemsPerPage:(p+1)*itemsPerPage]
  c['prev'] = -1 if p == 0 else p-1
  c['next'] = -1 if p >= len(all_posts)/itemsPerPage else p+1
  if len(posts) > 0:
    for p in posts:
      p['content'] = loadContent(p)
    assembleContext(c, xml_tree, wp_tree)
    c['posts'] = posts
    tfile = 'index.html'
    if category or tag:
      tfile = 'cattag.html'
      c['title'] += " - Tagged %s" % (tag) if tag else " - Category %s" % (category)
    t = util.getTemplate(tfile)
    return HttpResponse(t.render(c))
  return get404(request, xml_tree, wp_tree)
  
def get404(request, xml_tree, wp_tree):
  '''Get a 404 response.
    
  Args:
    request: View request object.
    xml_tree: Standard XML tree object.
    wp_tree: WordPress XML tree object.
    
  Returns:
    HttpResponseNotFound object.
  '''
  c = getDefaultContext(request)
  c['menu'] = getMenu(xml_tree, wp_tree)
  t = util.getTemplate('404.html')
  return HttpResponseNotFound(t.render(c))
  
def getDetail(request, type, slug, date=None):
  '''Get the response for a page or post.
  
  Args:
    request: Django HttpRequest object
    type: The type of response requested.  Must be 'page' or 'post'.
    slug: Name/ID of the item.
    date: Optional date of item used to reduce searching.
  
  Returns:
    An HttpResponse for the requested item.
  '''
  what = {'post': 'posts', 'page': 'pages'}
  xml_tree = ET.parse(util.checkBaseline())
  wp_tree = wp.loadXML()
  c = getDefaultContext(request)
  c['posts'] = getItems(xml_tree, what[type], isVisible)
  if not date or date.strftime('%Y-%m-%d') <= Config.WP_END_DATE:
    c['posts'] += wp.getItems(wp_tree, what[type])
  c['post'] = findContext(c['posts'], slug)
  if c['post']:
    c['post']['content'] = loadContent(c['post'])
    c['title'] += " - %s" % (c['post']['title'])
    assembleContext(c, xml_tree, wp_tree)
    t = util.getTemplate('detail.html')
    return HttpResponse(t.render(c))
  return get404(request, xml_tree, wp_tree)
  
def getSU(request, err_title_msg=None):
  '''Get the SU page response
  
  Args:
    request: Django HttpRequest object
    err_title_msg: Tuple with structure: (error title, error message)
  
  Returns:
    An HttpResponse for the SU page.
  '''
  if not request.user.is_authenticated():
    return redirect('django.contrib.auth.views.login')
  tree = ET.parse(util.checkBaseline())
  c = getSUContext(request, tree)
  if err_title_msg:
    c['dlg_title'] = err_title_msg[0]
    c['dlg_msg'] = err_title_msg[1]
  else:
    c['upload'], c['dlg_title'], c['dlg_msg'] = handleUpload(request)
  t = util.getTemplate('su.html', isSU=True)
  return HttpResponse(t.render(c))
  
###
### View Handlers ###
###

def index(request):
  '''The main index page for the site.'''
  return showList(request)

def category(request, category):
  '''Show all posts with a given category.'''
  return showList(request, category)
  
def tag(request, tag):
  '''Show all posts with a given tag.'''
  return showList(request, tag=tag)
  
def detail(request, year=None, month=None, day=None, slug=None):
  '''Individual post.'''
  date = datetime.datetime(int(year), int(month), int(day))
  return getDetail(request, 'post', slug, date)
  
def page(request, slug):
  '''Individual page.'''
  slug = slug.split('/')[-2] if slug[-1:] =='/' else slug.split('/')[-1]
  return getDetail(request, 'page', slug)
  
def su(request):
  '''Super User page.'''
  return getSU(request)
  
def su_edit(request, slug):
  '''SU edit item page.'''
  if not request.user.is_authenticated():
    return redirect('django.contrib.auth.views.login')
  tree = ET.parse(util.checkBaseline())
  c = getSUContext(request, tree)
  c['upload'], c['dlg_title'], c['dlg_msg'] = handleUpload(request)
  c['post'] = findContext(c['pages']+c['posts']+c['trash'], slug)
  c['post']['content'] = loadContent(c['post'])
  parent_choices = [('0', '0')]
  if c['post']['type'] == 'page':
    pages = flattenMenu(getMenu(tree))
    if slug in pages:
      pages.remove(slug)
    page_choices = [(p, p) for p in pages]
    parent_choices.extend(page_choices)
  if request.method == 'POST':
    c['form'] = EditForm(request.POST, parents=parent_choices)
    if c['form'].is_valid():
      item = formToItem(c['form'], c['post'])
      if save(c['post']['name'], item):
        return redirect('su')
      c['dlg_title'] = "Failed to save %s" % (c['post']['type'])
      c['dlg_msg'] = "An error occurred while attempting to save.  Try again."
  else:
    c['form'] = itemToForm(c['post'], parent_choices)
  if c['post']['trash'] and c['post']['trash'].lower() == 'true':
    c['readonly'] = True
  t = util.getTemplate('su_edit.html', isSU=True)
  return HttpResponse(t.render(c))
  
def su_new(request, type):
  '''SU create new page or post item.'''
  if not request.user.is_authenticated():
    return redirect('django.contrib.auth.views.login')
  if type != 'post' and type != 'page':
    return redirect('django.contrib.auth.views.login')
  catalog_path = util.checkBaseline()
  tree = ET.parse(catalog_path)
  new_post = newElem(type)
  tree.getroot().append(new_post)
  tree.write(catalog_path, 'UTF-8')
  writeContentFile(toContentElement(new_post))
  return redirect('su')
  
def su_delete(request, slug):
  '''SU delete item.'''
  if not request.user.is_authenticated():
    return redirect('django.contrib.auth.views.login')
  err_msg = None
  if not trash(request, slug):
    err_msg = ("Failed to delete",\
               "An error occurred while attempting to delete item.  Try again.")
  return getSU(request, err_msg)
  
def su_restore(request, slug):
  '''SU restore deleted item.'''
  if not request.user.is_authenticated():
    return redirect('django.contrib.auth.views.login')
  err_msg = None
  if not trash(request, slug, False):
    err_msg = ("Failed to restore",\
               "An error occurred while attempting to restore item.  Try again.")
  return getSU(request, err_msg)
  