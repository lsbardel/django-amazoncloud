from django.contrib import admin

from amazoncloud.models import AwsAccount, AMI


class AMIAdmin(admin.ModelAdmin):
    list_display = ('id','name','region','size','root_device_type','accno','our','is_public','platform','architecture','timestamp')
    list_filter = ('is_public', 'root_device_type', 'architecture', 'region')
    search_fields  = ('name', 'description', 'architecture')
    
admin.site.register(AMI, AMIAdmin)
admin.site.register(AwsAccount, list_display=['account_number','access_key','secret_key','prefix'])