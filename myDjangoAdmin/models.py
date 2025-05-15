# myDjangoAdmin/models.py
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
import random, uuid, string
from django.db import models
from django.utils import timezone

class AdminManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)  
        extra_fields.setdefault('is_superuser', True) 
        return self.create_user(email, password, **extra_fields)

class Admin(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=True)  
    is_superuser = models.BooleanField(default=True) 
    role = models.CharField(max_length=50, default="Admin")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = AdminManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        """Returns True if the admin user has the given permission."""
        return True  

    def has_module_perms(self, app_label):
        """Returns True if the admin user has access to the given app's permissions."""
        return True  

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='admin_groups', 
        blank=True,
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='admin_permissions',  
        blank=True,
    )

class StaffManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', False) 
        return self.create_user(email, password, **extra_fields)

class Staff(AbstractBaseUser, PermissionsMixin):
    staff_id = models.CharField(max_length=12, unique=True, blank=True, null=True)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    middle_name = models.CharField(max_length=50, blank=True, null=True)
    age = models.IntegerField()
    birthday = models.DateField()
    address = models.TextField()
    role = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_seen = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=True) 
    is_superuser = models.BooleanField(default=False)  

    objects = StaffManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'age', 'birthday', 'address', 'role']

    def __str__(self):
        return self.email

    def generate_staff_id(self):
        current_year = timezone.now().year
        random_digits = str(random.randint(100000, 999999))

        return f"{current_year}{random_digits}"

    def save(self, *args, **kwargs):
        if not self.staff_id:
            self.staff_id = self.generate_staff_id()
        super().save(*args, **kwargs)

    def time_since_last_seen(self):
        if self.last_seen:
            time_diff = timezone.now() - self.last_seen
            if time_diff < timezone.timedelta(seconds=60):
                return "Online"
            elif time_diff < timezone.timedelta(hours=1):
                return f"Offline {time_diff.seconds // 60} minute(s) ago"
            elif time_diff < timezone.timedelta(days=1):
                return f"Offline {time_diff.seconds // 3600} hour(s) ago"
            else:
                return f"Offline {time_diff.days} day(s) ago"
        else:
            return "Offline"

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='staff_groups',
        blank=True,
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='staff_permissions', 
        blank=True,
    )

class StaffSessionLog(models.Model):
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='session_logs')
    session_id = models.CharField(max_length=40)
    action = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.staff.email} | {self.action} | {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
            
class LibraryUserManager(BaseUserManager):
    def create_user(self, email, full_name, id_number, password=None, **extra_fields):
        if not email:
            raise ValueError('Users must have an email address')
        if not full_name:
            raise ValueError('Users must have a full name')
        if not id_number:
            raise ValueError('Users must have an ID number')

        email = self.normalize_email(email)
        user = self.model(
            email=email,
            full_name=full_name,
            id_number=id_number,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, full_name, id_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(
            email,
            full_name=full_name,
            id_number=id_number,
            password=password,
            **extra_fields
        )

class LibraryUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255)
    id_number = models.CharField(max_length=50, unique=True)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(null=True, blank=True) 

    otp_code = models.CharField(max_length=6, null=True, blank=True)
    otp_expiry = models.DateTimeField(null=True, blank=True)

    objects = LibraryUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name', 'id_number']

    def __str__(self):
        return self.email

    def time_since_last_seen(self):
        if self.last_seen:
            time_diff = timezone.now() - self.last_seen
            if time_diff < timezone.timedelta(seconds=60):
                return "Online"
            elif time_diff < timezone.timedelta(hours=1):
                return f"Offline {time_diff.seconds // 60} minute(s) ago"
            elif time_diff < timezone.timedelta(days=1):
                return f"Offline {time_diff.seconds // 3600} hour(s) ago"
            else:
                return f"Offline {time_diff.days} day(s) ago"
        else:
            return "Offline"
        
    def generate_otp(self, length=6):
        """Generate a random OTP code."""
        return ''.join(random.choices(string.digits, k=length))

    def is_otp_valid(self, otp_code):
        """Check if OTP is valid and not expired."""
        if self.otp_expiry and timezone.now() < self.otp_expiry:
            return self.otp_code == otp_code
        return False
    
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='user_groups',  
        blank=True,
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='user_permissions', 
        blank=True,
    )

class UserSessionLog(models.Model):
    library_user = models.ForeignKey(LibraryUser, on_delete=models.CASCADE, related_name='session_logs')
    session_id = models.CharField(max_length=40)
    action = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.library_user.email} | {self.action} | {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
    
class Genre(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Book(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    genres = models.ForeignKey(Genre, related_name='books', on_delete=models.CASCADE, null=True, blank=True)
    isbn = models.CharField(max_length=20, blank=True, null=True)
    publisher = models.CharField(max_length=255)
    published_date = models.DateField(blank=True, null=True)
    copies = models.PositiveIntegerField()
    cover_image = models.ImageField(upload_to='book_covers/')
    extra_image_1 = models.ImageField(upload_to='book_extra_images/', blank=True, null=True)
    extra_image_2 = models.ImageField(upload_to='book_extra_images/', blank=True, null=True)
    extra_image_3 = models.ImageField(upload_to='book_extra_images/', blank=True, null=True)
    extra_image_4 = models.ImageField(upload_to='book_extra_images/', blank=True, null=True)
    extra_image_5 = models.ImageField(upload_to='book_extra_images/', blank=True, null=True)
    barcode_code = models.CharField(max_length=100, unique=True)
    barcode_image = models.ImageField(upload_to='book_barcodes/', blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
    
# class BookRequest(models.Model):
#     user = models.ForeignKey(LibraryUser, on_delete=models.CASCADE, related_name='book_requests')
#     book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='requests')
#     status = models.CharField(max_length=20, choices=[
#         ('pending', 'Pending'),
#         ('approved', 'Approved'),
#         ('rejected', 'Rejected'),
#         ('borrowed', 'Borrowed'),
#         ('returned', 'Returned')
#     ], default='pending')
#     quantity = models.PositiveIntegerField(default=1)
#     request_date = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f"{self.user.email} - {self.book.title} ({self.status})"


# Create your models here.
