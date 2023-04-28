from app import create_app
import os

# create the app
app = create_app()

# set debug to False for production
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80)
