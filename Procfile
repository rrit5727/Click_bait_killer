release: python init_db.py
web: gunicorn app:app
worker: celery -A celery_config worker --loglevel=info
release: python -m spacy download en_core_web_sm