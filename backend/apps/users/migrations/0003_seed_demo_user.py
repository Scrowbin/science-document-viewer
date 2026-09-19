from django.db import migrations
from django.contrib.auth.hashers import make_password

def seed_demo_users(apps, schema_editor):
    User = apps.get_model('users', 'User')
    if not User.objects.filter(email='sarah.jenkins@stanford.edu').exists():
        User.objects.create(
            username='sarah_jenkins',
            email='sarah.jenkins@stanford.edu',
            first_name='Sarah',
            last_name='Jenkins',
            password=make_password('Password123!'),
            is_active=True,
        )

    if not User.objects.filter(email='demo@research.org').exists():
        User.objects.create(
            username='demo',
            email='demo@research.org',
            first_name='Alex',
            last_name='Morgan',
            password=make_password('Password123!'),
            is_active=True,
        )

def reverse_seed(apps, schema_editor):
    pass

class Migration(migrations.Migration):
    dependencies = [
        ('users', '0002_remove_user_created_at'),
    ]

    operations = [
        migrations.RunPython(seed_demo_users, reverse_seed),
    ]
