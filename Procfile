web: gunicorn --preload app.bot_core:app
worker: python -m apscheduler executors --url $DATABASE_URL