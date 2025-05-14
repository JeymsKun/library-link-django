# myserver/views.py
import uuid
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import HttpResponseRedirect
from myDjangoAdmin.models import Staff, LibraryUser, StaffSessionLog, UserSessionLog, Genre, Book
from django.contrib.auth.hashers import check_password
from myserver.decorators import staff_required, user_required
from myserver.forms import LibraryUserSignupForm, BookForm 
from django.core.paginator import Paginator
from django.db.models import Prefetch, Q
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, Content
from django.conf import settings

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

            # # Create the email content
            # content = Content("text/plain", f"Hi {user.full_name},\n\nYour library account has been successfully created. You can now log in using {user.email}.\n\nEnjoy reading!")

            # # Use Email class for to_email
            # to_email = Email(user.email)

            # message = Mail(
            #     from_email=Email(settings.DEFAULT_FROM_EMAIL),
            #     to_emails=to_email,  # Ensure to use 'to_emails' (plural)
            #     subject="Welcome to the Library!",
            #     content=content  # Use content instead of plain_text_content
            # )

            # try:
            #     # Initialize the SendGrid client with the API key
            #     sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
            #     # Now use the 'send' method from SendGridAPIClient to send the email
            #     response = sg.send(message)
            #     print(f"Email sent successfully! Response code: {response.status_code}")
            # except Exception as e:
            #     print(f"Error sending email: {str(e)}")

            messages.success(request, "You’ve successfully registered as a Library User!")
            return redirect('login_user')  
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
