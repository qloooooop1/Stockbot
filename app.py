import os  # Add this line to import the os module
from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run()