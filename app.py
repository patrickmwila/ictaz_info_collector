from flask import Flask, render_template, request, jsonify, flash, redirect, url_for, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
import csv
import io
import os
from forms import MemberForm, COUNTRY_DATA
from urllib.parse import quote, unquote
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this to a secure secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///members.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Member(db.Model):
    __tablename__ = 'Members'
    
    id = db.Column(db.Integer, primary_key=True)
    FirstName = db.Column(db.String(100))
    MiddleName = db.Column(db.String(100))
    LastName = db.Column(db.String(100))
    Gender = db.Column(db.String(10))
    Email = db.Column(db.String(120))
    DateofBirth = db.Column(db.String(20))
    MobileNo = db.Column(db.String(20))
    IDNumber = db.Column(db.String(20), unique=True, nullable=False)
    IDType = db.Column(db.String(20))
    Nationality = db.Column(db.String(100))
    MembershipCategory = db.Column(db.String(50))
    Address = db.Column(db.String(200))
    CountryCode = db.Column(db.String(2))
    City = db.Column(db.String(100))
    MonthlyDeduction = db.Column(db.Float)

def init_db():
    with app.app_context():
        db.create_all()
        
        # Create admin user if not exists
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin')
            admin.set_password('echoroot')
            db.session.add(admin)
        
        # Read ID numbers from JSON file
        try:
            with open('idnumbers.json', 'r') as file:
                id_data = json.load(file)
                id_numbers = id_data.get('IDNumbers', [])
                
                # Create initial member records
                for id_number in id_numbers:
                    if not Member.query.filter_by(IDNumber=id_number).first():
                        member = Member(IDNumber=id_number)
                        db.session.add(member)
                
            db.session.commit()
        except FileNotFoundError:
            print("Warning: idnumbers.json not found. No initial members created.")
        except json.JSONDecodeError:
            print("Warning: Invalid JSON format in idnumbers.json")
        except Exception as e:
            print(f"Error reading idnumbers.json: {str(e)}")

@app.route('/', methods=['GET', 'POST'])
def index():
    form = MemberForm()
    
    if request.method == 'POST':
        if not form.IDNumber.data:
            flash('Please enter an ID Number.', 'warning')
            return render_template('index.html', form=form)
            
        id_number = form.IDNumber.data.strip()
        
        # Validate NRC format (e.g., 243095/64/1)
        import re
        if not re.match(r'^\d{6}/\d{2}/\d{1}$', id_number):
            flash('Invalid ID Number format. Please use the format: XXXXXX/XX/X (e.g., 243095/64/1)', 'error')
            return render_template('index.html', form=form)
        
        # Check if we already have a record
        member = Member.query.filter_by(IDNumber=id_number).first()
        
        if member and member.FirstName:  # If member has already submitted details
            flash('Your details have been retrieved successfully.', 'success')
            return render_template('details.html', member=member)
        else:
            # URL encode the ID number for the redirect
            encoded_id = quote(id_number)
            return redirect(url_for('edit_member', id_number=encoded_id))
            
    return render_template('index.html', form=form)

@app.route('/edit_member/<path:id_number>', methods=['GET', 'POST'])
def edit_member(id_number):
    decoded_id = unquote(id_number)
    member = Member.query.filter_by(IDNumber=decoded_id).first()
    
    if not member:
        member = Member(IDNumber=decoded_id)
        db.session.add(member)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while creating your record. Please try again.', 'error')
            return redirect(url_for('index'))
    
    form = MemberForm(obj=member)
    
    # Update city choices based on nationality
    if member.Nationality:
        cities = COUNTRY_DATA.get(member.Nationality, {}).get('cities', [])
        form.City.choices = [('', 'Select City')] + [(city, city) for city in cities]
    
    if request.method == 'POST':
        # Update city choices based on form data
        nationality = request.form.get('Nationality')
        if nationality:
            cities = COUNTRY_DATA.get(nationality, {}).get('cities', [])
            form.City.choices = [('', 'Select City')] + [(city, city) for city in cities]
    
    if form.validate_on_submit():
        form.populate_obj(member)
        
        # Get country code based on nationality
        country_data = COUNTRY_DATA.get(member.Nationality, {})
        member.CountryCode = country_data.get('code', '')
        
        try:
            db.session.commit()
            flash('Your information has been updated successfully!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating your information. Please try again.', 'error')
            print(f"Error: {str(e)}")
            
    return render_template('edit.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully.', 'success')
            return redirect(url_for('backoffice'))
        else:
            flash('Invalid username or password.', 'error')
            
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('index'))

@app.route('/backoffice')
@login_required
def backoffice():
    filter_type = request.args.get('filter', 'all')
    
    # Get counts for each category
    all_members = Member.query.all()
    updated_members = Member.query.filter(Member.FirstName.isnot(None)).all()
    not_updated_members = Member.query.filter(Member.FirstName.is_(None)).all()
    
    all_count = len(all_members)
    updated_count = len(updated_members)
    not_updated_count = len(not_updated_members)
    
    # Filter members based on selection
    if filter_type == 'updated':
        members = updated_members
    elif filter_type == 'not_updated':
        members = not_updated_members
    else:
        members = all_members
    
    return render_template('backoffice.html', 
                         members=members,
                         current_filter=filter_type,
                         all_count=all_count,
                         updated_count=updated_count,
                         not_updated_count=not_updated_count)

@app.route('/export')
@login_required
def export_csv():
    try:
        si = io.StringIO()
        cw = csv.writer(si)
        
        # Write headers
        headers = ['FirstName', 'MiddleName', 'LastName', 'Gender', 'Email', 
                  'DateofBirth', 'MobileNo', 'IDNumber', 'IDType', 'Nationality', 
                  'MembershipCategory', 'Address', 'CountryCode', 'City', 'MonthlyDeduction']
        cw.writerow(headers)
        
        # Write data
        members = Member.query.all()
        for member in members:
            cw.writerow([
                member.FirstName, member.MiddleName, member.LastName,
                member.Gender, member.Email, member.DateofBirth,
                member.MobileNo, member.IDNumber, member.IDType,
                member.Nationality, member.MembershipCategory,
                member.Address, member.CountryCode, member.City, member.MonthlyDeduction
            ])
        
        output = si.getvalue()
        si.close()
        
        return send_file(
            io.BytesIO(output.encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name='members.csv'
        )
    except Exception as e:
        flash('An error occurred while exporting the data. Please try again.', 'error')
        return redirect(url_for('index'))

@app.route('/get_cities/<country>')
def get_cities(country):
    """Get cities for a given country"""
    cities = COUNTRY_DATA.get(country, {}).get('cities', [])
    return jsonify(cities)

@app.route('/get_country_code/<country>')
def get_country_code(country):
    """Get country code for a given country"""
    code = COUNTRY_DATA.get(country, {}).get('code', '')
    return jsonify(code)

@app.route('/view_member_details/<path:id_number>')
@login_required
def view_member_details(id_number):
    """View member details from backoffice"""
    decoded_id = unquote(id_number)
    member = Member.query.filter_by(IDNumber=decoded_id).first()
    
    if not member:
        flash('Member not found.', 'error')
        return redirect(url_for('backoffice'))
        
    return render_template('details.html', member=member, is_admin=True)

# Make sure init_db() is called when the app starts
with app.app_context():
    init_db()

if __name__ == '__main__':
    app.run(debug=True)
