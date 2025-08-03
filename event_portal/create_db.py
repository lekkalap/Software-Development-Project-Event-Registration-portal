from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash

# Step 1: Initialize the app context
app = create_app()

with app.app_context():
    # Step 2: Drop all tables (optional for dev refresh)
    db.drop_all()

    # Step 3: Create all tables
    db.create_all()
    print("✅ Database and tables created.")

    # Step 4: Seed default admin user
    admin_email = 'admin@event.com'
    existing_admin = User.query.filter_by(email=admin_email).first()

    if not existing_admin:
        admin = User(
            name='Admin',
            email=admin_email,
            password=generate_password_hash('admin123', method='pbkdf2:sha256'),
            role='admin'
        )
        db.session.add(admin)
        db.session.commit()
        print(f"✅ Admin user created: {admin_email} / admin123")
    else:
        print("⚠️ Admin user already exists.")
