from django.core.management.base import copy_helper, CommandError, BaseCommand
from django.utils.importlib import import_module
import os


class Command(BaseCommand):
    help = "Sync Amazon Web Services Accounts"

    requires_model_validation = True
    can_import_settings = True

    def handle(self, *args, **options):
        from amazoncloud.core import utils
        aws = utils.AWS()
        aws.sync_accounts()
        utils.updateInstances()