from django.core.management.base import BaseCommand
from loans.tasks import ingest_excel_files

class Command(BaseCommand):
    help = 'Enqueue Celery task to ingest excel files into DB'

    def handle(self, *args, **options):
        result = ingest_excel_files.delay()
        self.stdout.write(self.style.SUCCESS(f'Enqueued ingest task: {result.id}'))
