web: gunicorn app.bot_core:app --preload
worker: python -m apscheduler executors.pool --url $DATABASE_URL