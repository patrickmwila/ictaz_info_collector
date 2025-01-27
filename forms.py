from flask_wtf import FlaskForm
from wtforms import StringField, SelectField
from wtforms.validators import DataRequired, Email, ValidationError, Regexp, Optional
from datetime import datetime

# Comprehensive list of countries with Zambia at the top
COUNTRIES = [
    ('Zambian', 'Zambian'),  # Default option
    ('Afghan', 'Afghan'),
    ('Albanian', 'Albanian'),
    ('Algerian', 'Algerian'),
    ('American', 'American'),
    ('Andorran', 'Andorran'),
    ('Angolan', 'Angolan'),
    ('Antiguan', 'Antiguan'),
    ('Argentine', 'Argentine'),
    ('Armenian', 'Armenian'),
    ('Australian', 'Australian'),
    ('Austrian', 'Austrian'),
    ('Azerbaijani', 'Azerbaijani'),
    ('Bahamian', 'Bahamian'),
    ('Bahraini', 'Bahraini'),
    ('Bangladeshi', 'Bangladeshi'),
    ('Barbadian', 'Barbadian'),
    ('Belarusian', 'Belarusian'),
    ('Belgian', 'Belgian'),
    ('Belizean', 'Belizean'),
    ('Beninese', 'Beninese'),
    ('Bhutanese', 'Bhutanese'),
    ('Bolivian', 'Bolivian'),
    ('Bosnian', 'Bosnian'),
    ('Botswanan', 'Botswanan'),
    ('Brazilian', 'Brazilian'),
    ('British', 'British'),
    ('Bruneian', 'Bruneian'),
    ('Bulgarian', 'Bulgarian'),
    ('Burkinabe', 'Burkinabe'),
    ('Burundian', 'Burundian'),
    ('Cambodian', 'Cambodian'),
    ('Cameroonian', 'Cameroonian'),
    ('Canadian', 'Canadian'),
    ('Cape Verdean', 'Cape Verdean'),
    ('Central African', 'Central African'),
    ('Chadian', 'Chadian'),
    ('Chilean', 'Chilean'),
    ('Chinese', 'Chinese'),
    ('Colombian', 'Colombian'),
    ('Comoran', 'Comoran'),
    ('Congolese', 'Congolese'),
    ('Costa Rican', 'Costa Rican'),
    ('Croatian', 'Croatian'),
    ('Cuban', 'Cuban'),
    ('Cypriot', 'Cypriot'),
    ('Czech', 'Czech'),
    ('Danish', 'Danish'),
    ('Djiboutian', 'Djiboutian'),
    ('Dominican', 'Dominican'),
    ('Dutch', 'Dutch'),
    ('East Timorese', 'East Timorese'),
    ('Ecuadorean', 'Ecuadorean'),
    ('Egyptian', 'Egyptian'),
    ('Emirian', 'Emirian'),
    ('Equatorial Guinean', 'Equatorial Guinean'),
    ('Eritrean', 'Eritrean'),
    ('Estonian', 'Estonian'),
    ('Ethiopian', 'Ethiopian'),
    ('Fijian', 'Fijian'),
    ('Filipino', 'Filipino'),
    ('Finnish', 'Finnish'),
    ('French', 'French'),
    ('Gabonese', 'Gabonese'),
    ('Gambian', 'Gambian'),
    ('Georgian', 'Georgian'),
    ('German', 'German'),
    ('Ghanaian', 'Ghanaian'),
    ('Greek', 'Greek'),
    ('Grenadian', 'Grenadian'),
    ('Guatemalan', 'Guatemalan'),
    ('Guinean', 'Guinean'),
    ('Guyanese', 'Guyanese'),
    ('Haitian', 'Haitian'),
    ('Honduran', 'Honduran'),
    ('Hungarian', 'Hungarian'),
    ('Icelandic', 'Icelandic'),
    ('Indian', 'Indian'),
    ('Indonesian', 'Indonesian'),
    ('Iranian', 'Iranian'),
    ('Iraqi', 'Iraqi'),
    ('Irish', 'Irish'),
    ('Israeli', 'Israeli'),
    ('Italian', 'Italian'),
    ('Ivorian', 'Ivorian'),
    ('Jamaican', 'Jamaican'),
    ('Japanese', 'Japanese'),
    ('Jordanian', 'Jordanian'),
    ('Kazakhstani', 'Kazakhstani'),
    ('Kenyan', 'Kenyan'),
    ('Kiribati', 'Kiribati'),
    ('Kuwaiti', 'Kuwaiti'),
    ('Kyrgyz', 'Kyrgyz'),
    ('Laotian', 'Laotian'),
    ('Latvian', 'Latvian'),
    ('Lebanese', 'Lebanese'),
    ('Lesotho', 'Lesotho'),
    ('Liberian', 'Liberian'),
    ('Libyan', 'Libyan'),
    ('Liechtensteiner', 'Liechtensteiner'),
    ('Lithuanian', 'Lithuanian'),
    ('Luxembourger', 'Luxembourger'),
    ('Macedonian', 'Macedonian'),
    ('Malagasy', 'Malagasy'),
    ('Malawian', 'Malawian'),
    ('Malaysian', 'Malaysian'),
    ('Maldivian', 'Maldivian'),
    ('Malian', 'Malian'),
    ('Maltese', 'Maltese'),
    ('Marshallese', 'Marshallese'),
    ('Mauritanian', 'Mauritanian'),
    ('Mauritian', 'Mauritian'),
    ('Mexican', 'Mexican'),
    ('Micronesian', 'Micronesian'),
    ('Moldovan', 'Moldovan'),
    ('Monacan', 'Monacan'),
    ('Mongolian', 'Mongolian'),
    ('Montenegrin', 'Montenegrin'),
    ('Moroccan', 'Moroccan'),
    ('Mozambican', 'Mozambican'),
    ('Namibian', 'Namibian'),
    ('Nauruan', 'Nauruan'),
    ('Nepalese', 'Nepalese'),
    ('New Zealander', 'New Zealander'),
    ('Nicaraguan', 'Nicaraguan'),
    ('Nigerian', 'Nigerian'),
    ('Nigerien', 'Nigerien'),
    ('North Korean', 'North Korean'),
    ('Norwegian', 'Norwegian'),
    ('Omani', 'Omani'),
    ('Pakistani', 'Pakistani'),
    ('Palauan', 'Palauan'),
    ('Palestinian', 'Palestinian'),
    ('Panamanian', 'Panamanian'),
    ('Papua New Guinean', 'Papua New Guinean'),
    ('Paraguayan', 'Paraguayan'),
    ('Peruvian', 'Peruvian'),
    ('Polish', 'Polish'),
    ('Portuguese', 'Portuguese'),
    ('Qatari', 'Qatari'),
    ('Romanian', 'Romanian'),
    ('Russian', 'Russian'),
    ('Rwandan', 'Rwandan'),
    ('Saint Lucian', 'Saint Lucian'),
    ('Salvadoran', 'Salvadoran'),
    ('Samoan', 'Samoan'),
    ('San Marinese', 'San Marinese'),
    ('Sao Tomean', 'Sao Tomean'),
    ('Saudi', 'Saudi'),
    ('Senegalese', 'Senegalese'),
    ('Serbian', 'Serbian'),
    ('Seychellois', 'Seychellois'),
    ('Sierra Leonean', 'Sierra Leonean'),
    ('Singaporean', 'Singaporean'),
    ('Slovak', 'Slovak'),
    ('Slovenian', 'Slovenian'),
    ('Solomon Islander', 'Solomon Islander'),
    ('Somali', 'Somali'),
    ('South African', 'South African'),
    ('South Korean', 'South Korean'),
    ('South Sudanese', 'South Sudanese'),
    ('Spanish', 'Spanish'),
    ('Sri Lankan', 'Sri Lankan'),
    ('Sudanese', 'Sudanese'),
    ('Surinamese', 'Surinamese'),
    ('Swazi', 'Swazi'),
    ('Swedish', 'Swedish'),
    ('Swiss', 'Swiss'),
    ('Syrian', 'Syrian'),
    ('Taiwanese', 'Taiwanese'),
    ('Tajik', 'Tajik'),
    ('Tanzanian', 'Tanzanian'),
    ('Thai', 'Thai'),
    ('Togolese', 'Togolese'),
    ('Tongan', 'Tongan'),
    ('Trinidadian', 'Trinidadian'),
    ('Tunisian', 'Tunisian'),
    ('Turkish', 'Turkish'),
    ('Turkmen', 'Turkmen'),
    ('Tuvaluan', 'Tuvaluan'),
    ('Ugandan', 'Ugandan'),
    ('Ukrainian', 'Ukrainian'),
    ('Uruguayan', 'Uruguayan'),
    ('Uzbekistani', 'Uzbekistani'),
    ('Vanuatuan', 'Vanuatuan'),
    ('Venezuelan', 'Venezuelan'),
    ('Vietnamese', 'Vietnamese'),
    ('Yemeni', 'Yemeni'),
    ('Zimbabwean', 'Zimbabwean')
]

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
        DataRequired(message='Date of Birth is required')
    ])
    
    MobileNo = StringField('Mobile Number', validators=[DataRequired()])
    
    IDNumber = StringField('ID Number', validators=[
        DataRequired(message="Please enter an ID Number"),
        Regexp(r'^\d{6}/\d{2}/\d{1}$', message="Invalid ID Number format. Example: 243095/64/1")
    ])
    IDType = SelectField('ID Type', choices=[('', 'Select ID Type'), ('NRC', 'NRC'), ('Passport', 'Passport')], validators=[DataRequired()])
    Nationality = SelectField('Nationality', choices=COUNTRIES, default='Zambian')
    MembershipCategory = SelectField('Membership Category',
                                   choices=[('', 'Select Membership Category'),
                                          ('Fellow', 'Fellow'),
                                          ('FullMember', 'Full Member'),
                                          ('Associate', 'Associate'),
                                          ('Licentiate', 'Licentiate'),
                                          ('Affiliate', 'Affiliate'),
                                          ('Student', 'Student')],
                                   validators=[DataRequired()])

    def validate_DateofBirth(self, field):
        if not field.data:
            raise ValidationError('Date of Birth is required')
        
        try:
            # Try to parse the date
            date = datetime.strptime(field.data, '%d/%m/%Y')
            
            # Check if date is not in the future
            if date > datetime.now():
                raise ValidationError('Date of Birth cannot be in the future')
            
            # Check if person is at least 18 years old
            age = (datetime.now() - date).days / 365.25
            if age < 18:
                raise ValidationError('You must be at least 18 years old')
                
        except ValueError:
            raise ValidationError('Invalid date format. Use DD/MM/YYYY (e.g., 25/12/1990)')

    def validate_MobileNo(self, field):
        if not field.data:
            raise ValidationError('Mobile number is required')
        if not field.data.startswith('260'):
            raise ValidationError('Mobile number must start with 260')
        if not field.data[3:].isdigit() or len(field.data) != 12:
            raise ValidationError('Must be 12 digits total (260 followed by 9 digits)')
