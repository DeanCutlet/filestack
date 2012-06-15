===================================
Filestack: Simple blogging platform
===================================

Introduction:
-------------

Filestack was created after one too many security breaches of a WordPress installation.  The massive install base of WordPress makes it a delightful target for spam and hackers.

Filestack harkens back to the days of static files served from a webserver, but incorporates quick formatting and publishing of content for a single user.  The lack of a database makes backup as simple as a cron job using tar and security holes are further minimized by removing destructive actions like deleting content.

It is possible for Filestack to be used as a failsafe or bridge for a compromised WordPress installation.  The admin may wish to serve a static WordPress export file with Filestack until the site is cleaned and back in action.


Features:
---------

* Simple single user CMS with rich HTML editing with TinyMCE.
* Database-less: Data is stored in static files.
* Non-destructive: Data cannot be deleted through HTTP (must have server access).
* Uses Python/Django instead of PHP.
* Templates and all the Django goodies.
* Quick Wordpress replacement/recovery.


Requirements:
-------------

* Python 2.6+
* Django 1.2+
* SSH access to your server


Installation:
-------------

Standard:

1. Put the Filestack source directory in your Django site directory (e.g. in the "public/.." directory).
2. Copy the "filestack/media/fs" directory to "public/media".
3. Set your site information in "filestack/config.py" (site_name, site_title, etc...).
4. Add "filestack/templates" to TEMPLATE_DIRS in settings.py.
5. Include filestack to urls.py.  Add the following to the end of urlpatterns in your urls.py file:
  url(r'', include('filestack.urls')),
6. Create a Django user for editing and creating content:
   - https://docs.djangoproject.com/en/1.2/topics/auth/#creating-users
7. Restart Django (e.g. pkill python)

WordPress migration:

1. Generate an XML export file for your WordPress site.
2. Put a copy of the XML export file in filestack/posts
3. Set wp_xml_file and wp_end_date in filestack/config.py
4. Copy the WordPress upload content to the Django public directory. (e.g. cp -r BACKUP/wp-content/uploads public/wp-content)


Usage:
------

To create pages and posts, log in as super user by visiting www.YOURSITE.com/su/ in your browser.  Log in with the user created in the installation instructions above.

Pages and posts can be created (click around to figure out how it works) and they can be moved to trash.  However, they cannot be permanently deleted except by accessing the server.

To remove trash items use the "su.py" script in the Filestack app directory.

  > python su.py trash delete
  
Uploads are located in UPLOAD_DIR in the public/media directory.


Copyright and License:
----------------------

Copyright (c) 2012 Mark West.

Filestack is under the Apache 2.0 license.  See LICENSE for more information.


Contact:
--------

Questions or comments?  Contact mwest1910(at)gmail.com for more information.
