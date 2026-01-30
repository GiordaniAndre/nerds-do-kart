from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime
from models import db, User

auth = Blueprint('auth', __name__)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Por favor, preencha todos os campos.', 'error')
            return render_template('auth/login.html')

        user = User.query.filter_by(email=email).first()

        if user and user.is_active:
            from app import bcrypt
            if bcrypt.check_password_hash(user.password_hash, password):
                user.last_login = datetime.utcnow()
                db.session.commit()
                login_user(user)
                next_page = request.args.get('next')
                return redirect(next_page if next_page else url_for('dashboard'))

        flash('Email ou senha incorretos.', 'error')

    return render_template('auth/login.html')


@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        name = request.form.get('name', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not email or not name or not password or not confirm_password:
            flash('Por favor, preencha todos os campos.', 'error')
            return render_template('auth/register.html')

        if password != confirm_password:
            flash('As senhas não coincidem.', 'error')
            return render_template('auth/register.html')

        if len(password) < 6:
            flash('A senha deve ter pelo menos 6 caracteres.', 'error')
            return render_template('auth/register.html')

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Este email já está cadastrado.', 'error')
            return render_template('auth/register.html')

        from app import bcrypt
        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

        new_user = User(
            email=email,
            name=name,
            password_hash=password_hash
        )

        db.session.add(new_user)
        db.session.commit()

        flash('Conta criada com sucesso! Faça login para continuar.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você saiu da sua conta.', 'success')
    return redirect(url_for('dashboard'))


@auth.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    from models import Racer

    if request.method == 'POST':
        # Update user profile
        current_user.name = request.form.get('name', '').strip()
        current_user.bio = request.form.get('bio', '').strip()

        # Handle 13HP permission and interest
        has_permission = request.form.get('has_13hp_permission') == 'on'
        current_user.has_13hp_permission = has_permission

        # If user has permission, automatically set interested to True
        if has_permission:
            current_user.interested_in_13hp = True
        else:
            current_user.interested_in_13hp = request.form.get('interested_in_13hp') == 'on'

        # Handle racer profile
        racer_id = request.form.get('racer_id')
        if racer_id:
            current_user.racer_id = int(racer_id) if racer_id != 'new' else None

        # If user wants to create a new racer profile
        if racer_id == 'new':
            age = request.form.get('age')
            experience_years = request.form.get('experience_years')

            # Create new racer with user's name
            new_racer = Racer(
                name=current_user.name,
                age=int(age) if age else None,
                experience_years=int(experience_years) if experience_years else 0
            )
            db.session.add(new_racer)
            db.session.flush()  # Get the ID
            current_user.racer_id = new_racer.id
        elif current_user.racer_id:
            # Update existing racer info
            racer = Racer.query.get(current_user.racer_id)
            if racer:
                age = request.form.get('age')
                experience_years = request.form.get('experience_years')
                racer.age = int(age) if age else None
                racer.experience_years = int(experience_years) if experience_years else 0

        db.session.commit()
        flash('Perfil atualizado com sucesso!', 'success')
        return redirect(url_for('auth.profile'))

    # GET request - show profile
    racers = Racer.query.order_by(Racer.name).all()
    user_racer = Racer.query.get(current_user.racer_id) if current_user.racer_id else None

    return render_template('auth/profile.html', racers=racers, user_racer=user_racer)
