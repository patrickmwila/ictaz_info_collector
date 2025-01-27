from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, SelectField, FloatField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, ValidationError, Regexp, Optional, NumberRange
from datetime import datetime

# Comprehensive country data with codes and cities
COUNTRY_DATA = {
    'Zambian': {
        'code': 'ZM',
        'cities': ['Lusaka', 'Kitwe', 'Ndola', 'Kabwe', 'Chingola', 'Mufulira', 'Livingstone', 'Kasama', 'Chipata', 'Solwezi']
    },
    'South African': {
        'code': 'ZA',
        'cities': ['Johannesburg', 'Cape Town', 'Durban', 'Pretoria', 'Port Elizabeth', 'Bloemfontein', 'East London']
    },
    'Kenyan': {
        'code': 'KE',
        'cities': ['Nairobi', 'Mombasa', 'Kisumu', 'Nakuru', 'Eldoret', 'Thika']
    },
    'Nigerian': {
        'code': 'NG',
        'cities': ['Lagos', 'Abuja', 'Kano', 'Ibadan', 'Port Harcourt', 'Benin City']
    },
    'Tanzanian': {
        'code': 'TZ',
        'cities': ['Dar es Salaam', 'Dodoma', 'Mwanza', 'Arusha', 'Mbeya', 'Morogoro']
    },
    'Afghan': {
        'code': 'AF',
        'cities': ['Kabul', 'Kandahar', 'Herat', 'Mazar-i-Sharif']
    },
    'Albanian': {
        'code': 'AL',
        'cities': ['Tirana', 'Durrës', 'Vlorë', 'Elbasan']
    },
    'Algerian': {
        'code': 'DZ',
        'cities': ['Algiers', 'Oran', 'Constantine', 'Annaba']
    },
    'Angolan': {
        'code': 'AO',
        'cities': ['Luanda', 'Huambo', 'Benguela', 'Lobito']
    },
    'Botswanan': {
        'code': 'BW',
        'cities': ['Gaborone', 'Francistown', 'Molepolole', 'Maun']
    },
    'Burundian': {
        'code': 'BI',
        'cities': ['Bujumbura', 'Gitega', 'Muyinga', 'Ruyigi']
    },
    'Cameroonian': {
        'code': 'CM',
        'cities': ['Yaoundé', 'Douala', 'Bamenda', 'Garoua']
    },
    'Egyptian': {
        'code': 'EG',
        'cities': ['Cairo', 'Alexandria', 'Giza', 'Shubra El Kheima']
    },
    'Ethiopian': {
        'code': 'ET',
        'cities': ['Addis Ababa', 'Dire Dawa', "Mek'ele", 'Gondar']
    },
    'Ghanaian': {
        'code': 'GH',
        'cities': ['Accra', 'Kumasi', 'Tamale', 'Sekondi-Takoradi']
    },
    'Ivorian': {
        'code': 'CI',
        'cities': ['Abidjan', 'Bouaké', 'Daloa', 'Yamoussoukro']
    },
    'Malawian': {
        'code': 'MW',
        'cities': ['Lilongwe', 'Blantyre', 'Mzuzu', 'Zomba']
    },
    'Mozambican': {
        'code': 'MZ',
        'cities': ['Maputo', 'Matola', 'Beira', 'Nampula']
    },
    'Namibian': {
        'code': 'NA',
        'cities': ['Windhoek', 'Walvis Bay', 'Swakopmund', 'Oshakati']
    },
    'Rwandan': {
        'code': 'RW',
        'cities': ['Kigali', 'Butare', 'Gitarama', 'Ruhengeri']
    },
    'Senegalese': {
        'code': 'SN',
        'cities': ['Dakar', 'Touba', 'Thiès', 'Saint-Louis']
    },
    'Sudanese': {
        'code': 'SD',
        'cities': ['Khartoum', 'Omdurman', 'Nyala', 'Port Sudan']
    },
    'Ugandan': {
        'code': 'UG',
        'cities': ['Kampala', 'Gulu', 'Lira', 'Mbarara']
    },
    'Zimbabwean': {
        'code': 'ZW',
        'cities': ['Harare', 'Bulawayo', 'Chitungwiza', 'Mutare']
    }
}

def validate_date(form, field):
    if not field.data:
        return
    try:
        # Try to parse the date
        datetime.strptime(field.data, '%Y-%m-%d')
        
        # Check if date is not in the future
        if datetime.strptime(field.data, '%Y-%m-%d') > datetime.now():
            raise ValidationError('Date of birth cannot be in the future')
            
        # Check if person is at least 18 years old
        age = (datetime.now() - datetime.strptime(field.data, '%Y-%m-%d')).days / 365.25
        if age < 18:
            raise ValidationError('You must be at least 18 years old to register')
            
    except ValueError:
        raise ValidationError('Invalid date format. Use YYYY-MM-DD')

class MemberForm(FlaskForm):
    FirstName = StringField('First Name', validators=[
        DataRequired(message='First Name is required'),
        Regexp('^[A-Za-z]+$', message='First Name must contain only letters')
    ])
    MiddleName = StringField('Middle Name', validators=[
        Optional(),
        Regexp('^[A-Za-z]*$', message='Middle Name must contain only letters')
    ])
    LastName = StringField('Last Name', validators=[
        DataRequired(message='Last Name is required'),
        Regexp('^[A-Za-z]+$', message='Last Name must contain only letters')
    ])
    Gender = SelectField('Gender', choices=[('', 'Select Gender'), ('Male', 'Male'), ('Female', 'Female')], 
                        validators=[DataRequired(message='Please select your gender')])
    Email = StringField('Email', validators=[
        DataRequired(message='Email address is required'),
        Email(message='Please enter a valid email address')
    ])
    DateofBirth = StringField('Date of Birth', validators=[
        DataRequired(message='Date of Birth is required'),
        validate_date
    ])
    MobileNo = StringField('Mobile Number', validators=[DataRequired()])
    IDNumber = StringField('ID Number', validators=[
        DataRequired(message="Please enter an ID Number"),
        Regexp(r'^\d{6}/\d{2}/\d{1}$', message="Invalid ID Number format. Example: 243095/64/1")
    ])
    IDType = SelectField('ID Type', choices=[('', 'Select ID Type'), ('NRC', 'NRC'), ('Passport', 'Passport')], validators=[DataRequired()])
    IDDocument = FileField('ID Document', validators=[
        DataRequired(message='Please upload your ID document'),
        FileAllowed(['pdf', 'png', 'jpg', 'jpeg'], 'Only PDF and image files are allowed!')
    ])
    
    Nationality = SelectField('Nationality', choices=[('', 'Select Country')] + [(country, country) for country in COUNTRY_DATA.keys()], validators=[DataRequired(message='Please select your nationality')])
    
    MembershipCategory = SelectField('Membership Category',
                                   choices=[('', 'Select Category'),
                                          ('Fellow', 'Fellow'),
                                          ('Full Member', 'Full Member'),
                                          ('Associate', 'Associate'),
                                          ('Licentiate', 'Licentiate'),
                                          ('Affiliate', 'Affiliate'),
                                          ('Student', 'Student')],
                                   validators=[DataRequired()])
    
    Address = StringField('Address', validators=[
        DataRequired(message='Address is required')
    ])
    CountryCode = StringField('Country Code', render_kw={'readonly': True})
    City = SelectField('City', choices=[('', 'Select City')], validators=[DataRequired(message='City is required')])
    MonthlyDeduction = FloatField('Monthly Deduction', validators=[
        DataRequired(message='Monthly deduction is required'),
        NumberRange(min=0, message='Monthly deduction must be a positive number')
    ])

    def validate_MobileNo(self, field):
        if self.Nationality.data == 'Zambian':
            if not field.data.startswith('260'):
                raise ValidationError('For Zambian numbers, mobile number must start with 260 (Zambia country code)')
        if not field.data.isdigit():
            raise ValidationError('Mobile number must contain only digits')
        if len(field.data) != 12:
            raise ValidationError('Mobile number must be 12 digits long (including country code)')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')
