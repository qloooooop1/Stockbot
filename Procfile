web: gunicorn --preload app.bot_core:bot.run
worker: python -m apscheduler executors --url $DATABASE_URL
