======================
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

 * Multiple Accounts: you can setup multiple AWS accounts and manage them together.
 * **AMI**: the application stores your private AMI as well as public ones.
 * **Instances**: full management of your instances: start, stop, reboot, terminate.
 * Create a new AMI from a running instance.
 * **Image Resizing**. If the instance is mounted on EBS, you can resize it.
 * KeyPair and Security Group management.


Todo
============
 * Allow change of instance IP address
 * S3
 

