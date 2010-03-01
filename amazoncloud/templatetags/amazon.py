from django import template

register = template.Library()

def amazon_submit(context):
    opts = context['opts']
    change = context['change']
    is_popup = context['is_popup']
    save_as = context['save_as']
    return {
        'onclick_attrib': (opts.get_ordered_objects() and change
                            and 'onclick="submitOrderForm();"' or ''),
        'show_delete_link': (not is_popup and context['has_delete_permission']
                              and (change or context['show_delete'])),
        'is_popup': is_popup,
        'show_save': True
    }
amazon_submit = register.inclusion_tag('admin/amazoncloud/submit_line.html', takes_context=True)(amazon_submit)