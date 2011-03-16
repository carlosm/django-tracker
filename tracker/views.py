from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.core import cache
import datetime
from tracker.models import Tracker, make_daily_report, Statistic, make_monthly_report_country
from django.contrib.admin.views.decorators import staff_member_required
import cjson

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

@staff_memeber_required
def monthly(request):
    month = int(request.GET.get('month', False))
    year = int(request.GET.get('year', False))
    report = make_monthly_report_country(month=month, year=year)
    return render_to_response('monthly.html', {'report':report})
