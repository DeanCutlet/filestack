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

from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(r'^login/$', 'django.contrib.auth.views.login'),
    url(r'^logout/$', 'django.contrib.auth.views.logout'),
)

urlpatterns += patterns('filestack',
    url(r'^su/$', 'views.su', name='su'),
    url(r'^su/edit/(?P<slug>.+)/$', 'views.su_edit', name='su_edit'),
    url(r'^su/new/(?P<type>.+)/$', 'views.su_new', name='su_new'),
    url(r'^su/delete/(?P<slug>.+)/$', 'views.su_delete', name='su_delete'),
    url(r'^su/restore/(?P<slug>.+)/$', 'views.su_restore', name='su_restore'),
    url(r'^(?P<year>\d{4})/(?P<month>\d{2})/(?P<day>\d{2})/(?P<slug>.+)/$', \
      'views.detail', name='su_restore'),
    url(r'^category/(?P<category>.+)/$', 'views.category', name='category'),
    url(r'^tag/(?P<tag>.+)/$', 'views.tag', name='tag'),
    # Attention: These are catch-alls.
    url(r'(.*/)$', 'views.page', name='page'),
    url(r'^$', 'views.index', name='index'),
)
