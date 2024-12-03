from flask import Blueprint, render_template, request, redirect, url_for
from utils.sleeper_api import get_user

home_bp = Blueprint('home', __name__)

@home_bp.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        username = request.form['username']
        user_data = get_user(username)
        if not user_data:
            return render_template('home.html', error="User not found.")
        return redirect(url_for('leagues.leagues', user_id=user_data['user_id']))
    return render_template('home.html')
