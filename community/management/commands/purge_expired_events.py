from django.core.management.base import BaseCommand

from community.models import Event


class Command(BaseCommand):
    help = "Delete events whose date/time is in the past"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show how many events would be deleted without deleting them.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        expired_qs = Event.objects.expired()
        expired_count = expired_qs.count()

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"Dry run: {expired_count} expired event(s) would be deleted."
                )
            )
            return

        deleted_count, _ = expired_qs.delete()
        self.stdout.write(
            self.style.SUCCESS(f"Deleted {deleted_count} expired event(s).")
        )
