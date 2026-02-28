from database import SessionLocal
from models import Customer, RoleEnum
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_admin():
    db = SessionLocal()
    admin_user = db.query(Customer).filter(Customer.username == 'sysadmin').first()
    if not admin_user:
        hashed_password = pwd_context.hash('admin123')
        new_admin = Customer(username='sysadmin', password_hash=hashed_password, role=RoleEnum.admin)
        db.add(new_admin)
        db.commit()
        print("Admin user 'sysadmin' created with password 'admin123'")
    else:
        print("Admin user already exists.")
    db.close()

if __name__ == "__main__":
    create_admin()
