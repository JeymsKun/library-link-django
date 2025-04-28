# myserver/views.py
import uuid
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import HttpResponseRedirect
from myDjangoAdmin.models import Staff, LibraryUser, StaffSessionLog, UserSessionLog
from django.contrib.auth.hashers import check_password
from myserver.decorators import staff_required, user_required
from myserver.forms import LibraryUserSignupForm

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
    return render(request, 'staff/home.html')

@staff_required
def staff_addbook(request):
    return render(request, 'staff/addnewbook.html')

@staff_required
def staff_barcode(request):
    return render(request, 'staff/barcode.html')

@staff_required
def staff_transaction(request):
    return render(request, 'staff/transaction.html')

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
    # book_list = []

    # if view == 'favorites':
    #     book_list = request.user.favorite_books.all() 
    # elif view == 'returned':
    #     book_list = request.user.returned_books.all()  
    # else:
    #     book_list = request.user.recently_viewed_books.all()

    # context = {
    #     'view': view,
    #     'book_list': book_list,
    # }
    # return render(request, 'user/home.html', context)
    return render(request, 'user/home.html')

@user_required
def user_booking(request):
    return render(request, 'user/bookingsummary.html')

@user_required
def user_library(request):
    return render(request, 'user/library.html')

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
