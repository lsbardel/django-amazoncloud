from django.contrib import admin, messages
from django.conf import settings
from django import http

from amazoncloud import models, forms
from amazoncloud.core import utils


def launch_instance(modeladmin, request, queryset):
    if queryset.count() == 1:
        ami = queryset[0]
        url = '{0}amazoncloud/instance/add/?ami={1}'.format(settings.ADMIN_URL_PREFIX,ami.pk)
        return http.HttpResponseRedirect(url)
    else:
        messages.error(request, "Select on image at a time when launching new instances.")
launch_instance.short_description = "Launch new instance"

def instance_command(command, queryset):
    for obj in queryset:
        c = obj.ec2()
        comm = getattr(c,command,None)
        if comm:
            r = comm([obj.id])
            if r:
                inst = r[0]
                obj.state = inst.state
                obj.save()

def terminate_instances(modeladmin, request, queryset):
    instance_command('terminate_instances',queryset)

def reboot_instances(modeladmin, request, queryset):
    instance_command('reboot_instances',queryset)

def stop_instances(modeladmin, request, queryset):
    instance_command('stop_instances',queryset)


class AMIAdmin(admin.ModelAdmin):
    list_display = ('id','name','region','size','root_device_type','accno','our','is_public','platform','architecture','timestamp')
    list_filter = ('is_public', 'root_device_type', 'architecture', 'region', 'our')
    search_fields  = ('name', 'description', 'architecture')
    
    actions = [launch_instance]
    
    def has_change_permission(self, request, obj=None):
        if obj:
            return False
        else:
            return True

    
class InstanceAdmin(admin.ModelAdmin):
    list_display = ('id','account','ami','root','state','timestamp','type','region','public_dns_name',
                    'ip_address','key_pair','security','monitored')
    form = forms.InstanceForm
    actions = [terminate_instances, reboot_instances, stop_instances]
    
    def has_change_permission(self, request, obj=None):
        if obj:
            return False
        else:
            return True
        
    def save_model(self, request, obj, form, change):
        if change:
            return obj
        c   = obj.ec2()
        res = c.run_instances(obj.ami.id,
                              key_name = obj.key_pair.name,
                              security_groups = obj.sgroup(),
                              instance_type=obj.type,
                              monitoring_enabled=obj.monitored)
        utils.updateReservation(res)
        
    def get_actions(self, request):
        actions = super(InstanceAdmin, self).get_actions(request)
        del actions['delete_selected']
        return actions
        
    
    
admin.site.register(models.AMI, AMIAdmin)
admin.site.register(models.Instance, InstanceAdmin)
admin.site.register(models.AwsAccount, list_display=['account_number','access_key','secret_key','prefix'])
admin.site.register(models.SecurityGroup, list_display=['account','name'])
