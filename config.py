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

class Config:
  '''Configuration settings class.
  
  Attributes (all static):
    ...see below...
  '''
  
  # EDIT with your specific site details:
  SITE_NAME = 'A New Filestack Website'
  SITE_TITLE = 'Website Title'
  SITE_MOTTO = 'A pithy statement or mantra'
  SITE_DESCRIPTION = ''
  SITE_KEYWORDS = ''
  POSTS_PER_PAGE = 10
  
  # Located in project dir (filestack)
  POST_DIR = 'posts'
  
  # Located in templates dir
  # For files: index.html, cattag.html, 404.html, detail.html
  THEME_TEMPLATES = 'newsprint'
  # For files: su.html, su_edit.html
  SU_TEMPLATES = 'su'
  
  # Directory located in /media
  UPLOAD_DIR = 'uploads'
  
  # No reason to change this
  CATALOG_FILE = "catalog.xml"
  
  # Located in posts dir
  WP_XML_FILE = ''
  
  # Posts on or older than WP_END_DATE will be served by WP_XML_FILE
  WP_END_DATE = '1910-01-13'
  