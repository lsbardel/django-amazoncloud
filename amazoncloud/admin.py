from django.contrib import admin

from amazoncloud.models import AwsAccount, AMI, Instance


class AMIAdmin(admin.ModelAdmin):
    list_display = ('id','name','region','size','root_device_type','accno','our','is_public','platform','architecture','timestamp')
    list_filter = ('is_public', 'root_device_type', 'architecture', 'region', 'our')
    search_fields  = ('name', 'description', 'architecture')
    
class InstanceAdmin(admin.ModelAdmin):
    list_display = ('id','ami','state','timestamp','type','public_dns_name','ip_address','monitored')
    
admin.site.register(AMI, AMIAdmin)
admin.site.register(Instance, InstanceAdmin)
admin.site.register(AwsAccount, list_display=['account_number','access_key','secret_key','prefix'])