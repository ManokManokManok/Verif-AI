from django.core.management.base import BaseCommand

from src.infrastructure.mongodb.admin_repository import AdminRepository
from src.infrastructure.mongodb.analysis_repository import AnalysisResultRepository
from src.infrastructure.mongodb.connection import get_database_name, get_mongo_client


class Command(BaseCommand):
    help = (
        'Publish saved admin reviews for reports that were already resolved, '
        'so users see the admin-verified result. Use --dry-run to preview.'
    )

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='List changes without writing')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        client = get_mongo_client()
        db_name = get_database_name()
        admin_repo = AdminRepository(client, db_name)
        analysis_repo = AnalysisResultRepository(client, db_name)

        published = skipped_no_review = skipped_other = 0
        for report in admin_repo.reports_collection.find({'status': 'resolved'}):
            report_id = report.get('report_id')
            ref = report.get('analysis_ref_id') or report.get('analysis_id')
            if not ref:
                continue
            analysis = analysis_repo.get_by_ref_id(ref) or analysis_repo.get_by_id(ref)
            review = getattr(analysis, 'reviewed_result', None) if analysis else None
            if not review or review.get('report_id') != report_id:
                skipped_no_review += 1
                self.stdout.write(f'[no saved review] report {report_id} (analysis {ref})')
                continue
            if review.get('decision') not in ('confirmed_scam', 'confirmed_legitimate'):
                skipped_other += 1
                continue
            if review.get('is_published'):
                continue
            self.stdout.write(f'{"[dry-run] " if dry_run else ""}publish report {report_id} -> analysis {analysis.ref_id}')
            if not dry_run:
                analysis_repo.set_review_publication(analysis.ref_id, report_id, True)
            published += 1

        self.stdout.write(self.style.SUCCESS(
            f'Done. published={published}, no_saved_review={skipped_no_review}, non_verdict={skipped_other}'
        ))
