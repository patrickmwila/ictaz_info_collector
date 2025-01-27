from flask import Flask, render_template, request, jsonify, flash, redirect, url_for, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
import csv
import io
import os
from forms import MemberForm
from urllib.parse import quote, unquote

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///members.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Member(db.Model):
    __tablename__ = 'Members'
    
    FirstName = db.Column(db.String(100))
    MiddleName = db.Column(db.String(100))
    LastName = db.Column(db.String(100))
    Gender = db.Column(db.String(10))
    Email = db.Column(db.String(120))
    DateofBirth = db.Column(db.String(10))
    MobileNo = db.Column(db.String(15))
    IDNumber = db.Column(db.String(20), primary_key=True)
    IDType = db.Column(db.String(10))
    Nationality = db.Column(db.String(50), default='Zambian')
    MembershipCategory = db.Column(db.String(20))

def init_db():
    with app.app_context():
        db.create_all()
        # Load IDNumbers from JSON file
        if os.path.exists('idnumbers.json'):
            with open('idnumbers.json', 'r') as f:
                data = json.load(f)
                for id_number in data['IDNumbers']:
                    # Check if ID already exists
                    if not Member.query.filter_by(IDNumber=id_number).first():
                        member = Member(IDNumber=id_number)
                        db.session.add(member)
            db.session.commit()

@app.route('/', methods=['GET', 'POST'])
def index():
    form = MemberForm()
    if request.method == 'POST':
        if not form.IDNumber.data:
            flash('Please enter an ID Number.', 'warning')
            return render_template('index.html', form=form)
            
        id_number = form.IDNumber.data.strip()
        member = Member.query.filter_by(IDNumber=id_number).first()
        
        if not member:
            flash('ID Number not found in our records. Please contact support for assistance.', 'error')
            return render_template('index.html', form=form)
            
        if member.FirstName:  # If member has already submitted details
            flash('Your details have been retrieved successfully.', 'success')
            return render_template('details.html', member=member)
        else:
            # URL encode the ID number
            encoded_id = quote(id_number)
            return redirect(url_for('edit_member', id_number=encoded_id))
            
    return render_template('index.html', form=form)

@app.route('/member/<path:id_number>', methods=['GET', 'POST'])
def edit_member(id_number):
    # URL decode the ID number
    decoded_id = unquote(id_number)
    member = Member.query.filter_by(IDNumber=decoded_id).first()
    
    if not member:
        flash('ID Number not found in our records. Please contact support for assistance.', 'error')
        return redirect(url_for('index'))
        
    if member.FirstName:  # If member has already submitted details
        flash('Your details have already been submitted. Contact support if you need to make changes.', 'info')
        return render_template('details.html', member=member)
        
    form = MemberForm(obj=member)
    
    if form.validate_on_submit():
        form.populate_obj(member)
        db.session.commit()
        flash('Your information has been successfully saved! Please note that you cannot edit this information once submitted.', 'success')
        return redirect(url_for('index'))
    
    if form.errors:
        flash('Please correct the errors in the form before submitting.', 'warning')
        
    return render_template('edit.html', form=form, member=member)

@app.route('/export')
def export_csv():
    try:
        si = io.StringIO()
        cw = csv.writer(si)
        
        # Write headers
        headers = ['FirstName', 'MiddleName', 'LastName', 'Gender', 'Email', 
                  'DateofBirth', 'MobileNo', 'IDNumber', 'IDType', 'Nationality', 
                  'MembershipCategory']
        cw.writerow(headers)
        
        # Write data
        members = Member.query.all()
        for member in members:
            cw.writerow([
                member.FirstName, member.MiddleName, member.LastName,
                member.Gender, member.Email, member.DateofBirth,
                member.MobileNo, member.IDNumber, member.IDType,
                member.Nationality, member.MembershipCategory
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

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
