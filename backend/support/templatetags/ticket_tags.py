from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag(takes_context=True)
def render_ticket_info(context):
    """Render ticket info display"""
    adminform = context.get('adminform')
    if adminform and hasattr(adminform, 'form') and adminform.form.instance.pk:
        model_admin = adminform.model_admin
        obj = adminform.form.instance
        return mark_safe(model_admin.ticket_info_display(obj))
    return ''


@register.simple_tag(takes_context=True)
def render_ticket_messages(context):
    """Render ticket messages display"""
    adminform = context.get('adminform')
    if adminform and hasattr(adminform, 'form') and adminform.form.instance.pk:
        model_admin = adminform.model_admin
        obj = adminform.form.instance
        return mark_safe(model_admin.messages_display(obj))
    return ''


@register.simple_tag(takes_context=True)
def render_ticket_reply_form(context):
    """Render ticket reply form display"""
    adminform = context.get('adminform')
    if adminform and hasattr(adminform, 'form') and adminform.form.instance.pk:
        model_admin = adminform.model_admin
        obj = adminform.form.instance
        return mark_safe(model_admin.reply_form_display(obj))
    return ''
