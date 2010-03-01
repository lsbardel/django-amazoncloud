
from django.core.management.base import copy_helper, CommandError, BaseCommand
from django.utils.importlib import import_module
import os


class Command(BaseCommand):
    help = "Update Amazon database"

    requires_model_validation = True
    can_import_settings = True

    def handle(self, *args, **options):
        '''
        Updates accounts, security group, keypairs, own images and instances
        '''
        from amazoncloud.core import utils
        aws = utils.AWS()
        aws.sync_accounts()
        aws(all = False)
        utils.updateInstances()