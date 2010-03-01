from django import template
from django import http
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import render_to_response
from django.utils.encoding import force_unicode
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.utils.text import capfirst
from django.contrib.admin import helpers
from django.contrib.admin.util import get_deleted_objects, model_ngettext
from django.utils.translation import ugettext_lazy, ugettext as _
from django.conf import settings

from amazoncloud.forms import InstallPackagesForm


def confirmation(modeladmin, request, queryset, action, question):
    opts = modeladmin.model._meta
    app_label = opts.app_label
    # Check that the user has delete permission for the actual model
    if not modeladmin.has_delete_permission(request):
        raise PermissionDenied
    
    # Populate deletable_objects, a data structure of all related objects that
    # will also be deleted.
    deletable_objects, perms_needed = get_deleted_objects(queryset, opts, request.user, modeladmin.admin_site, levels_to_root=2)
        
    if request.POST.get('post'):
        if perms_needed:
            raise PermissionDenied
        instance_command(action,queryset)
        return None

    context = {
               "action": action,
                "question": question,
                "title": _("Are you sure?"),
                "object_name": force_unicode(opts.verbose_name),
                "deletable_objects": deletable_objects,
                'queryset': queryset,
                "perms_lacking": perms_needed,
                "opts": opts,
                "root_path": modeladmin.admin_site.root_path,
                "app_label": app_label,
                'action_checkbox_name': helpers.ACTION_CHECKBOX_NAME,
                }
    return render_to_response(modeladmin.delete_confirmation_template or [
            "admin/%s/%s/delete_selected_confirmation.html" % (app_label, opts.object_name.lower()),
            "admin/%s/delete_selected_confirmation.html" % app_label,
            "admin/delete_selected_confirmation.html"
            ], context, context_instance=template.RequestContext(request))
        
    


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
                                                                     int(ami.size))
        return http.HttpResponseRedirect(url)
    else:
        messages.error(request, "Select on image at a time when launching new instances.")
launch_instance.short_description = "Launch new instance"

def deregister_images(modeladmin, request, queryset):
    for obj in queryset:
        c = obj.ec2()
        if c.deregister_image(obj.id):
            modeladmin.message_user(request, 'deregistered image {0}'.format(obj))

#_________________________________________________________ Actions on Instances
def terminate_instances(modeladmin, request, queryset):
    return confirmation(modeladmin, request, queryset, 'terminate_instances',
                     "Are you sure you want to terminate the selected instances?")

def reboot_instances(modeladmin, request, queryset):
    c = confirmation(modeladmin, request, queryset,'reboot_instances'
                     "Are you sure you want to reboot the selected instances?")

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
        
def install_packages(modeladmin, request, queryset):
    opts = modeladmin.model._meta
    app_label = opts.app_label
    
    if request.POST.get('post'):
        f = InstallPackagesForm(request.POST)
        if f.is_valid():
            for installer in f.cleaned_data['packages']:
                for obj in queryset:
                    installer.install(obj)
        return None
    
    platform = ''
    error = False
    for obj in queryset:
        objp = obj.ami.platform
        if not platform:
            platform = objp
        if not objp:
            error = True
            messages.error(request,"Platform not available for {0}".format(obj))
        elif objp != platform:
            error = True
            messages.error(request,"Wrong platform for {0}".format(obj))
            
    f = None
    if not error:
        f = InstallPackagesForm(platform = platform)
    
    context = {
               'form': f,
               'queryset': queryset,
               'error': error,
               "object_name": force_unicode(opts.verbose_name),
                "opts": opts,
                "root_path": modeladmin.admin_site.root_path,
                "app_label": app_label,
                'action_checkbox_name': helpers.ACTION_CHECKBOX_NAME,
               }
    return render_to_response("admin/%s/install_packages.html" % app_label,
                              context,
                              context_instance=template.RequestContext(request))
               
        
    
    
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


