import os, certifi, uuid, base64, json, traceback
from django.conf import settings
from django.http import JsonResponse, HttpResponseNotFound
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils.crypto import get_random_string
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.core.paginator import Paginator
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import api_view, permission_classes
from myDjangoAdmin.models import Staff, Admin, LibraryUser, StaffSessionLog, UserSessionLog, Genre, Book
from myDjangoAdmin.serializers import BookSerializer, GenreSerializer
from myserver.decorators import staff_required, user_required
from myserver.forms import LibraryUserSignupForm, BookForm, ForgotPasswordForm, ResetPasswordForm
from django.shortcuts import render, redirect, get_object_or_404
from sendgrid import SendGridAPIClient
from .models import FavoriteBook
from .models import FavoriteBook, RecentlyViewed, BookingCart, BorrowedBook, ReservedBook
from sendgrid.helpers.mail import Mail, Email, To, Attachment, FileContent, FileName, FileType, Disposition, ContentId, Content
from django.db.models import Prefetch, Q
from itertools import chain
from operator import attrgetter
from types import SimpleNamespace
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.decorators import login_required

@api_view(['POST'])
@permission_classes([AllowAny])
def signup_user(request):
    email = request.data.get('email')
    full_name = request.data.get('full_name')
    id_number = request.data.get('id_number')
    password = request.data.get('password')

    if not all([email, full_name, id_number, password]):
        return Response({"success": False, "error": "All fields are required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        validate_password(password)
    except ValidationError as e:
        return Response({"success": False, "error": e.messages[0]}, status=status.HTTP_400_BAD_REQUEST)

    if LibraryUser.objects.filter(email=email).exists() or \
       Staff.objects.filter(email=email).exists() or \
       Admin.objects.filter(email=email).exists():
        return Response({"success": False, "error": "Email already in use."}, status=status.HTTP_400_BAD_REQUEST)

    name_parts = full_name.strip().split()
    first_name = name_parts[0]
    last_name = name_parts[-1] if len(name_parts) > 1 else ""

    if LibraryUser.objects.filter(full_name=full_name).exists() or \
       Staff.objects.filter(first_name=first_name, last_name=last_name).exists() or \
       Admin.objects.filter(first_name=first_name, last_name=last_name).exists():
        return Response({"success": False, "error": "Full name already exists."}, status=status.HTTP_400_BAD_REQUEST)

    if LibraryUser.objects.filter(id_number=id_number).exists() or \
       Staff.objects.filter(staff_id=id_number).exists():
        return Response({"success": False, "error": "ID number already in use."}, status=status.HTTP_400_BAD_REQUEST)

    user = LibraryUser(
        email=email,
        full_name=full_name,
        id_number=id_number,
        is_active=False
    )
    user.set_password(password)
    user.save()

    otp_code = user.generate_otp()
    user.otp_code = otp_code
    user.otp_expiry = timezone.now() + timezone.timedelta(minutes=10)
    user.save()

    logo_path = os.path.join(settings.BASE_DIR, 'myserver', 'static', 'assets', 'official_logo.png')
    try:
        with open(logo_path, 'rb') as f:
            logo_data = f.read()
            encoded_logo = base64.b64encode(logo_data).decode()
    except FileNotFoundError:
        return Response({"success": False, "error": "Logo file missing on server."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
            .container {{ padding: 20px !important; }}
            .otp-code {{ font-size: 22px !important; }}
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
          .header {{ text-align: center; margin-bottom: 30px; }}
          .logo {{ width: 120px; height: auto; }}
          h1 {{ color: #1a73e8; font-size: 24px; margin-bottom: 10px; }}
          p {{ font-size: 16px; color: #333333; line-height: 1.5; }}
          .otp-code {{
            font-size: 26px;
            font-weight: bold;
            color: #1a73e8;
            margin: 20px 0;
            text-align: center;
            letter-spacing: 2px;
          }}
          .footer {{ font-size: 12px; color: #888888; margin-top: 40px; text-align: center; }}
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
            <h1>Welcome to Library Link</h1>
          </div>
            <p>Hi {user.full_name},</p>
            <p>Thank you for registering with Library Link.</p>
            <p>To activate your new account, please use the one-time password (OTP) below. This code is valid for the next 10 minutes:</p>
          <div class="otp-code">{user.otp_code}</div>
          <p>Please open the app and enter this code to complete your signup process.</p>
          <div class="footer">
            <p>If you did not sign up for an account, please ignore this email.</p>
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
        plain_text_content=f"Hi {user.full_name},\n\nYour OTP code is: {otp_code}\nIt expires in 10 minutes.",
        html_content=html_content
    )
    message.attachment = attachment

    try:
        os.environ['SSL_CERT_FILE'] = certifi.where()
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sg.send(message)
        print(f"OTP email sent. Status: {response.status_code}")
    except Exception as e:
        print(f"SendGrid error: {str(e)}")

    return Response({"success": True, "message": "Account created. OTP sent via email."}, status=status.HTTP_201_CREATED)

def approve_reserved_book(request, reserved_book_id):
    reserved_book = get_object_or_404(ReservedBook, id=reserved_book_id)
    reserved_book.status = 'approved'
    reserved_book.save()

    messages.success(request, f"Your reservation for '{reserved_book.book.title}' has been approved by staff.")

    return redirect(request, 'user_home')  

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def favorite_books(request, user_id):
    favorites = FavoriteBook.objects.filter(user__id=user_id).select_related('book')
    books = [fav.book for fav in favorites]
    serializer = BookSerializer(books, many=True)
    return Response(serializer.data)

@api_view(["GET"])
def genre_list(request):
    genres = Genre.objects.all().order_by('name')
    return Response(GenreSerializer(genres, many=True).data)

@api_view(["GET"])
def books_by_genre(request):
    search = request.GET.get("search", "")
    user_id = request.GET.get("user_id")

    data = {}
    for genre in Genre.objects.all():
        books = Book.objects.filter(genres=genre)
        if search:
            books = books.filter(Q(title__icontains=search) | Q(author__icontains=search))

        books_data = BookSerializer(books, many=True, context={"request": request}).data

        if user_id:
            favorite_ids = FavoriteBook.objects.filter(user_id=user_id).values_list("book_id", flat=True)
            for book in books_data:
                book["is_favorite"] = book["id"] in favorite_ids

        data[genre.name] = books_data

    return Response(data)

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

def about(request):
    return render(request, 'myserver/about.html')

def privacy_policy(request):
    return render(request, 'myserver/privacypolicy.html', {'page_title': 'Privacy Policy'})

def terms_of_service(request):
    return render(request, 'myserver/termsofservice.html', {'page_title': 'Terms of Service'})

def report_issue(request):
    if request.method == "POST":
        user_email = request.POST.get("email", "").strip()
        issue_message = request.POST.get("message", "").strip()

        if not issue_message:
            messages.error(request, "Please provide a description of the issue.")
            return redirect('report_issue')

        subject = "Library Link - New Issue Reported"
        from_email = settings.DEFAULT_FROM_EMAIL
        to_email = settings.SUPPORT_EMAIL  

        body_html = f"""
        <html>
            <body>
                <h3>New Issue Submitted</h3>
                <p><strong>From:</strong> {user_email or 'Not provided'}</p>
                <p><strong>Message:</strong></p>
                <p>{issue_message.replace('\n', '<br>')}</p>
            </body>
        </html>
        """

        message = Mail(
            from_email=Email(from_email),
            to_emails=To(to_email),
            subject=subject,
            html_content=Content("text/html", body_html)
        )

        try:
            os.environ['SSL_CERT_FILE'] = certifi.where()
            sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
            response = sg.send(message)
            print(f"Issue report email sent. Response code: {response.status_code}")
            messages.success(request, "Thank you for reporting the issue! We’ve received your message and our team will review it shortly.")

        except Exception as e:
            print(f"Failed to send issue report email: {str(e)}")
            messages.error(request, "Sorry, there was an error sending your report. Please try again later.")

        return redirect("report_issue")

    return render(request, "myserver/reportissue.html")

def help(request):
    return render(request, 'myserver/help.html', {'page_title': 'Help'})

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
    user_summaries = []
    total_books = Book.objects.count()
    borrowed = BorrowedBook.objects.count()
    unreturned = BorrowedBook.objects.count() 
    users = LibraryUser.objects.count()

    for user in LibraryUser.objects.all():
        borrowed_books = BorrowedBook.objects.filter(user=user).select_related('book')
        reserved_books = ReservedBook.objects.filter(user=user).select_related('book')
        all_books = list({b.book for b in borrowed_books}.union({r.book for r in reserved_books}))
        user_summaries.append({
            'full_name': user.full_name,
            'books': all_books,
            'total_books': len(all_books),
        })

    booking_requests = ReservedBook.objects.filter(status='pending').select_related('user', 'book')

    borrowed_list = [
        SimpleNamespace(
            book=b.book,
            user=b.user,
            status="Borrowed",
            created_at=b.borrowed_at,
            id=b.id
        ) for b in BorrowedBook.objects.select_related('user', 'book')
    ]

    viewed_list = [
        SimpleNamespace(
            book=v.book,
            user=v.user,
            status="Viewed",
            created_at=v.viewed_at,
            id=v.id
        ) for v in RecentlyViewed.objects.select_related('user', 'book')
    ]

    reserved_list = [
        SimpleNamespace(
            book=r.book,
            user=r.user,
            status=r.status.capitalize(),
            created_at=r.reserved_at,
            id=r.id
        ) for r in ReservedBook.objects.select_related('user', 'book')
    ]

    recent_activities = sorted(
        chain(borrowed_list, viewed_list, reserved_list),
        key=attrgetter("created_at"),
        reverse=True
    )[:30]

    context = {
        'user_summaries': user_summaries,
        'total_books': total_books,
        'borrowed': borrowed,
        'unreturned': unreturned,
        'users': users,
        'appbar_title': 'Dashboard',
        'booking_requests': booking_requests,
        'recent_activities': recent_activities,  
    }

    return render(request, 'staff/home.html', context)

@staff_required
def booking_requests_view(request):
    booking_requests = ReservedBook.objects.filter(status='pending').select_related('user', 'book')
    return render(request, 'staff/components/bookingrequeststable.html', {'booking_requests': booking_requests})

@staff_required
@require_POST
@csrf_exempt  
def approve_request(request):
    try:
        data = json.loads(request.body)
        request_id = data.get('request_id')
    except (json.JSONDecodeError, KeyError):
        return JsonResponse({'success': False, 'error': 'Invalid data'})

    try:
        reservation = ReservedBook.objects.get(id=request_id, status='pending')
        reservation.status = 'approved'
        reservation.save()
        return JsonResponse({'success': True})
    except ReservedBook.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Request not found or already processed'})

@staff_required
@require_POST
@csrf_exempt
def cancel_request(request):
    try:
        data = json.loads(request.body)
        request_id = data.get('request_id')
    except (json.JSONDecodeError, KeyError):
        return JsonResponse({'success': False, 'error': 'Invalid data'})

    try:
        reservation = ReservedBook.objects.get(id=request_id, status='pending')
        reservation.status = 'cancelled'
        reservation.save()
        return JsonResponse({'success': True})
    except ReservedBook.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Request not found or already processed'})

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
def add_or_update_book(request, book_id=None):
    if book_id:
        book = get_object_or_404(Book, id=book_id)
    else:
        book = None

    genres = Genre.objects.all()

    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES, instance=book)
        if form.is_valid():
            book = form.save(commit=False)

            for i in range(1, 6):
                setattr(book, f'extra_image_{i}', None)

            extra_images = request.FILES.getlist('extra_images')
            for index, image in enumerate(extra_images[:5], start=1):
                setattr(book, f'extra_image_{index}', image)

            book.save()

            messages.success(request, "Book updated successfully.")
            return redirect('staff_booklist')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = BookForm(instance=book)

    return render(request, 'staff/addnewbook.html', {
        'form': form,
        'book': book,
        'genres': genres,
        'appbar_title': 'Update Book' if book else 'Add New Book',
    })

@staff_required
def delete_book(request, book_id):
    book = get_object_or_404(Book, id=book_id)

    if book.cover_image and os.path.isfile(book.cover_image.path):
        os.remove(book.cover_image.path)

    for i in range(1, 6):
        extra_image = getattr(book, f'extra_image_{i}')
        if extra_image and os.path.isfile(extra_image.path):
            os.remove(extra_image.path)

    if book.barcode_image and os.path.isfile(book.barcode_image.path):
        os.remove(book.barcode_image.path)

    RecentlyViewed.objects.filter(book=book).delete()
    FavoriteBook.objects.filter(book=book).delete()
    BookingCart.objects.filter(book=book).delete()
    BorrowedBook.objects.filter(book=book).delete()
    ReservedBook.objects.filter(book=book).delete()

    book.delete()

    messages.success(request, "Book and all related records deleted successfully.")
    return redirect('staff_addbook')

@staff_required
def staff_barcode(request):
    return render(request, 'staff/barcode.html', { 'appbar_title': 'Barcode' })

@staff_required
def staff_transaction(request):
    status_filter = request.GET.get('status', 'All')

    transactions = BorrowedBook.objects.select_related('user', 'book')

    def annotate_status(tx):
        if tx.returned_at:
            tx.status = 'returned'
        else:
            tx.status = 'borrowed'
        tx.display_title = tx.book.title
        tx.borrower = tx.user.full_name
        tx.borrow_date = tx.borrowed_at.strftime('%Y-%m-%d')
        return tx

    transactions = [annotate_status(tx) for tx in transactions]

    if status_filter != 'All':
        transactions = [tx for tx in transactions if tx.status == status_filter.lower()]

    return render(request, 'staff/transaction.html', {
        'appbar_title': 'Transaction',
        'transactions': transactions
    })

@staff_required
def staff_booklist(request):
    books = Book.objects.prefetch_related('genres').all().order_by('-created_at')
    genres = Genre.objects.all()
    return render(request, 'staff/listofbooks.html', {'books': books, 'genres': genres, 'appbar_title': 'Book Inventory'})  

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

@csrf_exempt
def forgot_password_request_mobile(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method."}, status=405)

    try:
        data = json.loads(request.body)
        email = data.get("email", "").strip()
    except (json.JSONDecodeError, KeyError):
        return JsonResponse({"error": "Invalid JSON or missing email"}, status=400)

    if not email:
        return JsonResponse({"error": "Email is required."}, status=400)

    try:
        user = LibraryUser.objects.get(email=email)
    except LibraryUser.DoesNotExist:
        return JsonResponse({"error": "No user with this email."}, status=404)

    user.otp_code = get_random_string(length=6, allowed_chars="1234567890")
    user.otp_expiry = timezone.now() + timezone.timedelta(minutes=15) 
    user.save()

    html_message = f"""
    <html>
      <head>
        <style>
          @media only screen and (max-width: 600px) {{
            .container {{ padding: 20px !important; }}
            .otp-code {{ font-size: 22px !important; }}
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
          .header {{ text-align: center; margin-bottom: 30px; }}
          .logo {{ width: 120px; height: auto; }}
          h1 {{ color: #1a73e8; font-size: 24px; margin-bottom: 10px; }}
          p {{ font-size: 16px; color: #333333; line-height: 1.5; }}
          .otp-code {{
            font-size: 26px;
            font-weight: bold;
            color: #1a73e8;
            margin: 20px 0;
            text-align: center;
            letter-spacing: 2px;
          }}
          .footer {{ font-size: 12px; color: #888888; margin-top: 40px; text-align: center; }}
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
          <p>You requested to reset your Library Link password. Use the one-time password (OTP) below in the mobile app to continue:</p>
          <div class="otp-code">{user.otp_code}</div>
          <p>Please open the app and enter this code to proceed. The OTP is valid for a limited time.</p>
          <div class="footer">
            <p>If you did not request a password reset, you can safely ignore this email.</p>
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

    try:
        message = Mail(
            from_email=settings.DEFAULT_FROM_EMAIL,
            to_emails=user.email,
            subject="Password Reset OTP",
            html_content=html_message,
        )

        logo_path = os.path.join(settings.BASE_DIR, "static", "images", "library-official-logo.png")
        if os.path.exists(logo_path):
            with open(logo_path, "rb") as f:
                data = f.read()
                encoded = base64.b64encode(data).decode()
            attachment = Attachment()
            attachment.file_content = FileContent(encoded)
            attachment.file_type = FileType("image/png")
            attachment.file_name = FileName("library-official-logo.png")
            attachment.disposition = Disposition("inline")
            attachment.content_id = ContentId("librarylinklogo")
            message.add_attachment(attachment) 

        os.environ['SSL_CERT_FILE'] = certifi.where()
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        sg.send(message)

        return JsonResponse({"message": "OTP sent to your email."}, status=200)

    except Exception as e:
        traceback.print_exc()
        return JsonResponse({"error": "Failed to send email", "detail": str(e)}, status=500)
    
@csrf_exempt
def reset_password_mobile(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method."}, status=405)

    try:
        data = json.loads(request.body)
        email = data.get("email", "").strip()
        otp = data.get("otp", "").strip()
        new_password = data.get("new_password", "").strip()
    except (json.JSONDecodeError, KeyError):
        return JsonResponse({"error": "Invalid JSON or missing fields"}, status=400)

    if not email or not otp or not new_password:
        return JsonResponse({"error": "Email, OTP and new password are required."}, status=400)

    try:
        user = LibraryUser.objects.get(email=email)
    except LibraryUser.DoesNotExist:
        return JsonResponse({"error": "No user with this email."}, status=404)

    if not user.is_otp_valid(otp):
        return JsonResponse({"error": "Invalid or expired OTP."}, status=400)

    user.set_password(new_password)

    user.otp_code = None
    user.otp_expiry = None
    user.save()

    return JsonResponse({"message": "Password has been reset successfully."}, status=200)

@csrf_exempt
def verify_otp_mobile(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method."}, status=405)

    try:
        data = json.loads(request.body)
        email = data.get("email", "").strip()
        otp = data.get("otp", "").strip()
    except (json.JSONDecodeError, KeyError):
        return JsonResponse({"error": "Invalid JSON or missing fields."}, status=400)

    if not email or not otp:
        return JsonResponse({"error": "Email and OTP are required."}, status=400)

    try:
        user = LibraryUser.objects.get(email=email)
    except LibraryUser.DoesNotExist:
        return JsonResponse({"error": "No user with this email."}, status=404)

    if not user.is_otp_valid(otp):
        return JsonResponse({"error": "Invalid or expired OTP."}, status=400)

    user.is_active = True
    user.otp_code = None
    user.otp_expiry = None
    user.save()

    return JsonResponse({"message": "Your account has been verified! You can now log in."}, status=200)

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
def user_borrowinghistory(request):
    user = request.user

    borrowed = BorrowedBook.objects.filter(user=user).select_related('book')
    reserved = ReservedBook.objects.filter(user=user, status='approved').select_related('book')

    history_items = []

    for item in borrowed:
        history_items.append({
            'title': item.book.title,
            'author': item.book.author,
            'activity_date': item.borrowed_at,  
            'tag': "Borrowed",
        })

    for item in reserved:
        history_items.append({
            'title': item.book.title,
            'author': item.book.author,
            'activity_date': item.reserved_at, 
            'tag': "Reserved",
        })

    history_items.sort(key=lambda x: x['activity_date'], reverse=True) 

    return render(request, 'user/borrowinghistory.html', {
        'appbar_title': 'My Borrowing History',
        'history_items': history_items,
    })

@user_required
def user_barcode(request):
    return render(request, 'user/barcode.html', { 'appbar_title': 'Barcode' })

@login_required
@require_POST
def mark_book_returned(request, book_id):
    user = request.user
    try:
        borrowed_instance = BorrowedBook.objects.get(
            book_id=book_id,
            user=user,
            returned_at__isnull=True,
        )
    except BorrowedBook.DoesNotExist:
        return HttpResponseNotFound("No active borrow record found for this book and user.")

    borrowed_instance.returned_at = timezone.now()
    borrowed_instance.save()

    book = borrowed_instance.book

    book.copies = (book.copies or 0) + 1
    book.save()

    response_data = {
        'id': str(book.id),
        'title': book.title,
        'author': book.author,
        'borrowed': False,
        'borrowed_by': None,
        'borrowed_at': None,
        'last_returned': {
            'user': {
                'id': borrowed_instance.user.id,
                'full_name': borrowed_instance.user.full_name,
            },
            'returned_at': borrowed_instance.returned_at.isoformat(),
        },
    }
    return JsonResponse(response_data)

def get_book_by_barcode(request, barcode):
    try:
        book = Book.objects.get(barcode_code=barcode)

        borrowed_instance = BorrowedBook.objects.filter(book=book, returned_at__isnull=True).select_related('user').first()
        last_returned_instance = BorrowedBook.objects.filter(book=book, returned_at__isnull=False).order_by('-returned_at').select_related('user').first()

        response_data = {
            'id': str(book.id),
            'title': book.title,
            'author': book.author,
            'genre': book.genres.name if book.genres else 'Unknown',
            'isbn': book.isbn,
            'published_date': book.published_date.isoformat() if book.published_date else '',
            'description': book.description or '',
            'cover_url': book.cover_image.url if book.cover_image else '',
            'borrowed': False,
            'borrowed_by': None,
            'borrowed_at': None,
            'last_returned': None,
        }

        if borrowed_instance:
            response_data['borrowed'] = True
            response_data['borrowed_by'] = {
                'id': borrowed_instance.user.id,
                'full_name': borrowed_instance.user.full_name,
                'email': borrowed_instance.user.email,
            }
            response_data['borrowed_at'] = borrowed_instance.borrowed_at.isoformat()

        if last_returned_instance:
            response_data['last_returned'] = {
                'user': {
                    'id': last_returned_instance.user.id,
                    'full_name': last_returned_instance.user.full_name,
                },
                'returned_at': last_returned_instance.returned_at.isoformat(),
            }

        return JsonResponse(response_data)

    except Book.DoesNotExist:
        return JsonResponse({'error': 'Book not found'}, status=404)
    
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
        'appbar_title': 'About this Book',
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

                active_borrow = BorrowedBook.objects.filter(
                    user=user,
                    book=cart_item.book,
                    returned_at__isnull=True
                ).first()

                if active_borrow:
                    messages.warning(request, f"You've already borrowed '{cart_item.book.title}'.")
                else:
                    BorrowedBook.objects.create(
                        user=user,
                        book=cart_item.book,
                        borrowed_at=timezone.now()
                    )
                    cart_item.delete()
                    messages.success(request, f"You borrowed '{cart_item.book.title}'.")

                return redirect('book_cart')

            except BookingCart.DoesNotExist:
                messages.error(request, "Book not found in your cart.")
                return redirect('book_cart')

        elif 'remove_book' in request.POST:
            book_id = request.POST.get('remove_book')
            try:
                cart_item = BookingCart.objects.get(user=user, book_id=book_id)
                book = cart_item.book
                book.copies += 1  
                book.save()
                cart_item.delete()
                messages.success(request, f"'{book.title}' removed from cart and copies updated.")
            except BookingCart.DoesNotExist:
                messages.warning(request, "Book was not found in your cart.")
            return redirect('book_cart')

        elif 'request_booking' in request.POST:
            book_id = request.POST.get('request_booking')
            try:
                cart_item = BookingCart.objects.get(user=user, book_id=book_id)

                reserved, created = ReservedBook.objects.get_or_create(
                    user=user,
                    book=cart_item.book,
                    defaults={'reserved_at': timezone.now(), 'status': 'pending'}
                )

                if created:
                    cart_item.delete()
                    messages.info(request, f"You have reserved '{cart_item.book.title}'. Please wait for staff approval.")
                else:
                    if reserved.status == 'pending':
                        messages.warning(request, f"Your reservation for '{reserved.book.title}' is still pending.")
                    elif reserved.status == 'approved':
                        messages.success(request, f"Your reservation for '{reserved.book.title}' has been approved!")
                    else:
                        messages.error(request, f"Your reservation for '{reserved.book.title}' was rejected.")

            except BookingCart.DoesNotExist:
                messages.error(request, "Book not found in your cart.")
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
    user = request.user
    book_id = request.POST.get('book_id')

    try:
        book = Book.objects.get(id=book_id)

        if BorrowedBook.objects.filter(user=request.user, book=book, returned_at__isnull=True).exists():
            return JsonResponse({'status': 'already_borrowed', 'message': 'You have already borrowed this book.'})

        if ReservedBook.objects.filter(user=request.user, book=book).exists():
            return JsonResponse({'status': 'already_reserved', 'message': 'You have already reserved this book.'})
        
        if BookingCart.objects.filter(user=user, book=book).exists():
            return JsonResponse({'status': 'already_exists', 'message': 'This book is already in your cart.'})
        
        if book.copies < 1:
            return JsonResponse({'status': 'no_copies', 'message': 'No available copies of this book.'})

        BookingCart.objects.create(user=user, book=book)
        book.copies -= 1
        book.save()

        return JsonResponse({'status': 'added', 'message': f"'{book.title}' has been added to your cart."})

    except Book.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Book not found'})
    
@user_required
@require_POST
def remove_from_cart(request):
    book_id = request.POST.get('remove_book')
    try:
        cart_item = BookingCart.objects.get(user=request.user, book_id=book_id)
        book = cart_item.book

        cart_item.delete()
        book.copies_available += 1
        book.save()

        messages.success(request, f"'{book.title}' has been removed from your cart.")
    except BookingCart.DoesNotExist:
        messages.error(request, 'Book not found in your cart.')
    except Book.DoesNotExist:
        messages.error(request, 'Book not found.')

    return redirect('book_cart')
    
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

def about(request):
    return render(request, 'myserver/about.html')

def privacy_policy(request):
    return render(request, 'myserver/privacypolicy.html', {'page_title': 'Privacy Policy'})

def terms_of_service(request):
    return render(request, 'myserver/termsofservice.html', {'page_title': 'Terms of Service'})

def report_issue(request):
    return render(request, 'myserver/reportissue.html', {'page_title': 'Report an Issue'})

def help(request):
    return render(request, 'myserver/help.html', {'page_title': 'Help'})

# Create your views here.
