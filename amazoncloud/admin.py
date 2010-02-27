from django.contrib import admin, messages
from django.conf import settings
from django import http

from amazoncloud import models, forms
from amazoncloud.core import utils

def instance_command(command, queryset):
    '''
    stop, reboot, terminate, monitor/unmonitor commands on instances
    '''
    for obj in queryset:
        inst = obj.instance()
        conn = inst.connection
        comm = getattr(conn,command,None)
        if comm:
            r = comm([obj.id])
            if r:
                inst = r[0]
                inst.update()
                obj.state = inst.state
                obj.monitored = inst.monitored
                obj.save()


#________________________________________________________ Actions on Images
def launch_instance(modeladmin, request, queryset):
    if queryset.count() == 1:
        ami = queryset[0]
        url = '{0}amazoncloud/instance/add/?ami={1}&size={2}'.format(settings.ADMIN_URL_PREFIX,
                                                                     ami.pk,
                                                                     ami.size)
        return http.HttpResponseRedirect(url)
    else:
        messages.error(request, "Select on image at a time when launching new instances.")
launch_instance.short_description = "Launch new instance"

def deregister_images(modeladmin, request, queryset):
    for obj in queryset:
        c = obj.ec2()
        if c.deregister_image(obj.id):
            self.message_user(request, 'deregistered image {0}'.format(obj))

#_________________________________________________________ Actions on Instances
def terminate_instances(modeladmin, request, queryset):
    instance_command('terminate_instances',queryset)

def reboot_instances(modeladmin, request, queryset):
    instance_command('reboot_instances',queryset)

def stop_instances(modeladmin, request, queryset):
    instance_command('stop_instances',queryset)

def monitor_instances(modeladmin, request, queryset):
    instance_command('monitor_instance',queryset)
    
def unmonitor_instances(modeladmin, request, queryset):
    instance_command('unmonitor_instance',queryset)

def create_image(modeladmin, request, queryset):
    if queryset.count() == 1:
        inst = queryset[0]
        url  = '{0}amazoncloud/ami/add/?id={1}'.format(settings.ADMIN_URL_PREFIX,inst.pk)
        return http.HttpResponseRedirect(url)
    else:
        messages.error(request, "Select on instance at a time when creating a new image.")
    
#__________________________________________________________ Actions on AwsAccounts
def create_key_pair(modeladmin, request, queryset):
    if queryset.count() == 1:
        acc = queryset[0]
        url = '{0}amazoncloud/keypair/add/?account={1}'.format(settings.ADMIN_URL_PREFIX,acc.pk)
        return http.HttpResponseRedirect(url)
    else:
        messages.error(request, "Select one account at a time when creating keypairs.")
        
#__________________________________________________________ Actions on KeyPair
def delete_key_pairs(modeladmin, request, queryset):
    for obj in queryset:
        c = obj.ec2()
        c.delete_key_pair(obj.name)
        obj.delete()




class EC2Admin(admin.ModelAdmin):
    
    #def has_change_permission(self, request, obj=None):
    #    if obj:
    #        return False
    #    else:
    #        return True
    
    def get_actions(self, request):
        actions = super(EC2Admin, self).get_actions(request)
        del actions['delete_selected']
        return actions
    

class AwsAccountAdmin(admin.ModelAdmin):
    list_display=['account_number','prefix','access_key']
    
    actions = [create_key_pair]
    

    
class KeyPairAdmin(EC2Admin):
     list_display=['account','name','fingerprint']
     
     actions = [delete_key_pairs]
     
     def save_model(self, request, obj, form, change):
        if change:
            return obj
        c   = obj.ec2()
        res = c.create_key_pair(obj.name)
        obj.fingerprint = res.fingerprint
        obj.material = res.material or ''
        obj.save()
     
    
class AMIAdmin(EC2Admin):
    list_display = ('id','name','region','size','root_device_type','accno','our',
                    'is_public','platform','architecture','location','timestamp')
    list_filter = ('is_public', 'root_device_type', 'architecture', 'region', 'our')
    search_fields  = ('name', 'description', 'architecture')
    
    actions = [launch_instance,deregister_images]
    
    def add_view(self, request, **kwargs):
        if request.method == 'GET':
            initial = dict(request.GET.items())
            id = initial.pop('id',None)
            # The id Could be an image id or an instance id
            if id:
                inst = models.Instance.objects.get(id = id)
                ami  = inst.ami
                initial['size'] = inst.size()
                initial['name'] = ami.name
                initial['description'] = ami.description
            request.GET = initial
        return super(AMIAdmin,self).add_view(request, **kwargs)
                

    
class InstanceAdmin(EC2Admin):
    list_display = ('id','account','ami','root','size','state','timestamp','type','region','public_dns_name',
                    'ip_address','key_pair','security','monitored')
    form = forms.InstanceForm
    actions = [terminate_instances, reboot_instances,
               stop_instances, create_image,
               monitor_instances, unmonitor_instances]
            
    def save_model(self, request, obj, form, change):
        '''
        Replace the save model with launch new instance
        '''
        # Cannot change an instance, only launch new one
        if change:
            return obj
        c   = obj.ec2()
        image = c.get_image(obj.ami.id)
        if image.root_device_type == 'ebs':
            rdn = image.root_device_name
            ebsblock = image.block_device_mapping[image.root_device_name]
            if obj.size > 0:
                ebsblock.size = obj.size
        res = c.run_instances(image.id,
                              key_name = obj.key_pair.name,
                              security_groups = obj.sgroup(),
                              instance_type=obj.type,
                              monitoring_enabled=obj.monitored,
                              block_device_map = image.block_device_mapping)
        utils.updateReservation(res)
        
    
    
admin.site.register(models.AMI, AMIAdmin)
admin.site.register(models.Instance, InstanceAdmin)
admin.site.register(models.AwsAccount, AwsAccountAdmin)
admin.site.register(models.SecurityGroup, list_display=['account','name'])
admin.site.register(models.KeyPair,KeyPairAdmin)
