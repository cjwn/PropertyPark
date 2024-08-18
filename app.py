from sqlalchemy import func
from datetime import datetime, timedelta
import csv
from flask import request
from io import StringIO
from flask import Flask, render_template, redirect, url_for, flash, request, Response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_babel import Babel, gettext as _
from flask_migrate import Migrate
from models import AuditLog, ParkingSpace, Room, db, User, Fee
from forms import LoginForm, ProfileForm, RegistrationForm, FeeForm, UserEditForm
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

migrate = Migrate(app, db)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

babel = Babel(app)


def get_locale():
    return request.accept_languages.best_match(['en', 'zh'])


babel.init_app(app, locale_selector=get_locale)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/register', methods=['GET', 'POST'])
def register():
    # 检查是否已经有超级管理员存在
    if User.query.filter_by(role='Super Admin').first() is None:
        # 没有超级管理员存在，允许创建第一个超级管理员
        form = RegistrationForm()
        del form.role
        if form.validate_on_submit():
            user = User(username=form.username.data,
                        email=form.email.data,
                        role='Super Admin')  # 自动赋予超级管理员角色
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            flash('Super Admin has been created successfully!', 'success')
            return redirect(url_for('login'))

        return render_template('register.html', form=form)
    else:
        # 已经有超级管理员存在，限制注册为超级管理员
        if not current_user.is_authenticated or current_user.role != 'Super Admin':
            flash('You do not have permission to create new users.', 'danger')
            return redirect(url_for('login'))

        form = RegistrationForm()
        if form.validate_on_submit():
            user = User(username=form.username.data,
                        email=form.email.data,
                        role=form.role.data)
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            flash('User has been created successfully!', 'success')
            return redirect(url_for('index'))

        return render_template('register.html', form=form)



@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash(_('Logged in successfully!'), 'success')
            return redirect(url_for('index'))
        flash(_('Invalid username or password.'), 'danger')
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash(_('You have been logged out.'), 'success')
    return redirect(url_for('login'))


@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    selected_month = None
    if request.method == 'POST':
        month_str = request.form.get('month')
        if month_str:
            selected_month = datetime.strptime(month_str, '%Y-%m')
    else:
        # 如果没有选择月份，默认使用当前月份
        selected_month = datetime.now()

    # 计算各项数据
    query = db.session.query(Fee)

    start_date = selected_month.replace(day=1)
    end_date = (selected_month.replace(day=1) +
                timedelta(days=32)).replace(day=1)
    query = query.filter(Fee.payment_date >= start_date,
                         Fee.payment_date < end_date)

    total_property_fees = query.filter(Fee.fee_type == 'property fee').with_entities(
        func.sum(Fee.amount)).scalar() or 0
    total_parking_fees = query.filter(Fee.fee_type == 'parking fee').with_entities(
        func.sum(Fee.amount)).scalar() or 0

    total_parking_spaces = ParkingSpace.query.count()

    unpaid_property_fees = query.filter(
        Fee.fee_type == 'property fee', Fee.payment_date == None).count()
    unpaid_parking_fees = query.filter(
        Fee.fee_type == 'parking fee', Fee.payment_date == None).count()

    occupied_parking_spaces = query.filter(Fee.fee_type == 'parking fee').with_entities(
        Fee.parking_space_number).distinct().count()
    vacant_parking_spaces = total_parking_spaces - occupied_parking_spaces

    return render_template('index.html',
                           total_property_fees=total_property_fees,
                           total_parking_fees=total_parking_fees,
                           total_parking_spaces=total_parking_spaces,
                           unpaid_property_fees=unpaid_property_fees,
                           unpaid_parking_fees=unpaid_parking_fees,
                           vacant_parking_spaces=vacant_parking_spaces,
                           selected_month=selected_month.strftime('%Y-%m') if selected_month else None)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm(obj=current_user)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        if form.password.data:
            current_user.set_password(form.password.data)
        db.session.commit()
        flash('Your profile has been updated!', 'success')
        return redirect(url_for('profile'))
    return render_template('profile.html', form=form)

@app.route('/manage-users', methods=['GET', 'POST'])
@login_required
def manage_users():
    if current_user.role != 'Super Admin':
        flash('You do not have permission to manage users.', 'danger')
        return redirect(url_for('index'))
    
    users = User.query.all()
    return render_template('manage_users.html', users=users)


@app.route('/edit-user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    if current_user.role != 'Super Admin':
        flash('You do not have permission to edit users.', 'danger')
        return redirect(url_for('index'))
    
    user = User.query.get_or_404(user_id)
    form = UserEditForm(obj=user)
    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        user.role = form.role.data
        db.session.commit()
        flash('User has been updated successfully!', 'success')
        return redirect(url_for('manage_users'))
    return render_template('edit_user.html', form=form, user=user)



@app.route('/add-fee', methods=['GET', 'POST'])
@login_required
def add_fee():
    form = FeeForm()
    form.action = 'add'
    if form.validate_on_submit():
        parking_space_number = form.parking_space_number.data
        room_number = form.room_number.data

        # 如果停车位不存在，则添加
        if parking_space_number and not ParkingSpace.query.filter_by(space_number=parking_space_number).first():
            new_space = ParkingSpace(space_number=parking_space_number)
            db.session.add(new_space)

        # 如果房间号不存在，则添加
        if room_number and not Room.query.filter_by(room_number=room_number).first():
            new_room = Room(room_number=room_number)
            db.session.add(new_room)

        fee = Fee(payment_date=form.payment_date.data.strftime('%Y-%m-%d'),
                  room_number=room_number,
                  license_plate_number=form.license_plate_number.data,
                  parking_space_number=parking_space_number,
                  amount=form.amount.data,
                  fee_type=form.fee_type.data,
                  payment_method=form.payment_method.data,
                  due_date=form.due_date.data.strftime('%Y-%m-%d'),
                  receipt_number=form.receipt_number.data,
                  name=form.name.data,
                  gender=form.gender.data,
                  user_id=current_user.id)
        db.session.add(fee)
        db.session.commit()
        flash(_('Fee information submitted successfully!'), 'success')
        return redirect(url_for('view_fees'))
    return render_template('fee_form.html', form=form)


@app.route('/import-fees', methods=['GET', 'POST'])
@login_required
def import_fees():
    if request.method == 'POST':
        file = request.files['file']
        if file and file.filename.endswith('.csv'):
            csv_file = StringIO(file.stream.read().decode('utf-8'))
            csv_reader = csv.DictReader(csv_file)

            for row in csv_reader:
                # 提取CSV文件中的各列
                payment_date = row['payment_date']
                room_number = row['room_number']
                license_plate_number = row['license_plate_number']
                parking_space_number = row['parking_space_number']
                amount = row['amount']
                fee_type = row['fee_type']
                payment_method = row['payment_method']
                due_date = row['due_date']
                receipt_number = row['receipt_number']
                name = row['name']
                gender = row['gender']

                # 自动添加房间号和停车位
                if room_number and not Room.query.filter_by(room_number=room_number).first():
                    new_room = Room(room_number=room_number)
                    db.session.add(new_room)

                if parking_space_number and not ParkingSpace.query.filter_by(space_number=parking_space_number).first():
                    new_space = ParkingSpace(space_number=parking_space_number)
                    db.session.add(new_space)

                # 创建并保存 Fee 对象
                fee = Fee(
                    payment_date=payment_date,
                    room_number=room_number,
                    license_plate_number=license_plate_number,
                    parking_space_number=parking_space_number,
                    amount=amount,
                    fee_type=fee_type,
                    payment_method=payment_method,
                    due_date=due_date,
                    receipt_number=receipt_number,
                    name=name,
                    gender=gender,
                    user_id=current_user.id  # 假设这些历史费用属于当前用户
                )
                db.session.add(fee)

            db.session.commit()
            flash(_('Historical fees imported successfully!'), 'success')
        else:
            flash(_('Please upload a valid CSV file!'), 'danger')

        return redirect(url_for('index'))

    return render_template('import_fees.html')


@app.route('/view-fees', methods=['GET', 'POST'])
@login_required
def view_fees():
    query = Fee.query.filter_by(is_deleted=False)

    if request.method == 'POST':
        search_term = request.form.get('search_term')
        if search_term:
            query = query.filter(
                Fee.room_number.ilike(f'%{search_term}%') |
                Fee.license_plate_number.ilike(f'%{search_term}%') |
                Fee.parking_space_number.ilike(f'%{search_term}%') |
                Fee.receipt_number.ilike(f'%{search_term}%') |
                Fee.name.ilike(f'%{search_term}%')
            )

    fees = query.all()
    return render_template('view_fees.html', fees=fees, search_term=search_term if 'search_term' in locals() else "")



@app.route('/download-fee-template')
@login_required
def download_fee_template():
    csv_data = """payment_date,room_number,license_plate_number,parking_space_number,amount,fee_type,payment_method,due_date,receipt_number,name,gender
2024-08-10,101,ABC123,PS01,100.0,property fee,bank,2024-08-20,123456,John Doe,Male
"""
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=fee_template.csv"})


@app.route('/summary')
@login_required
def summary():
    fees = Fee.query.filter_by(is_deleted=False).all()  # 仅显示未逻辑删除的记录
    if not fees:  # 如果 fees 列表为空
        flash(_('No fees found for the current user.'), 'info')
        return render_template('summary.html', fees=fees)
    return render_template('summary.html', fees=fees)


@app.route('/parking-spaces', methods=['GET', 'POST'])
@login_required
def parking_spaces():
    selected_month = None
    search_query = request.form.get('search_query')  # 获取搜索查询

    if request.method == 'POST':
        month_str = request.form.get('month')
        if month_str:
            selected_month = datetime.strptime(month_str, '%Y-%m')
        else:
            selected_month = datetime.now()
    else:
        # 如果不是 POST 请求，默认使用当前月份
        selected_month = datetime.now()

    query = db.session.query(ParkingSpace, Fee.license_plate_number, func.count(Fee.id).label('paid')).outerjoin(
        Fee, ParkingSpace.space_number == Fee.parking_space_number
    )

    if selected_month:
        start_date = selected_month.replace(day=1)
        end_date = (selected_month.replace(day=1) +
                    timedelta(days=32)).replace(day=1)
        query = query.filter(Fee.payment_date >= start_date,
                             Fee.payment_date < end_date)

    if search_query:
        query = query.filter(ParkingSpace.space_number.ilike(f'%{search_query}%') |
                             Fee.license_plate_number.ilike(f'%{search_query}%'))

    parking_spaces = query.group_by(
        ParkingSpace.space_number, Fee.license_plate_number).all()

    return render_template('parking_spaces.html', parking_spaces=parking_spaces, selected_month=selected_month.strftime('%Y-%m') if selected_month else None, search_query=search_query)


@app.route('/add-parking-space', methods=['GET', 'POST'])
@login_required
def add_parking_space():
    if request.method == 'POST':
        space_number = request.form['space_number']
        if not ParkingSpace.query.filter_by(space_number=space_number).first():
            new_space = ParkingSpace(space_number=space_number)
            db.session.add(new_space)
            db.session.commit()
            flash(_('Parking space added successfully!'), 'success')
        else:
            flash(_('Parking space already exists!'), 'warning')
        return redirect(url_for('parking_spaces'))

    return render_template('add_parking_space.html')


@app.route('/import-parking-spaces', methods=['GET', 'POST'])
@login_required
def import_parking_spaces():
    if request.method == 'POST':
        file = request.files['file']
        if file and file.filename.endswith('.csv'):
            csv_file = StringIO(file.stream.read().decode('utf-8'))
            csv_reader = csv.reader(csv_file, delimiter=',')
            for row in csv_reader:
                space_number = row[0]
                if space_number and not ParkingSpace.query.filter_by(space_number=space_number).first():
                    new_space = ParkingSpace(space_number=space_number)
                    db.session.add(new_space)
            db.session.commit()
            flash(_('Parking spaces imported successfully!'), 'success')
        else:
            flash(_('Please upload a valid CSV file!'), 'danger')
        return redirect(url_for('parking_spaces'))

    return render_template('import_parking_spaces.html')


@app.route('/rooms', methods=['GET', 'POST'])
@login_required
def rooms():
    selected_month = None
    search_query = request.form.get('search_query')  # 获取搜索查询

    if request.method == 'POST':
        month_str = request.form.get('month')
        if month_str:
            selected_month = datetime.strptime(month_str, '%Y-%m')
        else:
            selected_month = datetime.now()
    else:
        # 如果不是 POST 请求，默认使用当前月份
        selected_month = datetime.now()

    query = db.session.query(Room, func.count(Fee.id).label('paid')).outerjoin(
        Fee, Room.room_number == Fee.room_number
    )

    if selected_month:
        start_date = selected_month.replace(day=1)
        end_date = (selected_month.replace(day=1) +
                    timedelta(days=32)).replace(day=1)
        query = query.filter(Fee.payment_date >= start_date,
                             Fee.payment_date < end_date)

    if search_query:
        query = query.filter(Room.room_number.ilike(f'%{search_query}%'))

    rooms = query.group_by(Room.room_number).all()

    return render_template('rooms.html', rooms=rooms, selected_month=selected_month.strftime('%Y-%m') if selected_month else None, search_query=search_query)


@app.route('/add-room', methods=['GET', 'POST'])
@login_required
def add_room():
    if request.method == 'POST':
        room_number = request.form['room_number']
        if not Room.query.filter_by(room_number=room_number).first():
            new_room = Room(room_number=room_number)
            db.session.add(new_room)
            db.session.commit()
            flash(_('Room number added successfully!'), 'success')
        else:
            flash(_('Room number already exists!'), 'warning')
        return redirect(url_for('rooms'))

    return render_template('add_room.html')


@app.route('/edit-room/<int:room_id>', methods=['GET', 'POST'])
@login_required
def edit_room(room_id):
    room = Room.query.get_or_404(room_id)
    if request.method == 'POST':
        new_room_number = request.form['room_number']
        if new_room_number and Room.query.filter_by(room_number=new_room_number).first():
            flash(_('Room number already exists!'), 'warning')
        else:
            room.room_number = new_room_number
            db.session.commit()
            flash(_('Room number updated successfully!'), 'success')
        return redirect(url_for('rooms'))

    return render_template('edit_room.html', room=room)


@app.route('/edit-parking-space/<int:space_id>', methods=['GET', 'POST'])
@login_required
def edit_parking_space(space_id):
    space = ParkingSpace.query.get_or_404(space_id)
    if request.method == 'POST':
        new_space_number = request.form['space_number']
        if new_space_number and ParkingSpace.query.filter_by(space_number=new_space_number).first():
            flash(_('Parking space already exists!'), 'warning')
        else:
            space.space_number = new_space_number
            db.session.commit()
            flash(_('Parking space updated successfully!'), 'success')
        return redirect(url_for('parking_spaces'))

    return render_template('edit_parking_space.html', space=space)


@app.route('/import-rooms', methods=['GET', 'POST'])
@login_required
def import_rooms():
    if request.method == 'POST':
        file = request.files['file']
        if file and file.filename.endswith('.csv'):
            csv_file = StringIO(file.stream.read().decode('utf-8'))
            csv_reader = csv.reader(csv_file, delimiter=',')
            for row in csv_reader:
                room_number = row[0]
                if room_number and not Room.query.filter_by(room_number=room_number).first():
                    new_room = Room(room_number=room_number)
                    db.session.add(new_room)
            db.session.commit()
            flash(_('Rooms imported successfully!'), 'success')
        else:
            flash(_('Please upload a valid CSV file!'), 'danger')
        return redirect(url_for('rooms'))

    return render_template('import_rooms.html')


@app.route('/parking-usage', methods=['GET', 'POST'])
@login_required
def parking_usage():
    if request.method == 'POST':
        date_str = request.form['date']
        query_date = datetime.strptime(date_str, '%Y-%m-%d')

        # 查询指定日期已支付的停车位及其车牌号
        fees = Fee.query.filter(
            # 仅显示未逻辑删除的记录
            Fee.payment_date <= query_date, Fee.due_date >= query_date, Fee.is_deleted is False).all()
        parking_usage = {}
        for fee in fees:
            if fee.parking_space_number:
                parking_usage[fee.parking_space_number] = fee.license_plate_number

        # 获取所有停车位
        all_parking_spaces = ParkingSpace.query.all()
        occupied_spaces = set(parking_usage.keys())
        total_spaces = set(
            [space.space_number for space in all_parking_spaces])

        # 计算闲置的停车位
        free_spaces = total_spaces - occupied_spaces

        return render_template('parking_usage.html', parking_usage=parking_usage, free_spaces=free_spaces, date=date_str)

    return render_template('parking_usage_form.html')


@app.route('/delete-fee/<int:fee_id>', methods=['POST'])
@login_required
def delete_fee(fee_id):
    fee = Fee.query.get_or_404(fee_id)
    if current_user.role == 'Finance Supervisor' or current_user.role == 'Super Admin':
        db.session.delete(fee)  # 物理删除
        db.session.commit()
        flash(_('Fee record has been permanently deleted.'), 'success')
    elif current_user.role == 'Cashier':
        fee.delete()  # 逻辑删除
        flash(_('Fee record has been marked as deleted.'), 'success')
    else:
        flash(_('You do not have permission to delete this fee.'), 'danger')
    # 记录删除操作
    log = AuditLog(
        user_id=current_user.id,
        action='delete',
        fee_id=fee.id,
        details=f'Deleted fee record with receipt number: {fee.receipt_number}'
    )
    db.session.add(log)

    db.session.delete(fee)
    db.session.commit()
    flash(_('Fee record deleted successfully!'), 'success')
    return redirect(url_for('index'))


@app.route('/edit-fee/<int:fee_id>', methods=['GET', 'POST'])
@login_required
def edit_fee(fee_id):
    fee = Fee.query.get_or_404(fee_id)
    
    # Ensure datetime fields are properly handled
    if isinstance(fee.payment_date, str):
        fee.payment_date = datetime.strptime(fee.payment_date, '%Y-%m-%d')
    
    if isinstance(fee.due_date, str):
        fee.due_date = datetime.strptime(fee.due_date, '%Y-%m-%d')
    
    form = FeeForm(obj=fee)
    form.action = 'edit'

    if form.validate_on_submit():
        # 记录编辑前的状态
        original_data = {
            'payment_date': fee.payment_date,
            'room_number': fee.room_number,
            'license_plate_number': fee.license_plate_number,
            'parking_space_number': fee.parking_space_number,
            'amount': fee.amount,
            'fee_type': fee.fee_type,
            'payment_method': fee.payment_method,
            'due_date': fee.due_date,
            'receipt_number': fee.receipt_number,
            'name': fee.name,
            'gender': fee.gender,
        }

        # 更新费用对象
        fee.payment_date = datetime.strptime(form.payment_date.data, '%Y-%m-%d') if isinstance(form.payment_date.data, str) else form.payment_date.data
        fee.due_date = datetime.strptime(form.due_date.data, '%Y-%m-%d') if isinstance(form.due_date.data, str) else form.due_date.data
        form.populate_obj(fee)
        
        db.session.commit()

        # 记录编辑操作
        log = AuditLog(
            user_id=current_user.id,
            action='edit',
            fee_id=fee.id,
            details=f'Edited fee record from {original_data} to {form.data}'
        )
        db.session.add(log)
        db.session.commit()

        flash(_('Fee record updated successfully!'), 'success')
        return redirect(url_for('index'))

    return render_template('fee_form.html', form=form, fee=fee)


@app.route('/audit-log')
@login_required
def audit_log():
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).all()
    return render_template('audit_log.html', logs=logs)


@app.route('/fee-statistics', methods=['GET', 'POST'])
@login_required
def fee_statistics():
    fee_type_stats = []
    payment_method_stats = []

    if request.method == 'POST':
        month_str = request.form.get('month')
        if month_str:
            selected_month = datetime.strptime(month_str, '%Y-%m')
        else:
            selected_month = datetime.now()  # 如果没有选择月份，默认使用当前月份
    else:
        selected_month = datetime.now()

    query = db.session.query(Fee)

    start_date = selected_month.replace(day=1)
    end_date = (selected_month.replace(day=1) +
                timedelta(days=32)).replace(day=1)
    query = query.filter(Fee.payment_date >= start_date,
                         Fee.payment_date < end_date)

    # 按费用类型统计
    fee_type_stats = query.with_entities(
        Fee.fee_type,
        func.sum(Fee.amount).label('total_amount')
    ).group_by(Fee.fee_type).all()

    # 按支付方式统计
    payment_method_stats = query.with_entities(
        Fee.payment_method,
        func.sum(Fee.amount).label('total_amount')
    ).group_by(Fee.payment_method).all()

    return render_template('fee_statistics.html',
                           fee_type_stats=fee_type_stats,
                           payment_method_stats=payment_method_stats,
                           selected_month=selected_month.strftime('%Y-%m') if selected_month else None)


@app.route('/search-fees', methods=['GET', 'POST'])
@login_required
def search_fees():
    fees = []
    if request.method == 'POST':
        receipt_number = request.form.get('receipt_number')
        name = request.form.get('name')
        parking_space_number = request.form.get('parking_space_number')
        license_plate_number = request.form.get('license_plate_number')
        amount = request.form.get('amount')

        query = Fee.query

        if receipt_number:
            query = query.filter(Fee.receipt_number == receipt_number)
        if name:
            query = query.filter(Fee.name.ilike(f'%{name}%'))
        if parking_space_number:
            query = query.filter(
                Fee.parking_space_number == parking_space_number)
        if license_plate_number:
            query = query.filter(
                Fee.license_plate_number == license_plate_number)
        if amount:
            query = query.filter(Fee.amount == amount)

        fees = query.all()

    return render_template('search_fees.html', fees=fees)


@app.route('/parking-space/<string:space_number>', methods=['GET'])
@login_required
def parking_space_details(space_number):
    fees = Fee.query.filter_by(
        parking_space_number=space_number, is_deleted=False).all()
    return render_template('parking_space_details.html', space_number=space_number, fees=fees)


@app.route('/room/<string:room_number>', methods=['GET'])
@login_required
def room_details(room_number):
    fees = Fee.query.filter_by(room_number=room_number, is_deleted=False).all()
    return render_template('room_details.html', room_number=room_number, fees=fees)


@app.route('/organize-data', methods=['GET', 'POST'])
@login_required
def organize_data():
    # 获取所有Fee记录中的房间号和停车位号
    fees = Fee.query.filter_by(is_deleted=False).all()  # 仅显示未逻辑删除的记录

    # 处理房间号
    for fee in fees:
        if fee.room_number and not Room.query.filter_by(room_number=fee.room_number).first():
            new_room = Room(room_number=fee.room_number)
            db.session.add(new_room)

    # 处理停车位号
    for fee in fees:
        if fee.parking_space_number and not ParkingSpace.query.filter_by(space_number=fee.parking_space_number).first():
            new_space = ParkingSpace(space_number=fee.parking_space_number)
            db.session.add(new_space)

    db.session.commit()

    flash(_('Rooms and Parking Spaces have been organized based on existing fees.'), 'success')
    return redirect(url_for('index'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
