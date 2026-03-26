from django.core.management.base import BaseCommand
from django.db.models import Q

from crawler.crawl_runner import finish_crawl
from crawler.models import Crawl


class Command(BaseCommand):
    def handle(self, *args, **options):
        for crawl in Crawl.objects.filter(
            Q(status="running") | Q(status="finished", wacz_archive__isnull=True)
        ):
            finish_crawl(crawl)
