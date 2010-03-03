from django.contrib import admin, messages
from django.conf import settings
from django import http


from amazoncloud import models, forms
from amazoncloud.core import utils
from amazoncloud import actions

class EC2Admin(admin.ModelAdmin):
    '''
    Base class for amazon admin
    '''
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
    list_display=['id','prefix','access_key']
    
    actions = [actions.create_key_pair]
    

    
class KeyPairAdmin(EC2Admin):
     list_display=['account','name','fingerprint']
     
     actions = [actions.delete_key_pairs]
     
     def save_model(self, request, obj, form, change):
        if change:
            return obj
        c   = obj.ec2()
        res = c.create_key_pair(obj.name)
        obj.fingerprint = res.fingerprint
        obj.material = res.material or ''
        obj.save()
     
    
class AMIAdmin(EC2Admin):
    list_display = ('id','name','region','size','root_device_type','accno','cost','our',
                    'is_public','platform','architecture','location','timestamp','snapshot')
    list_filter = ('is_public', 'root_device_type', 'architecture', 'region', 'our')
    search_fields  = ('name', 'description', 'architecture')
    form    = forms.CreateImage
    actions = [actions.launch_instance,
               actions.deregister_images]
    
    def add_view(self, request, **kwargs):
        if request.method == 'GET':
            initial = dict(request.GET.items())
            id = initial.get('id',None)
            # The id is an instance id
            if id:
                inst = models.Instance.objects.get(id = id)
                ami  = inst.ami
                initial['instance'] = id
                initial['name'] = ami.name
                initial['description'] = ami.description
            request.GET = initial
        return super(AMIAdmin,self).add_view(request, **kwargs)
    
    def save_model(self, request, obj, form, change):
        if change:
            return super(AMIAdmin,self).save_model(request, obj, form, change)
        try:
            data = form.cleaned_data
            inst = models.Instance.objects.get(id = data['instance'])
            c    = inst.ec2()
            id = c.create_image(inst.id, data['name'], data['description'])
            if id:
                self.message_user(request, 'CReated new AMI %s' % id)
        except Exception, e:
            messages.error(request,str(e))

    
class InstanceAdmin(EC2Admin):
    list_display = ('id','account','ami','root','size','state','timestamp','type',
                    'region','public_dns_name',
                    'ip_address','key_pair','security','volume','persistent','monitored')
    form = forms.InstanceForm
    actions = [actions.terminate_instances,
               actions.reboot_instances,
               actions.stop_instances,
               actions.create_image,
               actions.monitor_instances,
               actions.unmonitor_instances,
               actions.install_packages]
            
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
            ebsblock.delete_on_termination = not obj.persistent
            if obj.size > 0:
                ebsblock.size = obj.size
        sgn = [s.name for s in form.cleaned_data['security_groups']]
        res = c.run_instances(image.id,
                              key_name = obj.key_pair.name,
                              security_groups = sgn,
                              instance_type=obj.type,
                              monitoring_enabled=obj.monitored,
                              block_device_map = image.block_device_mapping)
        aws = utils.AWS()
        aws.updateReservation(res)

class SnapShotAdmin(EC2Admin):
    list_display=['id', 'accno', 'size', 'state', 'timestamp', 'our', 'cost']
    list_filter = ('state', 'our')
            
class VolumeAdmin(EC2Admin):
    list_display=['id', 'account', 'size', 'region', 'state', 'instance', 'snapshot', 'cost']

class IpAddressAdmin(admin.ModelAdmin):
    list_display=['account','ip','instance','cost']
    form = forms.CreateAddress
    
    def save_model(self, request, obj, form, change):
        if change:
            return obj
        acc    = form.cleaned_data['account']
        addr   = acc.allocate_address()
        obj.ip = addr.public_ip
        super(IpAddressAdmin,self).save_model(request, obj, form, change)
        
    
    
    
    
admin.site.register(models.AMI, AMIAdmin)
admin.site.register(models.Instance, InstanceAdmin)
admin.site.register(models.AwsAccount, AwsAccountAdmin)
admin.site.register(models.SecurityGroup, list_display=['account','name'])
admin.site.register(models.KeyPair,KeyPairAdmin)
admin.site.register(models.Installer, list_display=['name','osystem'])
admin.site.register(models.EbsVolume, VolumeAdmin)
admin.site.register(models.SnapShot, SnapShotAdmin)
admin.site.register(models.IpAddress, IpAddressAdmin)
