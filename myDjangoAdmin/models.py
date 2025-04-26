# myDjangoAdmin/models.py
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
import random
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
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(null=True, blank=True)  

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

# Create your models here.
