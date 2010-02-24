from django.contrib import admin

from amazoncloud.models import AwsAccount, AMI


class AMIAdmin(admin.ModelAdmin):
    list_display = ('id','root_device_type','account','is_public','platform','architecture')
    list_filter = ('is_public', 'root_device_type')
    
    
admin.site.register(AMI, AMIAdmin)
admin.site.register(AwsAccount, list_display=['account_number','access_key','secret_key','prefix'])