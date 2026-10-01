from django.core.management.base import BaseCommand
from restaurants.models import DiningTable, MenuItem, Offer


class Command(BaseCommand):
    help = "Add sample food-stall menu items with illustrative photos."

    def handle(self, *args, **options):
        items = [
            {
                "name": "Street Samosa",
                "description": "Crisp, golden pastry with a warmly spiced potato filling.",
                "category": "Snacks",
                "price": "25.00",
                "is_vegetarian": True,
                "is_bestseller": True,
                "spice_level": 1,
                "preparation_minutes": 8,
                "rating": "4.8",
                "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e5/Samosa.jpg/900px-Samosa.jpg",
            },
            {
                "name": "Masala Chai",
                "description": "A comforting cup of tea brewed with milk and warming spices.",
                "category": "Drinks",
                "price": "20.00",
                "is_vegetarian": True,
                "is_bestseller": False,
                "spice_level": 0,
                "preparation_minutes": 5,
                "rating": "4.9",
                "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/cb/A_cup_of_chai.JPG/900px-A_cup_of_chai.JPG",
            },
            {
                "name": "Avarebele Dose",
                "description": "A Bangalore food-street dosa made with seasonal hyacinth beans.",
                "category": "Fresh from the griddle",
                "price": "80.00",
                "is_vegetarian": True,
                "is_bestseller": True,
                "spice_level": 1,
                "preparation_minutes": 18,
                "rating": "4.8",
                "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c3/Avarebele_Dose_-_VV_Puram_Food_Street%2C_Bangalore_-_Karnataka_-_PXL5960.jpg/900px-Avarebele_Dose_-_VV_Puram_Food_Street%2C_Bangalore_-_Karnataka_-_PXL5960.jpg",
            },
        ]
        created = 0
        for item in items:
            _, was_created = MenuItem.objects.update_or_create(name=item["name"], defaults=item)
            created += int(was_created)
        for number, capacity in [("01", 2), ("02", 2), ("04", 4), ("05", 4), ("06", 6)]:
            DiningTable.objects.get_or_create(number=number, defaults={"capacity": capacity})
        Offer.objects.get_or_create(code="WELCOME10", defaults={
            "title": "A warm welcome", "description": "Take 10% off your first order.",
            "discount_percent": 10, "minimum_order": "199.00", "is_active": True,
        })
        self.stdout.write(self.style.SUCCESS(f"Ready: {len(items)} sample dishes, sample tables and WELCOME10. Replace demo details before serving customers."))
