Django Amazon Cloud
======================

Very simple Amazon Web Service admin in django.
This package only works with latest python and django releases.
Very much under development and not ready yet.

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
 * boto version 1.9 or above
 * python-dateutil for date manipulation
 
 
 Features
 ==============
  * Manage multiple accounts on Amazon Web Services (AWS).
  * Store your AMIs as well as public ones.
  * Manage your instances, start, stop, reboot, terminate.
  * Create an AMI from a running instance.
  * KeyPair and Security Group management.

