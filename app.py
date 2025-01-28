from flask import Flask, render_template, request, jsonify, flash, redirect, url_for, send_file, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
import csv
import io
import os
from forms import MemberForm, LoginForm, COUNTRY_DATA
from urllib.parse import quote, unquote
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.utils import secure_filename

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
    IDDocument = db.Column(db.String(255))  # Store the file path
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

# Create upload folder if it doesn't exist
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Configure allowed extensions
ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def load_valid_ids():
    try:
        with open('idnumbers.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def validate_id_number(id_number):
    """Validate ID number against idnumbers.json"""
    valid_ids = load_valid_ids()
    return id_number in valid_ids

@app.route('/', methods=['GET', 'POST'])
def index():
    form = MemberForm()
    if request.method == 'POST':
        id_number = request.form.get('IDNumber', '').strip()
        if id_number:
            valid_ids = load_valid_ids()
            if id_number in valid_ids:
                return redirect(url_for('edit_member', id_number=id_number))
            else:
                flash('Invalid PMEC ID number. Please enter a valid ID.', 'error')
                return redirect(url_for('index'))
        else:
            flash('Please enter your PMEC ID number.', 'error')
            return redirect(url_for('index'))
    
    # Clear form on GET request
    form.IDNumber.data = ''
    return render_template('index.html', form=form)

@app.route('/edit_member/<id_number>', methods=['GET', 'POST'])
def edit_member(id_number):
    try:
        # Validate ID number again for security
        valid_ids = load_valid_ids()
        if id_number not in valid_ids:
            flash('Invalid PMEC ID number.', 'error')
            return redirect(url_for('index'))

        # Load existing member data if any
        try:
            with open('members.json', 'r') as f:
                members = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            members = {}

        form = MemberForm()
        
        if request.method == 'POST':
            if form.validate_on_submit():
                # Process form data and save
                member_data = {
                    'IDNumber': id_number,
                    'FirstName': form.FirstName.data,
                    'MiddleName': form.MiddleName.data,
                    'LastName': form.LastName.data,
                    'Gender': form.Gender.data,
                    'Email': form.Email.data,
                    'DateofBirth': form.DateofBirth.data,
                    'MobileNo': form.MobileNo.data,
                    'IDType': form.IDType.data,
                    'Nationality': form.Nationality.data,
                    'MembershipCategory': form.MembershipCategory.data,
                    'Address': form.Address.data,
                    'City': form.City.data,
                    'MonthlyDeduction': form.MonthlyDeduction.data
                }

                # Handle file upload
                if form.IDDocument.data:
                    file = form.IDDocument.data
                    if file and allowed_file(file.filename):
                        filename = secure_filename(f"{id_number}_{file.filename}")
                        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                        member_data['IDDocument'] = filename

                # Save to members.json
                members[id_number] = member_data
                with open('members.json', 'w') as f:
                    json.dump(members, f, indent=4)

                flash('Your information has been saved successfully!', 'success')
                return redirect(url_for('index'))
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        flash(f'{error}', 'error')

        # For GET request, populate form with existing data
        if id_number in members:
            member = members[id_number]
            for field in form._fields:
                if field in member:
                    getattr(form, field).data = member[field]

        return render_template('edit.html', form=form, id_number=id_number)
    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('backoffice'))
        
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash('Logged in successfully.', 'success')
            return redirect(url_for('backoffice'))
        else:
            flash('Invalid username or password.', 'error')
            
    return render_template('login.html', form=form)

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

@app.route('/view_document/<path:id_number>')
@login_required
def view_document(id_number):
    """View uploaded ID document"""
    try:
        decoded_id = unquote(id_number)
        member = Member.query.filter_by(IDNumber=decoded_id).first()
        
        if not member or not member.IDDocument:
            return jsonify({'error': 'Document not found'}), 404
            
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], member.IDDocument)
        if not os.path.exists(file_path):
            return jsonify({'error': 'Document file not found'}), 404
            
        return send_file(
            file_path,
            mimetype='application/pdf',
            as_attachment=False,
            download_name=f'document_{member.IDNumber}.pdf'
        )
    except Exception as e:
        print(f"Error serving file: {str(e)}")
        return jsonify({'error': 'Error accessing document'}), 500

# Make sure init_db() is called when the app starts
with app.app_context():
    init_db()

if __name__ == '__main__':
    app.run(debug=True)
