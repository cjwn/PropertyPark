from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from flask_babel import Babel, gettext as _

db = SQLAlchemy()


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    role = db.Column(db.String(50), nullable=False, default='Business Manager')  # 默认角色为业务经理

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return '<User {}>'.format(self.username)


class Fee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    payment_date = db.Column(db.String(50))
    room_number = db.Column(db.String(50))
    license_plate_number = db.Column(db.String(50))
    parking_space_number = db.Column(db.String(50))
    amount = db.Column(db.Float)
    fee_type = db.Column(db.String(50))
    payment_method = db.Column(db.String(50))
    due_date = db.Column(db.String(50))
    receipt_number = db.Column(db.String(50))
    name = db.Column(db.String(150), nullable=False)
    gender = db.Column(db.String(10))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    is_deleted = db.Column(db.Boolean, default=False)  # 新增字段：逻辑删除标志

    def delete(self):
        self.is_deleted = True
        db.session.commit()

    def get_fee_type_display(self):
        if self.fee_type == 'parking fee':
            return _('Parking Fee')
        elif self.fee_type == 'property fee':
            return _('Property Fee')

    def get_payment_method_display(self):
        if self.payment_method == 'bank':
            return _('Bank')
        elif self.payment_method == 'CITIC':
            return _('CITIC')
        elif self.payment_method == 'Shouqianba':
            return _('Shouqianba')
        elif self.payment_method == 'cash':
            return _('Cash')

    def __repr__(self):
        return f'<Fee {self.room_number} - {self.get_fee_type_display()}>'


class ParkingSpace(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    space_number = db.Column(db.String(50), unique=True, nullable=False)

    def __repr__(self):
        return f'<ParkingSpace {self.space_number}>'


class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_number = db.Column(db.String(50), unique=True, nullable=False)

    def __repr__(self):
        return f'<Room {self.room_number}>'


class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    action = db.Column(db.String(50), nullable=False)  # 例如 'edit', 'delete'
    fee_id = db.Column(db.Integer, nullable=True)  # 记录与操作相关的费用ID
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)  # 操作时间
    details = db.Column(db.String(255), nullable=True)  # 记录操作的详细信息

    def __repr__(self):
        return f'<AuditLog {self.action} by User {self.user_id} on Fee {self.fee_id}>'
