# ===== seed_data.py =====
from sqlmodel import Session, select
from database import engine
from models import User, Package, UserRole, Language
from auth import get_password_hash
import json

def create_sample_data():
    """Create sample data for testing"""
    with Session(engine) as session:
        # Create admin user
        admin_exists = session.exec(
            select(User).where(User.email == "admin@dubaitravel.com")
        ).first()
        
        if not admin_exists:
            admin_user = User(
                name="Dubai Travel Admin",
                email="admin@dubaitravel.com",
                password_hash=get_password_hash("admin123"),
                role=UserRole.ADMIN,
                language=Language.EN,
                is_active=True,
                email_verified=True
            )
            session.add(admin_user)
        
def get_sample_packages():
    return [
        {
            "title_en": "Dubai City Tour",
            "title_ar": "جولة مدينة دبي",
            "description_en": "Explore the magnificent city of Dubai with our comprehensive city tour. Visit iconic landmarks including Burj Khalifa, Dubai Mall, and traditional souks.",
            "description_ar": "استكشف مدينة دبي الرائعة مع جولتنا الشاملة في المدينة. قم بزيارة المعالم الشهيرة بما في ذلك برج خليفة ودبي مول والأسواق التقليدية.",
            "price": 299.0,
            "duration": "8 hours",
            "max_travelers": 30,
            "min_travelers": 1,
            "includes_en": "Transportation, Guide, Lunch, Entry tickets",
            "includes_ar": "النقل، المرشد، الغداء، تذاكر الدخول",
            "excludes_en": "Personal expenses, Beverages",
            "excludes_ar": "المصاريف الشخصية، المشروبات",
            "featured": True,
            "availability": 50
        },
        {
            "title_en": "Desert Safari Adventure",
            "title_ar": "مغامرة سفاري الصحراء",
            "description_en": "Experience the thrill of desert safari with dune bashing, camel riding, and traditional BBQ dinner under the stars.",
            "description_ar": "اختبر إثارة سفاري الصحراء مع التزلج على الكثبان الرملية وركوب الجمال وعشاء الشواء التقليدي تحت النجوم.",
            "price": 199.0,
            "duration": "6 hours",
            "max_travelers": 40,
            "min_travelers": 2,
            "includes_en": "4WD Transportation, BBQ Dinner, Entertainment, Camel Ride",
            "includes_ar": "النقل بسيارة الدفع الرباعي، عشاء الشواء، الترفيه، ركوب الجمال",
            "excludes_en": "Alcoholic beverages, Quad biking",
            "excludes_ar": "المشروبات الكحولية، دراجات الكواد",
            "featured": True,
            "availability": 60
        },
        {
            "title_en": "Abu Dhabi Full Day Tour",
            "title_ar": "جولة أبوظبي يوم كامل",
            "description_en": "Discover the capital of UAE with visits to Sheikh Zayed Grand Mosque, Emirates Palace, and Louvre Abu Dhabi.",
            "description_ar": "اكتشف عاصمة دولة الإمارات مع زيارات لمسجد الشيخ زايد الكبير وقصر الإمارات ومتحف اللوفر أبوظبي.",
            "price": 349.0,
            "duration": "10 hours",
            "max_travelers": 25,
            "min_travelers": 2,
            "includes_en": "Transportation, Guide, Entry tickets, Lunch",
            "includes_ar": "النقل، المرشد، تذاكر الدخول، الغداء",
            "excludes_en": "Personal expenses, Beverages",
            "excludes_ar": "المصاريف الشخصية، المشروبات",
            "featured": False,
            "availability": 40
        }
    ]

def create_sample_data():
    """Create sample data for testing"""
    with Session(engine) as session:
        # Create admin user
        admin_exists = session.exec(
            select(User).where(User.email == "admin@dubaitravel.com")
        ).first()
        
        if not admin_exists:
            admin_user = User(
                name="Dubai Travel Admin",
                email="admin@dubaitravel.com",
                password_hash=get_password_hash("admin123"),
                role=UserRole.ADMIN,
                language=Language.EN,
                is_active=True,
                email_verified=True
            )
            session.add(admin_user)

        # Create sample packages
        sample_packages = get_sample_packages()
        for pkg in sample_packages:
            exists = session.exec(
                select(Package).where(Package.title_en == pkg["title_en"])
            ).first()
            if not exists:
                package = Package(**pkg)
                session.add(package)

        session.commit()

