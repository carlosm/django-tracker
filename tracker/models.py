from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.core.cache import cache

import datetime
import pickle
import re
import operator

from django.db.models import Sum
from yadayada import countries
from yadayada.models import SerializedObjectField

TTL = 300 # 5 minutes
COLLECT_TIME = 120 # every 2 minutes

QUERY_STRING_VALIDATOR = r'[\w.\-\_\|\+ ]+'
MONTHS_CHOICES = ((1, 'January'),
 (2, 'February'),
 (3, 'March'),
 (4, 'April'),
 (5, 'May'),
 (6, 'June'),
 (7, 'July'),
 (8, 'August'),
 (9, 'September'),
 (10, 'October'),
 (11, 'November'),
 (12, 'December'))


def parse_query(query):
    """
    Can parse "label1|label2" or
              "label.catergory.domid"
    """
    # sanitize
    if not re.match(QUERY_STRING_VALIDATOR, query):
        raise ValueError("Query string is not valid.")

    labels = query.split('|')
    query_list = []
    for label in labels:
        parts = label.split(':')
        if len(parts) == 1:
            query_list.append({'lbl': parts[0]})
        if len(parts) == 2:
            query_list.append({'lbl': parts[0], 'cat': parts[1]})
        if len(parts) == 3:
            query_list.append({'lbl': parts[0], 'cat': parts[1],
                'domid': parts[2]})
        if len(parts) > 3:
            ValueError("Too many dots in your query string.")
    return query_list


class Statistic(models.Model):

    label = models.CharField(max_length=250)
    category = models.CharField(max_length=30, default="None")
    dom_id = models.CharField(max_length=50)
    counter = models.IntegerField(default=0)
    day = models.DateField(auto_now_add=True)

    class Meta:
        verbose_name_plural = _('Statistics')
        ordering = ['-day']
        get_latest_by = "day"

    def __unicode__(self):
        return self.label


class Tracker(object):

    def __init__(self):
        # get the labels that are already used
        self.labels = cache.get('used_tracker_label_list', {})
        self.changed = False

    def append(self, label):
        if label['lbl'] not in self.labels.keys():
            self.labels[label['lbl']] = label
            self.changed = True
            cache.set('tracker_'+label['lbl'], 0)

    def flush_label(self, label):
        value = cache.get('tracker_'+label, 0)
        cache.set('tracker_'+label, 0)
        return value

    def incr_labels(self, query, save=True):
        labels = parse_query(query)
        for label in labels:
            self.append(label)
            try:
                cache.incr('tracker_'+label['lbl'])
            except ValueError:
                cache.set('tracker_'+label['lbl'], 0)
        if save:
            self.save()

    def save(self):
        if self.changed:
            cache.set('used_tracker_label_list', self.labels)

    def reset_cache(self):
        cache.delete('used_tracker_label_list')


def make_daily_report():
    tracker = Tracker()
    today = datetime.date.today()
    for label, values in tracker.labels.items():

        cat = values.get('cat', "None")
        dom_id = values.get('domid', "None")

        counter = tracker.flush_label(label)
        try:
            s = Statistic.objects.filter(label=label, day=today).latest()
            s.dom_id = dom_id
            s.cat = cat
            s.counter += counter
        except Statistic.DoesNotExist:
            s = Statistic(label=label, category=cat, dom_id=dom_id,
                counter=counter)

        s.save()


class CountryStatistic(models.Model):
    country = models.CharField(max_length=2,
            choices=countries.iso_name_choices)

    month = models.IntegerField(choices=MONTHS_CHOICES)
    year = models.IntegerField()
    data_serialized = SerializedObjectField()
    tag = models.CharField(max_length=50)

    class Meta:
        unique_together = ('country', 'month', 'year', 'tag')

    def total(self):
        return sum([obj[1] for obj in self.data_serialized])


COUNTRY_STATS_TIME=24 # in hours
def make_monthly_report_country(category='links', month=None, year=None,
        force=False):
    """ Counts for the month all the labels like country_domain
        category: the category to filter.
    """
    today = datetime.datetime.today()
    month = month or today.month
    year = year or  today.year

    data = CountryStatistic.objects.filter(month=month, year=year,
             tag=category)

    if force or not data:
        countries = [x[0] for x in settings.COUNTRY_PROFILES]
        s = Statistic.objects.filter(category=category)
        queries = s.filter(day__month=month, day__year=year)
        for country in countries:
            country_q = queries.filter(label__startswith=country + '_')
            sites = dict((obj['label'].split('_')[1], 0) for obj in country_q.values('label'))
            for site in sites.keys():
                # Sum all days
                sites[site] = country_q.filter(label__iregex=r'%s_%s' % (country,
                    site)).aggregate(Sum('counter'))['counter__sum']
            if sites:
                obj, created = CountryStatistic.objects.get_or_create(country=country, month=month,
                                year=year, tag=category)
                obj.data_serialized = sorted(sites.iteritems(), key=operator.itemgetter(1), reverse=True)
                obj.save()
            
        data = CountryStatistic.objects.filter(month=month, year=year,
             tag=category)

    return data 
