from tracker.models import Statistic, CountryStatistic
from django.contrib import admin


class StatisticAdmin(admin.ModelAdmin):

    list_display = ('label', 'category', 'counter', 'day', 'dom_id')
    list_filter = ('day', 'category', 'label')

class CountryStatisticAdmin(admin.ModelAdmin):
    list_display = ('tag','month', 'year', 'country')
    list_filter = ('tag', 'month', 'year', 'country')

admin.site.register(Statistic, StatisticAdmin)
admin.site.register(CountryStatistic, CountryStatisticAdmin)

