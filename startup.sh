#!/usr/bin/env bash
set -e

echo "=== Migrations ==="
python manage.py migrate --noinput

echo "=== Superuser admin (si absent) ==="
python manage.py shell << 'EOF'
from django.contrib.auth.models import User
import os
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser(
        username=os.environ.get('ADMIN_USERNAME', 'admin'),
        email=os.environ.get('ADMIN_EMAIL_ADDR', 'kaluunexpresse@gmail.com'),
        password=os.environ.get('ADMIN_PASSWORD', 'Kaluun@2024!')
    )
    print("Superuser créé")
else:
    print("Superuser existe déjà")
EOF

echo "=== Chargement des données initiales (si table vide) ==="
python manage.py shell << 'EOF'
from store.models import Product
if Product.objects.count() == 0:
    import subprocess
    subprocess.run(['python', 'manage.py', 'loaddata', 'store/fixtures/initial_data.json'], check=True)
    print("Produits chargés")
else:
    print("Produits déjà présents")
EOF

python manage.py shell << 'EOF'
from blog.models import Post
if Post.objects.count() == 0:
    import subprocess
    subprocess.run(['python', 'manage.py', 'loaddata', 'blog/fixtures/initial_posts.json'], check=True)
    print("Articles blog chargés")
else:
    print("Articles déjà présents")
EOF

echo "=== Démarrage Gunicorn ==="
exec gunicorn kaluun.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120
