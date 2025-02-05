web: gunicorn app.bot_core:app
worker: python -m apscheduler executors.pool --url $DATABASE_URL