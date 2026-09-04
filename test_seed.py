import os
os.environ['FLASK_ENV'] = 'development'
from app import app
with app.app_context():
    from extensions import db
    db.drop_all()
    db.create_all()
    print("Tables created")
    from models import JobRole
    print(f"JobRoles before seed: {JobRole.query.count()}")
    
# Now run the create_tables which should seed
import sys
sys.path.insert(0, '.')
from app import create_tables
create_tables()

# Check again
from app import app
with app.app_context():
    from models import JobRole, SkillArea, Topic, Lab
    print(f"JobRoles after seed: {JobRole.query.count()}")
    print(f"SkillAreas: {SkillArea.query.count()}")
    print(f"Topics: {Topic.query.count()}")
    print(f"Labs: {Lab.query.count()}")
    for r in JobRole.query.all():
        print(f"  - {r.name} ({r.slug})")