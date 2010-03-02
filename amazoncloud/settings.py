from django.conf import settings

SSH_KEYS_PATH = getattr(settings,'SSH_KEYS_PATH',None)

EBS_COST_GB_MONTH = 0.1
EBS_COST_IO_MILLION = 0.1
COST_CLOUD_WATCH_HOUR = 0.015