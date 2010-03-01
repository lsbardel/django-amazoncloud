
from django.core.management.base import copy_helper, CommandError, BaseCommand
from django.utils.importlib import import_module
import os


class Command(BaseCommand):
    help = "Update Amazon database"

    requires_model_validation = True
    can_import_settings = True

    def handle(self, *args, **options):
        '''
        Update public images
        '''
        from amazoncloud.core import utils
        aws = utils.AWS()
        added, removed = aws(all = True)
        print("added {0}, removed {1}".format(added,removed))