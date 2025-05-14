# myserver/views.
import os
import certifi
import uuid
import base64
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from myDjangoAdmin.models import Staff, LibraryUser, StaffSessionLog, UserSessionLog, Genre, Book
from myserver.decorators import staff_required, user_required
from myserver.forms import LibraryUserSignupForm, BookForm 
from django.db.models import Prefetch, Q
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition, ContentId
from django.conf import settings
from django.utils import timezone
from django.urls import reverse

def otp_confirm(request):
    user = request.user
    
    if request.method == 'POST':
        otp_code = request.POST.get('otp_code')
        try:
            user = LibraryUser.objects.get(otp_code=otp_code)
            if user.is_otp_valid(otp_code):
                user.is_active = True
                user.otp_code = None
                user.otp_expiry = None
                user.save()
                messages.success(request, "Your account has been verified! You can now log in.")
                return redirect('login') 
            else:
                messages.error(request, "Invalid or expired OTP.")
        except LibraryUser.DoesNotExist:
            messages.error(request, "Invalid OTP.")
    return render(request, "myserver/components/otpconfirm.html")

def login_page(request):
    return render(request, "myserver/login.html")

def login_staff(request):
    if request.method == 'POST':
        staff_id = request.POST.get('staff_id')
        password = request.POST.get('password')

        try:
    
            staff = Staff.objects.get(staff_id=staff_id)
            email = staff.email  

            user = authenticate(request, email=email, password=password)
            print(f"[Authenticate Result - Staff Login] {user} ({type(user)})")

            if user is not None and isinstance(user, Staff):
                login(request, user)

                session_id = str(uuid.uuid4())
                request.session['session_id'] = session_id
                request.session['staff_id'] = staff_id
                request.session['is_staff'] = True

                StaffSessionLog.objects.create(
                    staff=staff,
                    session_id=session_id,
                    action="Login"
                )

                print(f"[Login Success] {staff.email} | Session ID: {session_id}")

                request.session.save()

                return redirect('staff_home')
            else:
                messages.error(request, 'Invalid password. Please try again.')

        except Staff.DoesNotExist:
            messages.error(request, 'Staff ID not found. Please try again.')

    return render(request, "myserver/loginstaff.html")

@staff_required
def staff_home(request):
    return render(request, 'staff/home.html', { 'appbar_title': 'Dashboard' })

@staff_required
def staff_addbook(request):
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES)
        if form.is_valid():
            book = form.save()

            extra_images = request.FILES.getlist('extra_images')
            for index, image in enumerate(extra_images[:5], start=1):
                setattr(book, f'extra_image_{index}', image)
            book.save()

            messages.success(request, "Book added successfully.")
            return redirect('staff_addbook')
        else:
            print(form.errors)
            messages.error(request, "Please correct the errors below.")
    else:
        form = BookForm()

    genres = Genre.objects.all()
    return render(request, 'staff/addnewbook.html', {'form': form, 'genres': genres, 'appbar_title': 'Add New Book'})

@staff_required
def staff_barcode(request):
    return render(request, 'staff/barcode.html', { 'appbar_title': 'Barcode' })

@staff_required
def staff_transaction(request):
    return render(request, 'staff/transaction.html', { 'appbar_title': 'Transaction' })

@staff_required
def staff_booklist(request):
    books = Book.objects.prefetch_related('genres').all().order_by('-created_at')
    genres = Genre.objects.all()
    return render(request, 'staff/listofbooks.html', {'books': books, 'genres': genres, 'appbar_title': 'List of Books'})  

def login_user(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        print(f"[Login Attempt] Email: {email}")

        try:
            user_obj = LibraryUser.objects.get(email=email)

            if not user_obj.id_number:
                messages.error(request, "User does not have an associated ID number.")
                print(f"[Login Failed] {email} - No associated ID number.")
                return render(request, "myserver/loginuser.html")

            user = authenticate(request, email=email, password=password)
            print(f"[Authenticate Result - User Login] {user} ({type(user)})")

            if user is not None and isinstance(user, LibraryUser):
                login(request, user) 

                request.session['session_id'] = str(uuid.uuid4())
                request.session['user_email'] = user_obj.email 
                request.session['is_user'] = True

                UserSessionLog.objects.create(
                    library_user=user_obj,  
                    session_id=request.session['session_id'],
                    action="Login"
                )

                print(f"[Login Success] {user_obj.email} | Session ID: {request.session['session_id']}")

                print(f"[Before Redirect] Session: {request.session.items()}")
                return redirect('user_home')

            else:
                messages.error(request, "Invalid password. Please try again.")

        except LibraryUser.DoesNotExist:
            messages.error(request, "Email address not found. Please try again.")

    return render(request, "myserver/loginuser.html")

def user_signup(request):
    if request.method == "POST":
        form = LibraryUserSignupForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.role = "user"
            user.save()

            otp_code = user.generate_otp()
            user.otp_code = otp_code
            user.otp_expiry = timezone.now() + timezone.timedelta(minutes=10)
            user.save()

            otp_url = request.build_absolute_uri(reverse('otp_confirm'))

            logo_path = os.path.join(settings.BASE_DIR, 'myserver', 'static', 'assets', 'official_logo.png')
            with open(logo_path, 'rb') as f:
                logo_data = f.read()
                encoded_logo = base64.b64encode(logo_data).decode()

            attachment = Attachment()
            attachment.file_content = FileContent(encoded_logo)
            attachment.file_type = FileType('image/png')
            attachment.file_name = FileName('official_logo.png')
            attachment.disposition = Disposition('inline')
            attachment.content_id = ContentId('librarylinklogo')

            html_content = f"""
            <html>
            <head>
                <style>
                @media only screen and (max-width: 600px) {{
                    .container {{
                        padding: 20px !important;
                    }}
                    .btn {{
                        padding: 12px 20px !important;
                        font-size: 16px !important;
                    }}
                }}
                body {{
                    font-family: Arial, sans-serif;
                    background-color: #f2f4f6;
                    margin: 0;
                    padding: 0;
                }}
                .container {{
                    background-color: #ffffff;
                    max-width: 600px;
                    margin: 40px auto;
                    padding: 40px;
                    border-radius: 8px;
                    box-shadow: 0 0 10px rgba(0, 0, 0, 0.08);
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                }}
                .logo {{
                    width: 120px;
                    height: auto;
                }}
                h1 {{
                    color: #1a73e8;
                    font-size: 24px;
                    margin-bottom: 10px;
                }}
                p {{
                    font-size: 16px;
                    color: #333333;
                    line-height: 1.5;
                }}
                .otp-code {{
                    font-size: 24px;
                    font-weight: bold;
                    color: #1a73e8;
                    margin: 20px 0;
                    text-align: center;
                }}
                .btn-container {{
                    text-align: center;
                }}
                .btn {{
                    display: inline-block;
                    padding: 14px 28px;
                    background-color: #1a73e8;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    font-size: 16px;
                    font-weight: bold;
                    margin-top: 20px;
                }}
                .footer {{
                    font-size: 12px;
                    color: #888888;
                    margin-top: 40px;
                    text-align: center;
                }}
                .legal {{
                    margin-top: 20px;
                    font-size: 11px;
                    color: #aaa;
                    line-height: 1.4;
                    text-align: center;
                }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <img src="cid:librarylinklogo" alt="Library Link Logo" class="logo">
                        <h1>Welcome to Library Link, {user.full_name}!</h1>
                    </div>
                    <p>Thank you for registering with Library Link.</p>
                    <p>To activate your account, please use the one-time password (OTP) below. This code is valid for the next 10 minutes:</p>
                    <div class="otp-code">{otp_code}</div>
                    <p class="btn-container">
                        <a href="{otp_url}" class="btn">Verify OTP</a>
                    </p>
                    <div class="footer">
                        <p>If you did not create this account, you can safely ignore this email.</p>
                        <p>Library Link &copy; {timezone.now().year}</p>
                    </div>
                    <div class="legal">
                        <p>This service is currently in <strong>beta</strong>. Features and availability may change without notice.</p>
                        <p>Use of this service is subject to our <a href="#">Terms of Service</a> and <a href="#">Privacy Policy</a>.</p>
                        <p>All rights reserved. Powered by Library Link Team.</p>
                    </div>
                </div>
            </body>
            </html>
            """

            message = Mail(
                from_email=settings.DEFAULT_FROM_EMAIL,
                to_emails=user.email,
                subject="Library Link Account - Email Address OTP Confirmation",
                plain_text_content=f"Hi {user.full_name},\n\nYour OTP code is: {otp_code}",
                html_content=html_content
            )

            message.attachment = attachment

            try:
                os.environ['SSL_CERT_FILE'] = certifi.where()
                sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
                response = sg.send(message)
                print(f"OTP email sent successfully! Response code: {response.status_code}")
            except Exception as e:
                print(f"Error sending OTP email: {str(e)}")

            messages.success(request, "You’ve successfully registered! Please check your email for the OTP code to confirm your account.")
            return redirect('otp_confirm')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = LibraryUserSignupForm()

    return render(request, "myserver/signupuser.html", {'form': form})

@user_required
def user_home(request):
    # view = request.GET.get('view', 'grid')

    # if view == 'favorites':
    #     book_list = Book.objects.filter(favorite_by=request.user)
    # elif view == 'pending':
    #     book_list = Book.objects.filter(pending_user=request.user)
    # else:  
    #     book_list = Book.objects.filter(recently_viewed_by=request.user)

    # paginator = Paginator(book_list, 12)
    # page_number = request.GET.get('page')
    # books = paginator.get_page(page_number)

    # return render(request, 'user/bookshelf.html', {
    #     'view': view,
    #     'book_list': books,
    #     'books': books,
    # })
    return render(request, 'user/home.html', { 'appbar_title': 'My Bookshelf' })

@user_required
def user_booking(request):
    return render(request, 'user/bookingsummary.html', { 'appbar_title': 'Booking Summary' })

@user_required
def user_library(request):
    genre_id = request.GET.get('genre', None)
    search_term = request.GET.get('searchTerm', '').strip()

    if genre_id:
        books_qs = Book.objects.filter(genres__id=genre_id)
        genres = Genre.objects.filter(id=genre_id).prefetch_related(
            Prefetch('books', queryset=books_qs)
        )
    else:
        books_qs = Book.objects.all()
        genres = Genre.objects.prefetch_related(
            Prefetch('books', queryset=books_qs)
        )

    if search_term:
        books_qs = books_qs.filter(
            Q(title__icontains=search_term) | 
            Q(author__icontains=search_term) | 
            Q(isbn__icontains=search_term) | 
            Q(publisher__icontains=search_term) | 
            Q(published_date__icontains=search_term) | 
            Q(barcode_code__icontains=search_term) | 
            Q(copies__icontains=search_term)
        )

        genres = genres.filter(
            Q(name__icontains=search_term)
        )

    all_genres = Genre.objects.all()

    context = {
        'genres': genres,          
        'all_genres': all_genres,  
        'books': books_qs,        
        'search_term': search_term,
        'appbar_title': 'Library',
    }
    return render(request, 'user/library.html', context)

@user_required
def book_detail(request, pk):
    book = get_object_or_404(Book, pk=pk)
    return render(request, 'user/components/bookdetails.html', {'book': book})

@staff_required
def logout_staff(request):
    staff_id = request.session.get('staff_id')
    session_id = request.session.get('session_id')

    if staff_id and session_id:
        try:
            staff = Staff.objects.get(staff_id=staff_id)
            StaffSessionLog.objects.create(
                staff=staff,
                session_id=session_id,
                action="Logout"
            )
        except Staff.DoesNotExist:
            pass

    request.session.pop('is_staff', None)
    request.session.pop('session_id', None)
    request.session.pop('staff_id', None)
    logout(request)
    return redirect('login_staff')


@user_required
def logout_user(request):
    user_email = request.session.get('user_email')
    session_id = request.session.get('session_id')

    if user_email and session_id:
        try:
            user = LibraryUser.objects.get(email=user_email)
            UserSessionLog.objects.create(
                library_user=user,
                session_id=session_id,
                action="Logout"
            )
        except LibraryUser.DoesNotExist:
            pass

    request.session.pop('is_user', None)
    request.session.pop('session_id', None)
    request.session.pop('user_email', None)
    logout(request)
    return redirect('login_user') 



# Create your views here.
