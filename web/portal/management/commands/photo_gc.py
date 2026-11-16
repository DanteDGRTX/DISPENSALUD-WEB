from django.core.management.base import BaseCommand
from portal.private_photos.store import PhotoStore

class Command(BaseCommand):
    help = "Detecta hasta 100 fotos huérfanas de más de una hora; dry-run por defecto."
    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true")
    def handle(self, *args, **options):
        store = PhotoStore()
        try:
            self.stdout.write(str(store.cleanup(apply=options["apply"])) + " huérfanos antiguos; " + ("eliminados" if options["apply"] else "sin borrar"))
        finally:
            store.close()
