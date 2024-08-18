from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FloatField, SelectField, DateField
from wtforms.validators import DataRequired, Length, Optional
from flask_babel import lazy_gettext as _

class LoginForm(FlaskForm):
    username = StringField(_('Username'), validators=[DataRequired(message=_('This field is required.'))])
    password = PasswordField(_('Password'), validators=[DataRequired(message=_('This field is required.'))])
    submit = SubmitField(_('Login'))

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError
from models import User

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])

    # 仅在已经有超级管理员时显示角色选择
    role = SelectField('Role', choices=[('Finance Supervisor', 'Finance Supervisor'),
                                        ('Cashier', 'Cashier'),
                                        ('Business Manager', 'Business Manager')],
                                        validators=[DataRequired()])

    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username is already taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email is already registered. Please choose a different one.')


class FeeForm(FlaskForm):
    payment_date = DateField(_('Payment Date'), format='%Y-%m-%d', validators=[DataRequired(message=_('This field is required.'))])
    room_number = StringField(_('Room Number'), validators=[DataRequired(message=_('This field is required.'))])
    license_plate_number = StringField(_('License Plate Number'))
    parking_space_number = StringField(_('Parking Space Number'))
    amount = FloatField(_('Amount'), validators=[DataRequired(message=_('This field is required.'))])
    fee_type = SelectField(_('Fee Type'), choices=[('parking fee', _('Parking Fee')), ('property fee', _('Property Fee'))], validators=[DataRequired(message=_('This field is required.'))])
    payment_method = SelectField(_('Payment Method'), choices=[('bank', _('Bank')), ('CITIC', _('CITIC')), ('Shouqianba', _('Shouqianba')), ('cash', _('Cash'))], validators=[DataRequired(message=_('This field is required.'))])
    due_date = DateField(_('Due Date'), format='%Y-%m-%d')
    receipt_number = StringField(_('Receipt Number'), validators=[DataRequired(message=_('This field is required.'))])
    name = StringField(_('Name'), validators=[DataRequired(message=_('This field is required.'))])
    gender = StringField(_('Gender'), validators=[DataRequired(message=_('This field is required.'))])
    
    submit = SubmitField(_('Submit'))


class ProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('New Password', validators=[Optional()])
    submit = SubmitField('Update Profile')


class UserEditForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    role = SelectField('Role', choices=[('Finance Supervisor', 'Finance Supervisor'),
                                        ('Cashier', 'Cashier'),
                                        ('Business Manager', 'Business Manager'),
                                        ('Super Admin', 'Super Admin')],
                                        validators=[DataRequired()])
    submit = SubmitField('Update User')
