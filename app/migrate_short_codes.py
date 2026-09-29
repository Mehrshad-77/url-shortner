from app.database import SessionLocal
from app.models import URL
from app.services.url_service import generate_short_code


db = SessionLocal()

try:
    urls = db.query(URL).filter(URL.short_code.is_(None)).all()

    for url in urls:
        url.short_code = generate_short_code()
        print(f"{url.id} -> {url.short_code}")

    db.commit()

except Exception:
    db.rollback()
    raise

finally:
    db.close()