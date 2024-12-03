from flask import Flask
from routes.home import home_bp
from routes.leagues import leagues_bp
from routes.rosters import rosters_bp
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

def create_app():
    app = Flask(__name__)

    # Register blueprints
    app.register_blueprint(home_bp)
    app.register_blueprint(leagues_bp)
    app.register_blueprint(rosters_bp)

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
