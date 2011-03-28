from django import template
from tracker import models

register = template.Library()

@register.inclusion_tag('country_stats.html')
def display_country(object_id):
    data = models.CountryStatistic.objects.get(id=object_id).data_serialized
    return { 'data': data }
