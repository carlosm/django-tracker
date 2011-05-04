from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.core import cache
import datetime
from tracker.models import Tracker, make_daily_report, Statistic, make_monthly_report_country, CountryStatistic

from django.contrib.admin.views.decorators import staff_member_required
import cjson
import operator
import datetime

def test(request):
    return render_to_response('test.html', {})

def track(request):
    labels = request.GET.get('labels', False)
    if not labels:
        return HttpResponse("syntax: ?labels=label1|label2")
    tracker = Tracker()
    tracker.incr_labels(str(labels))
    return HttpResponse("ok")

def report(request):
    make_daily_report()
    return HttpResponse("ok")

@staff_member_required
def get_stats(request):
    today = datetime.date.today()
    dom_ids = request.GET.get('dom_ids', "").split('|')
    statistics = Statistic.objects.filter(dom_id__in=dom_ids, day=today)
    stat_list = []
    for stat in statistics:
        stat_list.append([stat.dom_id, stat.counter, stat.label])

    return HttpResponse(cjson.encode(stat_list))

@staff_member_required
def monthly(request):
    today = datetime.datetime.today() 
    # ?month ?year
    month = int(request.GET.get('month', today.month))
    year = int(request.GET.get('year', today.year))

    # ?force would generate the statistics from that period
    force = request.GET.has_key('force')
    category = request.GET.get("tag", 'links')

    # Call the actuall procedure to get the report
    data = make_monthly_report_country(month=month, year=year, force=force,
            category=category)

    return render_to_response('monthly.html', {'report': data})

def crazy_function(month=today.month, category='links', year=today.year):
    data = make_monthly_report_country(month=month, year=year, category=category)
    total = 0
    for country in data:
        if len(country.data_serialized) > total:
            total = len(country.data_serialized)

    #header
    total += 1

    final = ["" for a in range(total)]
    for country in data:
        if country.total() < 25:
            continue
        final[0] += "%s,%s," % (country.total(), country.country)
        for nline in range(len(country.data_serialized)):
            line = "%s,%s," % (country.data_serialized[nline][1], country.data_serialized[nline][0])
            try:
                final[nline+1] += line
            except IndexError:
                final.append(line)
        for n in range(nline+2, total):
            final[n] += ",,"
    f = open("/tmp/%s-%s.%s.csv" % (category, month, year), 'w')
    f.write("\n".join(final));f.close()

