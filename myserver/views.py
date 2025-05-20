# myserver/views.
import os, certifi, uuid, base64
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from myDjangoAdmin.models import Staff, Admin, LibraryUser, StaffSessionLog, UserSessionLog, Genre, Book
from myserver.decorators import staff_required, user_required
from myserver.forms import LibraryUserSignupForm, BookForm, ForgotPasswordForm, ResetPasswordForm
from django.db.models import Prefetch, Q
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition, ContentId
from django.conf import settings
from django.utils import timezone
from django.urls import reverse
from .models import FavoriteBook, RecentlyViewed, BookingCart, BorrowedBook, ReservedBook
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import FavoriteBook
from myDjangoAdmin.serializers import BookSerializer

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def favorite_books(request, user_id):
    favorites = FavoriteBook.objects.filter(user__id=user_id).select_related('book')
    books = [fav.book for fav in favorites]
    serializer = BookSerializer(books, many=True)
    return Response(serializer.data)

@require_POST
@user_required
def toggle_favorite(request):
    book_id = request.POST.get('book_id')
    if not book_id:
        return JsonResponse({'error': 'Missing book ID'}, status=400)

    try:
        book = Book.objects.get(pk=book_id)
        fav, created = FavoriteBook.objects.get_or_create(user=request.user, book=book)
        if not created:
            fav.delete()
            return JsonResponse({'status': 'removed'})
        return JsonResponse({'status': 'added'})
    except Book.DoesNotExist:
        return JsonResponse({'error': 'Book not found'}, status=404)

def otp_confirm(request):
    if request.user.is_authenticated:
        if not request.user.is_staff:
            return redirect('user_home')
        else:
            return render(request, "myserver/components/loginasauserrequired.html")

    email = request.session.get('email_for_otp', None)
    if not email:
        messages.error(request, "No email found for OTP confirmation.")
        return redirect('user_signup')

    if request.method == 'POST':
        otp_code = request.POST.get('otp_code')
        try:
            user = LibraryUser.objects.get(email=email, otp_code=otp_code)
            if user.is_otp_valid(otp_code):
                user.is_active = True
                user.otp_code = None
                user.otp_expiry = None
                user.save()
                messages.success(request, "Your account has been verified! You can now log in.")
                request.session.pop('email_for_otp', None)
                return redirect('login_user')
            else:
                messages.error(request, "Invalid or expired OTP.")
        except LibraryUser.DoesNotExist:
            messages.error(request, "Invalid OTP.")

    return render(request, "myserver/components/otpconfirm.html", {'email': email})


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

        email = request.POST.get('email')
        full_name = request.POST.get('full_name')
        id_number = request.POST.get('id_number')

        if LibraryUser.objects.filter(email=email).exists() or \
           Staff.objects.filter(email=email).exists() or \
           Admin.objects.filter(email=email).exists():
            pass

        name_parts = full_name.strip().split()
        first_name = name_parts[0]
        last_name = name_parts[-1] if len(name_parts) > 1 else ""

        if LibraryUser.objects.filter(full_name=full_name).exists() or \
           Staff.objects.filter(first_name=first_name, last_name=last_name).exists() or \
           Admin.objects.filter(first_name=first_name, last_name=last_name).exists():
            form.add_error('full_name', "Library user with this Name already exists.")

        if LibraryUser.objects.filter(id_number=id_number).exists() or \
           Staff.objects.filter(staff_id=id_number).exists():
            pass

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
                    font-size: 10px;
                    color: #aaa;
                    line-height: 1.2;
                    text-align: justify;
                }}
                .legal .inline {{
                    display: inline-block;
                    margin-right: 20px;
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
                        <a href="{otp_url}" class="btn" style="color: white;">Verify OTP</a>
                    </p>
                    <div class="footer">
                        <p>If you did not request a password reset, you can ignore this email.</p>
                    </div>
                    <div class="legal">
                        <p>This service is currently in its <strong>beta</strong> version. Features and availability may change without notice.</p>
                        <p>Use of this service is subject to our <a href="#">Terms of Service</a> and <a href="#">Privacy Policy</a>.</p>
                        <p class="inline">All rights reserved. Powered by Library Link Team.</p>
                        <p class="inline">Library Link &copy; {timezone.now().year}</p>
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
            request.session['email_for_otp'] = user.email
            return redirect('otp_confirm')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = LibraryUserSignupForm()

    return render(request, "myserver/signupuser.html", {'form': form})

def forgot_password_request(request):
    if request.method == "POST":
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = LibraryUser.objects.get(email=email)
            except LibraryUser.DoesNotExist:
                messages.error(request, "No account found with this email.")
                return redirect('forgot_password')

            otp_code = user.generate_otp()
            user.otp_code = otp_code
            user.otp_expiry = timezone.now() + timezone.timedelta(minutes=10)
            user.save()

            reset_url = request.build_absolute_uri(reverse('reset_password')) + f"?email={email}"

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
                            font-size: 10px;
                            color: #aaa;
                            line-height: 1.2;
                            text-align: justify;
                        }}
                        .legal .inline {{
                            display: inline-block;
                            margin-right: 20px;
                        }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <img src="cid:librarylinklogo" alt="Library Link Logo" class="logo">
                            <h1>Password Reset Requested</h1>
                        </div>
                        <p>Hi {user.full_name},</p>
                        <p>You requested to reset your Library Link password. Use the OTP below to proceed:</p>
                        <div class="otp-code">{otp_code}</div>
                        <p class="btn-container">
                            <a href="{reset_url}" class="btn" style="color: white;">Reset Password</a>
                        </p>
                        <div class="footer">
                            <p>If you did not request a password reset, you can ignore this email.</p>
                        </div>
                        <div class="legal">
                            <p>This service is currently in its <strong>beta</strong> version. Features and availability may change without notice.</p>
                            <p>Use of this service is subject to our <a href="#">Terms of Service</a> and <a href="#">Privacy Policy</a>.</p>
                            <p class="inline">All rights reserved. Powered by Library Link Team.</p>
                            <p class="inline">Library Link &copy; {timezone.now().year}</p>
                        </div>
                    </div>
                </body>
            </html>
            """

            message = Mail(
                from_email=settings.DEFAULT_FROM_EMAIL,
                to_emails=user.email,
                subject="Library Link - Password Reset OTP",
                plain_text_content=f"Hi {user.full_name},\n\nYour OTP is: {otp_code}",
                html_content=html_content
            )

            message.attachment = attachment

            try:
                os.environ['SSL_CERT_FILE'] = certifi.where()
                sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
                sg.send(message)
                messages.success(request, "OTP sent to your email. Please check and proceed to reset your password.")
                return redirect(f"{reverse('reset_password')}?email={email}")
            except Exception as e:
                messages.error(request, f"Email error: {str(e)}")

    else:
        form = ForgotPasswordForm()

    return render(request, "myserver/components/forgotpassword.html", {"form": form})

def reset_password(request):
    email = request.GET.get("email") or request.POST.get("email")
    if request.method == "POST":
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            otp = form.cleaned_data["otp"]
            new_password = form.cleaned_data["new_password"]
            try:
                user = LibraryUser.objects.get(email=email)
                if user.is_otp_valid(otp):
                    user.set_password(new_password)
                    user.otp_code = None
                    user.otp_expiry = None
                    user.save()
                    messages.success(request, "Password reset successful. You may now log in.")
                    return redirect("login_user")
                else:
                    messages.error(request, "Invalid or expired OTP.")
            except LibraryUser.DoesNotExist:
                messages.error(request, "Invalid email address.")
    else:
        form = ResetPasswordForm(initial={"email": email})
    return render(request, "myserver/components/resetpassword.html", {"form": form})

@user_required
def user_home(request):
    user = request.user
    view = request.GET.get('view', 'grid')

    if view == 'favorites':
        book_list = Book.objects.filter(favoritebook__user=user)
    elif view == 'pending':
        book_list = Book.objects.filter(in_carts__user=user).order_by('-in_carts__added_at')
    else:  
        book_list = Book.objects.filter(recentlyviewed__user=user).order_by('-recentlyviewed__viewed_at')

    recently_viewed = RecentlyViewed.objects.filter(user=user).select_related('book').order_by('-viewed_at')[:10]

    paginator = Paginator(book_list, 12)  
    page_number = request.GET.get('page')
    books_page = paginator.get_page(page_number)

    return render(request, 'user/home.html', {
        'view': view,
        'book_list': books_page,
        'books': books_page, 
        'recently_viewed': recently_viewed,
        'appbar_title': 'My Bookshelf'
    })

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
    recently_viewed = RecentlyViewed.objects.filter(user=request.user).select_related('book')[:10]

    context = {
        'genres': genres,          
        'all_genres': all_genres,  
        'books': books_qs,        
        'search_term': search_term,
        'recently_viewed': [entry.book for entry in recently_viewed],
        'appbar_title': 'Library',
    }
    return render(request, 'user/library.html', context)

@user_required
def clear_recently_viewed(request):
    RecentlyViewed.objects.filter(user=request.user).delete()
    return redirect('user_library')

@user_required
def book_detail(request, pk):
    book = get_object_or_404(Book, pk=pk)

    images = []
    if book.cover_image:
        images.append(book.cover_image.url)
    for extra_img in [
        book.extra_image_1,
        book.extra_image_2,
        book.extra_image_3,
        book.extra_image_4,
        book.extra_image_5,
    ]:
        if extra_img:
            images.append(extra_img.url)

    barcode_url = book.barcode_image.url if book.barcode_image else None
    is_favorite = FavoriteBook.objects.filter(user=request.user, book=book).exists()

    RecentlyViewed.objects.update_or_create(
        user=request.user,
        book=book,
        defaults={'viewed_at': timezone.now()}
    )

    from_page = request.GET.get('from', None)
    view_name = request.GET.get('view', None)

    context = {
        'book': book,
        'images': images,
        'barcode_url': barcode_url,
        'is_favorite': is_favorite,
        'appbar_title': 'About This Book',
        'from_page': from_page,
        'view_name': view_name,
    }
    return render(request, 'user/components/bookdetails.html', context)

@user_required
def book_cart(request):
    user = request.user

    if request.method == 'POST':
        if 'borrow_book' in request.POST:
            book_id = request.POST.get('borrow_book')

            try:
                cart_item = BookingCart.objects.get(user=user, book_id=book_id)

                borrowed, created = BorrowedBook.objects.get_or_create(
                    user=user,
                    book=cart_item.book,
                    defaults={
                        'borrowed_at': timezone.now(),
                    }
                )

                if created:
                    cart_item.delete()
                    messages.success(request, f"You borrowed '{cart_item.book.title}'.")
                else:
                    messages.warning(request, f"You've already borrowed '{cart_item.book.title}'.")

                return redirect('book_cart')

            except BookingCart.DoesNotExist:
                messages.error(request, "Book not found in your cart.")
                return redirect('book_cart')

        elif 'remove_book' in request.POST:
            book_id = request.POST.get('remove_book')
            BookingCart.objects.filter(user=user, book_id=book_id).delete()
            messages.success(request, "Book removed from cart.")
            return redirect('book_cart')

        elif 'request_booking' in request.POST:
            book_id = request.POST.get('request_booking')

            try:
                cart_item = BookingCart.objects.get(user=user, book_id=book_id)

                reserved, created = ReservedBook.objects.get_or_create(
                    user=user,
                    book=cart_item.book,
                    defaults={'reserved_at': timezone.now()}
                )

                if created:
                    cart_item.delete()
                    messages.success(request, f"You reserved '{cart_item.book.title}'.")
                else:
                    messages.warning(request, f"You already reserved '{cart_item.book.title}'.")

            except BookingCart.DoesNotExist:
                messages.error(request, "Book not found in your cart.")

            return redirect('book_cart')

        elif 'request_booking' in request.POST:
            messages.info(request, "Booking request submitted (mock action).")
            return redirect('book_cart')

    cart_items = BookingCart.objects.filter(user=user).select_related('book')
    suggested_books = list(Book.objects.order_by('?')[:5])

    context = {
        'books': cart_items,
        'suggested_books': suggested_books,
        'appbar_title': 'Book Cart',
    }

    return render(request, 'user/components/bookcart.html', context)

@user_required
@require_POST
def add_to_cart(request):
    book_id = request.POST.get('book_id')
    try:
        book = Book.objects.get(id=book_id)

        if BorrowedBook.objects.filter(user=request.user, book=book).exists():
            return JsonResponse({'status': 'already_borrowed', 'message': 'You have already borrowed this book.'})

        if ReservedBook.objects.filter(user=request.user, book=book).exists():
            return JsonResponse({'status': 'already_reserved', 'message': 'You have already reserved this book.'})

        cart_item, created = BookingCart.objects.get_or_create(user=request.user, book=book)

        if created:
            return JsonResponse({'status': 'added', 'message': 'Book added to your cart!'})
        else:
            return JsonResponse({'status': 'already_exists', 'message': 'This book is already in your cart.'})

    except Book.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Book not found'})
    
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
