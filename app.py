from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory, send_file
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
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create upload folder if it doesn't exist
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', os.path.join(BASE_DIR, 'static', 'uploads'))
MEMBERS_JSON = os.path.join(BASE_DIR, 'members.json')
BACKOFFICE_DIR = os.path.join(BASE_DIR, 'backoffice')
BACKOFFICE_CSV = os.path.join(BACKOFFICE_DIR, 'members.csv')


try:
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
except Exception as e:
    print(f"Error creating upload folder: {e}")

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')  # Change this to a secure secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///members.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Admin credentials from environment variables
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')

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
    HighestQualification = db.Column(db.String(100))
    QualificationDocument = db.Column(db.String(255))  # Store the file path

def init_db():
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Create admin user if not exists
        admin = User.query.filter_by(username=ADMIN_USERNAME).first()
        if not admin:
            admin = User(username=ADMIN_USERNAME)
            admin.set_password(ADMIN_PASSWORD)
            db.session.add(admin)
            db.session.commit()
            print("Admin user created successfully")
        
        # Read ID numbers from JSON file
        json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'idnumbers.json')
        try:
            with open(json_path, 'r') as file:
                id_data = json.load(file)
                id_numbers = id_data.get('IDNumbers', [])
                
                # Create initial member records
                for id_number in id_numbers:
                    if not Member.query.filter_by(IDNumber=id_number).first():
                        member = Member(IDNumber=id_number)
                        db.session.add(member)
                
            db.session.commit()
            print("Member records initialized")
        except Exception as e:
            print(f"Error initializing database: {str(e)}")
            db.session.rollback()

# Configure allowed extensions
ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def load_valid_ids():
    """Load valid IDs from idnumbers.json"""
    json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'idnumbers.json')
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
            return data.get('IDNumbers', [])  # Get the list of IDs from the nested structure
    except FileNotFoundError:
        print("Warning: idnumbers.json not found")
        return []
    except json.JSONDecodeError:
        print("Warning: idnumbers.json is not valid JSON")
        return []

def save_to_backoffice(member_data):
    """Save member data to backoffice CSV file"""
    try:
        # Create backoffice directory if it doesn't exist
        os.makedirs(BACKOFFICE_DIR, exist_ok=True)
        
        file_exists = os.path.isfile(BACKOFFICE_CSV)
        fieldnames = [
            'IDNumber', 'FirstName', 'MiddleName', 'LastName', 'Gender',
            'Email', 'DateofBirth', 'MobileNo', 'IDType', 'Nationality',
            'MembershipCategory', 'Address', 'City', 'MonthlyDeduction',
            'IDDocument', 'HighestQualification', 'QualificationDocument', 'SubmissionDate'
        ]

        # Add submission date to member data
        member_data['SubmissionDate'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        try:
            # Write to CSV with proper encoding
            with open(BACKOFFICE_CSV, mode='a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                
                # Write header if file doesn't exist
                if not file_exists:
                    writer.writeheader()
                
                writer.writerow(member_data)

            print(f"Successfully saved to backoffice: {member_data['IDNumber']}")
            return True
            
        except Exception as e:
            print(f"Error writing to CSV: {str(e)}")
            return False

    except Exception as e:
        print(f"Error saving to backoffice: {str(e)}")
        return False

    return render_template('index.html', form=form)


@app.route('/', methods=['GET', 'POST'])
def index():
    form = MemberForm()

    if request.method == 'POST':
        id_number = request.form.get('IDNumber', '').strip()

        if not id_number:
            return jsonify({
                'status': 'error',
                'title': 'Error',
                'message': 'Please enter your PMEC ID number.',
                'icon': 'error'
            }), 400

        # Load and check valid IDs
        valid_ids = load_valid_ids()

        if id_number in valid_ids:
            print(f"Valid ID found: {id_number}")

            # Check if member data exists
            try:
                if os.path.exists(MEMBERS_JSON):
                    with open(MEMBERS_JSON, 'r') as f:
                        members = json.load(f)
                        if id_number in members:
                            # Member exists, return success with view redirect
                            return jsonify({
                                'status': 'success',
                                'title': 'Success',
                                'message': 'Your information has been found in our records. Click okay to view your record.',
                                'icon': 'success',
                                'redirect': url_for('view_member', id_number=quote(id_number))
                            })

                # If we get here, either file doesn't exist or member not found
                return jsonify({
                    'status': 'success',
                    'title': 'Success',
                    'message': 'We found a match! Your ID Number was found in our records. Click OK to proceed.',
                    'icon': 'info',
                    'redirect': url_for('edit_member', id_number=quote(id_number))
                })
            except Exception as e:
                print(f"Error checking member status: {str(e)}")
                # Handle any file access or JSON parsing errors
                return jsonify({
                    'status': 'success',
                    'title': 'Success',
                    'message': 'We found a match! Your ID Number was found in our records. Click OK to proceed.',
                    'icon': 'info',
                    'redirect': url_for('edit_member', id_number=quote(id_number))
                })
        else:
            print(f"Invalid ID: {id_number}")
            return jsonify({
                'status': 'error',
                'title': 'Access Denied',
                'message': 'The provided ID number was not found in our records.',
                'icon': 'error'
            }), 400

    return render_template('index.html', form=form)

@app.route('/view_member/<path:id_number>')
def view_member(id_number):
    try:
        # Decode the ID number
        decoded_id = unquote(id_number)

        # Validate ID number again for security
        valid_ids = load_valid_ids()
        if decoded_id not in valid_ids:
            flash('Access Denied: Invalid PMEC ID number.', 'error')
            return redirect(url_for('index'))

        # Load member data
        try:
            if not os.path.exists(MEMBERS_JSON):
                flash('Member information not found.', 'error')
                return redirect(url_for('index'))

            with open(MEMBERS_JSON, 'r') as f:
                members = json.load(f)
                if decoded_id in members:
                    member = members[decoded_id]

                    # Add file existence checks for documents
                    if 'IDDocument' in member:
                        id_doc_path = os.path.join(UPLOAD_FOLDER, member['IDDocument'])
                        member['IDDocumentExists'] = os.path.exists(id_doc_path)

                    if 'QualificationDocument' in member:
                        qual_doc_path = os.path.join(UPLOAD_FOLDER, member['QualificationDocument'])
                        member['QualificationDocumentExists'] = os.path.exists(qual_doc_path)

                    return render_template('view_member.html', member=member)
                else:
                    flash('Member information not found.', 'error')
                    return redirect(url_for('index'))

        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in members.json")
            flash('Error reading member data. Please contact support.', 'error')
            return redirect(url_for('index'))
        except Exception as e:
            print(f"Error reading member data: {str(e)}")
            flash('Error accessing member information. Please try again later.', 'error')
            return redirect(url_for('index'))

    except Exception as e:
        print(f"Error in view_member: {str(e)}")
        flash('An unexpected error occurred. Please try again later.', 'error')
        return redirect(url_for('index'))


@app.route('/edit_member/<path:id_number>', methods=['GET', 'POST'])
def edit_member(id_number):
    try:
        decoded_id = unquote(id_number)

        # Create member-specific upload directory
        member_dir_name = decoded_id.replace('/', '_')
        member_upload_dir = os.path.join(UPLOAD_FOLDER, member_dir_name)
        try:
            os.makedirs(member_upload_dir, exist_ok=True)
        except Exception as e:
            print(f"Error creating member upload directory: {str(e)}")
            return jsonify({
                'status': 'error',
                'title': 'Error',
                'message': 'Could not create upload directory',
                'icon': 'error'
            }), 500

        # Validate ID number again for security
        valid_ids = load_valid_ids()
        if decoded_id not in valid_ids:
            return jsonify({
                'status': 'error',
                'title': 'Access Denied',
                'message': 'The provided ID number was not found in our records.',
                'icon': 'error'
            }), 400

        form = MemberForm()
        form.IDNumber.render_kw = {'readonly': True}
        form.IDNumber.data = decoded_id

        # Load existing data if available
        existing_data = None
        try:
            if os.path.exists(MEMBERS_JSON):
                with open(MEMBERS_JSON, 'r') as f:
                    members = json.load(f)
                    if decoded_id in members:
                        existing_data = members[decoded_id]
        except Exception as e:
            print(f"Error loading existing data: {str(e)}")

        if request.method == 'POST':
            if form.Nationality.data in COUNTRY_DATA:
                form.City.choices = [('', 'Select City')] + [(city, city) for city in COUNTRY_DATA[form.Nationality.data]['cities']]

            if form.validate():
                id_document = None
                qualification_document = None

                # Handle ID Document upload
                if form.IDDocument.data:
                    try:
                        filename = secure_filename(form.IDDocument.data.filename)
                        extension = os.path.splitext(filename)[1]
                        new_filename = f"{member_dir_name}{extension}"
                        file_path = os.path.join(member_upload_dir, new_filename)
                        form.IDDocument.data.save(file_path)
                        id_document = f"{member_dir_name}/{new_filename}"
                    except Exception as e:
                        print(f"Error saving ID document: {str(e)}")
                        return jsonify({
                            'status': 'error',
                            'title': 'Error',
                            'message': f'Could not save ID document: {str(e)}',
                            'icon': 'error'
                        }), 500

                # Handle Qualification Document upload
                if form.QualificationDocument.data:
                    try:
                        filename = secure_filename(form.QualificationDocument.data.filename)
                        extension = os.path.splitext(filename)[1]
                        new_filename = f"{member_dir_name}_qual{extension}"
                        file_path = os.path.join(member_upload_dir, new_filename)
                        form.QualificationDocument.data.save(file_path)
                        qualification_document = f"{member_dir_name}/{new_filename}"
                    except Exception as e:
                        print(f"Error saving qualification document: {str(e)}")
                        return jsonify({
                            'status': 'error',
                            'title': 'Error',
                            'message': f'Could not save qualification document: {str(e)}',
                            'icon': 'error'
                        }), 500

                # Prepare member data
                member_data = {
                    'FirstName': form.FirstName.data,
                    'MiddleName': form.MiddleName.data,
                    'LastName': form.LastName.data,
                    'Gender': form.Gender.data,
                    'Email': form.Email.data,
                    'DateofBirth': form.DateofBirth.data,
                    'MobileNo': form.MobileNo.data,
                    'IDNumber': decoded_id,
                    'IDType': form.IDType.data,
                    'Nationality': form.Nationality.data,
                    'MembershipCategory': form.MembershipCategory.data,
                    'HighestQualification': form.HighestQualification.data,
                    'City': form.City.data,
                    'Address': form.Address.data,
                    'MonthlyDeduction': form.MonthlyDeduction.data,
                    'UpdatedAt': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }

                if id_document:
                    member_data['IDDocument'] = id_document
                if qualification_document:
                    member_data['QualificationDocument'] = qualification_document

                # Save to members.json
                try:
                    if os.path.exists(MEMBERS_JSON):
                        with open(MEMBERS_JSON, 'r') as f:
                            members = json.load(f)
                    else:
                        members = {}
                        with open(MEMBERS_JSON, 'w') as f:
                            json.dump({}, f)

                    members[decoded_id] = member_data

                    with open(MEMBERS_JSON, 'w') as f:
                        json.dump(members, f, indent=2)
                        f.flush()
                        os.fsync(f.fileno())

                    print(f"Successfully saved to members.json: {decoded_id}")

                    # Prepare data for backoffice
                    backoffice_data = member_data.copy()
                    del backoffice_data['UpdatedAt']

                    # Save to backoffice
                    if save_to_backoffice(backoffice_data):
                        return jsonify({
                            'status': 'success',
                            'title': 'Success',
                            'message': 'Your information has been submitted successfully!',
                            'icon': 'success',
                            'redirect': url_for('view_member', id_number=quote(decoded_id))
                        })
                    else:
                        return jsonify({
                            'status': 'warning',
                            'title': 'Partial Success',
                            'message': 'Your information was saved but there was an issue updating the backoffice. Please contact support.',
                            'icon': 'warning',
                            'redirect': url_for('view_member', id_number=quote(decoded_id))
                        })

                except Exception as e:
                    print(f"Error saving to members.json: {str(e)}")
                    return jsonify({
                        'status': 'error',
                        'title': 'Error',
                        'message': f'Could not save member data: {str(e)}',
                        'icon': 'error'
                    }), 500
            else:
                errors = []
                for field, field_errors in form.errors.items():
                    errors.extend(field_errors)
                return jsonify({
                    'status': 'error',
                    'title': 'Validation Error',
                    'message': '\n'.join(errors),
                    'icon': 'error'
                }), 400

        # For GET request, populate form with existing data
        if existing_data:
            for field in form._fields:
                if field in existing_data and field != 'IDNumber':
                    getattr(form, field).data = existing_data[field]

            # Update city choices for existing data
            if existing_data.get('Nationality') in COUNTRY_DATA:
                form.City.choices = [('', 'Select City')] + [(city, city) for city in COUNTRY_DATA[existing_data['Nationality']]['cities']]

        return render_template('edit.html', form=form, existing_data=existing_data)

    except Exception as e:
        print(f"Error in edit_member: {str(e)}")
        return jsonify({
            'status': 'error',
            'title': 'Error',
            'message': str(e),
            'icon': 'error'
        }), 500


@app.route('/update_cities/<nationality>')
def update_cities(nationality):
    """AJAX endpoint to get cities for a nationality"""
    if nationality in COUNTRY_DATA:
        cities = COUNTRY_DATA[nationality]['cities']
        return jsonify({'cities': cities})
    return jsonify({'cities': []})

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
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

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

    try:
        # Load valid IDs from idnumbers.json
        valid_ids = load_valid_ids()

        # Load submitted member data from members.json using absolute path
        try:
            if not os.path.exists(MEMBERS_JSON):
                # Initialize empty members.json if it doesn't exist
                with open(MEMBERS_JSON, 'w') as f:
                    json.dump({}, f)
                submitted_members = {}
            else:
                with open(MEMBERS_JSON, 'r') as f:
                    submitted_members = json.load(f)
        except Exception as e:
            print(f"Error loading members.json: {str(e)}")
            submitted_members = {}

        # Create a list of all members with their update status
        all_members = []
        for id_number in valid_ids:
            member = submitted_members.get(id_number, {'IDNumber': id_number})
            # Ensure IDNumber is always present
            if 'IDNumber' not in member:
                member['IDNumber'] = id_number
            all_members.append(member)

        # Filter members based on selection
        if filter_type == 'updated':
            members = [m for m in all_members if m.get('FirstName')]
        elif filter_type == 'not_updated':
            members = [m for m in all_members if not m.get('FirstName')]
        else:
            members = all_members

        # Get counts
        all_count = len(all_members)
        updated_count = len([m for m in all_members if m.get('FirstName')])
        not_updated_count = all_count - updated_count

        return render_template('backoffice.html',
                            members=members,
                            current_filter=filter_type,
                            all_count=all_count,
                            updated_count=updated_count,
                            not_updated_count=not_updated_count)

    except Exception as e:
        print(f"Error in backoffice: {str(e)}")
        flash('Error loading member data', 'error')
        return render_template('backoffice.html',
                            members=[],
                            current_filter='all',
                            all_count=0,
                            updated_count=0,
                            not_updated_count=0)


@app.route('/view_member_details/<path:id_number>')
@login_required
def view_member_details(id_number):
    try:
        if not os.path.exists(MEMBERS_JSON):
            flash('Member information not found.', 'error')
            return redirect(url_for('backoffice'))

        with open(MEMBERS_JSON, 'r') as f:
            members = json.load(f)
            if id_number in members:
                member = members[id_number]
                # Add file existence checks
                if 'IDDocument' in member:
                    id_doc_path = os.path.join(UPLOAD_FOLDER, member['IDDocument'])
                    member['IDDocumentExists'] = os.path.exists(id_doc_path)
                if 'QualificationDocument' in member:
                    qual_doc_path = os.path.join(UPLOAD_FOLDER, member['QualificationDocument'])
                    member['QualificationDocumentExists'] = os.path.exists(qual_doc_path)
                return render_template('view_member.html', member=member)
            else:
                flash('Member has not submitted their information yet.', 'warning')
                return redirect(url_for('backoffice'))
    except Exception as e:
        print(f"Error loading member details: {str(e)}")
        flash('Error loading member details', 'error')
        return redirect(url_for('backoffice'))


@app.route('/view_document/<path:id_number>')
@login_required
def view_document(id_number):
    try:
        if not os.path.exists(MEMBERS_JSON):
            flash('Document not found', 'error')
            return redirect(url_for('backoffice'))

        with open(MEMBERS_JSON, 'r') as f:
            members = json.load(f)
            if id_number in members and members[id_number].get('IDDocument'):
                filename = members[id_number]['IDDocument']
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                if os.path.exists(file_path):
                    return send_from_directory(UPLOAD_FOLDER, filename)
            flash('Document not found', 'error')
            return redirect(url_for('backoffice'))
    except Exception as e:
        print(f"Error accessing document: {str(e)}")
        flash('Error accessing document', 'error')
        return redirect(url_for('backoffice'))


@app.route('/static/uploads/<path:filename>')
def uploaded_file(filename):
    # Split the filename into directory and actual filename
    member_dir, file = os.path.split(filename)
    return send_from_directory(os.path.join(app.config['UPLOAD_FOLDER'], member_dir), file)

@app.route('/export_csv')
@login_required
def export_csv():
    try:
        # Load valid IDs from idnumbers.json
        valid_ids = load_valid_ids()
        
        # Load submitted member data from members.json
        try:
            with open(MEMBERS_JSON, 'r') as f:
                members = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            members = {}
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['ID Number', 'First Name', 'Middle Name', 'Last Name', 'Gender', 
                        'Email', 'Date of Birth', 'Mobile No', 'ID Type', 'Nationality',
                        'Membership Category', 'Address', 'City', 'Monthly Deduction',
                        'ID Document', 'Status'])
        
        # Write member data for all valid IDs
        for id_number in valid_ids:
            data = members.get(id_number, {})
            writer.writerow([
                id_number,
                data.get('FirstName', ''),
                data.get('MiddleName', ''),
                data.get('LastName', ''),
                data.get('Gender', ''),
                data.get('Email', ''),
                data.get('DateofBirth', ''),
                data.get('MobileNo', ''),
                data.get('IDType', ''),
                data.get('Nationality', ''),
                data.get('MembershipCategory', ''),
                data.get('Address', ''),
                data.get('City', ''),
                data.get('MonthlyDeduction', ''),
                data.get('IDDocument', ''),
                'Updated' if data.get('FirstName') else 'Not Updated'
            ])
        
        # Prepare response
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'members_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )
        
    except Exception as e:
        print(f"Error in export_csv: {str(e)}")  # Debug print
        flash('Error exporting data', 'error')
        return redirect(url_for('backoffice'))

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

# Make sure init_db() is called when the app starts
with app.app_context():
    init_db()

if __name__ == '__main__':
    app.run(debug=True)
