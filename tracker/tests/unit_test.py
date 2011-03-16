import django
from django.conf import settings
from tracker.models import parse_query, Tracker
from tracker.models import Statistic, make_daily_report
from tracker.models import make_monthly_report_country
from django.test import TestCase

import datetime

class UnitTestCase(TestCase):

    def test_query_string(self):

        query = "label1"
        self.assertEqual(parse_query(query), [{'lbl': 'label1'}])
        query = "label1|label2"
        self.assertEqual(parse_query(query), [{'lbl': 'label1'},
            {'lbl': 'label2'}])

        query = "label1:cat|label2"
        self.assertEqual(parse_query(query), [{'lbl': 'label1', 'cat': 'cat'},
            {'lbl': 'label2'}])

        query = "label1:cat:ele1|label2"
        self.assertEqual(parse_query(query),
            [{'lbl': 'label1', 'cat': 'cat', 'domid': 'ele1'},
            {'lbl': 'label2'}])

    def test_traker(self):

        tracker = Tracker()

        tracker.incr_labels('label1')
        self.assertEqual(tracker.labels, {'label1': {'lbl': 'label1'}})
        tracker.incr_labels('label1')
        self.assertEqual(tracker.flush_label('label1'), 2)
        self.assertEqual(tracker.flush_label('label1'), 0)
        tracker.save()

        tracker = Tracker()
        self.assertEqual(tracker.labels, {'label1': {'lbl': 'label1'}})
        tracker.reset_cache()

    def test_report(self):

        tracker = Tracker()
        tracker.incr_labels('label1:cat1:dom1')
        tracker.incr_labels('label1:cat1:dom1')

        self.assertEqual(Statistic.objects.count(), 0)

        make_daily_report()

        self.assertEqual(tracker.flush_label('label1'), 0)

        self.assertEqual(Statistic.objects.count(), 1)

        stat = Statistic.objects.all()[0]
        self.assertEqual(stat.counter, 2)
        self.assertEqual(stat.category, 'cat1')
        self.assertEqual(stat.dom_id, 'dom1')

        tracker.incr_labels('label1:cat1:dom1')
        tracker.incr_labels('label1:cat1:dom1')

        stat = Statistic.objects.all()[0]
        self.assertEqual(stat.counter, 2)

        make_daily_report()

        stat = Statistic.objects.all()[0]
        self.assertEqual(stat.counter, 4)

        tracker.reset_cache()

    def test_montlyreport(self):
        tracker = Tracker()
        def add_static(labels, **kwargs):
            for label in parse_query(labels):
                s = Statistic(label=label.get('lbl'), category=label.get('cat'),
                        dom_id=label.get('domid', ''), **kwargs)

                s.save()
        add_static("us_link1.com:links|es_link2.com:links|us_link2.com:links",
                counter=5)

        add_static("us_link1.com:links|es_link4.com:links|us_link3.com:links",
                counter=10)

        report = make_monthly_report_country()
        def ListEqual(list1, list2):
            if len(list1) != len(list2):
                return False
            for ele in list1:
                if ele not in list2:
                    return False
            return True
        self.assertTrue(ListEqual(report['us'].keys(), ['link1.com', 'link2.com',
            'link3.com']))
        self.assertTrue(ListEqual(report['es'].keys(), ['link4.com',
            'link2.com']))
        self.assertEqual(report['us']['link1.com'], 15)
        self.assertEqual(report['es']['link2.com'], 5)
        self.assertEqual(report['us']['link3.com'], 10)
        self.assertEqual(report['fr'], dict())
