Django Amazon Cloud
======================

Amazon Web Service admin in django.
This package only works with latest python and django releases.
**Very much under development and not ready yet**.

The application works with the django version 1.2, not even the 1.1 version is supported (sorry).
In addition, it works with python 2.6 and above (not the 3 version).


Installation
================
Put the folder ``amazoncloud`` in your Python path or run::

    python setup.py install

in your INSTALLED_APPS add ``amazoncloud``


Requirements
===============

 * Python 2.6 or above (2.5 NOT SUPPORTED and not version 3)
 * Django version 1.2 or above
 * boto version 1.9 or above, actually boto svn is the best!!
 * python-dateutil for date manipulation
 
 
Features
==============

Multiple Accounts
------------------- 
You can setup multiple AWS accounts and manage them together.

AMI
------------------
The application stores your account's private AMI as well as public AMI

Instances
---------------
 * Full management of your instances: start, stop, reboot, terminate.
 * You can also create a new AMI from a running instance, implemented as an action in the Instances list.
 * **Image Resizing** If the type of instance is mounted on EBS, you can specify a different image size. in this way you can create new EBS images of different sizes.

Security
-----------
 * KeyPair and Security Group management.


Todo
============
 * S3
 

