# webapp/forms.py

from django import forms
from core.models import KnowledgeBase
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password # NEW: For manual password validation
from django.core.exceptions import ValidationError # NEW: For validation errors
from django.db import transaction # NEW: For atomic save if needed
from django.contrib.auth.hashers import make_password # NEW: For manually hashing password


class KnowledgeBaseForm(forms.ModelForm):
    class Meta:
        model = KnowledgeBase
        fields = ['title', 'file']

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            allowed_extensions = ['.txt', '.pdf', '.docx', '.doc']
            extension = file.name.split('.')[-1].lower()
            if f'.{extension}' not in allowed_extensions:
                raise forms.ValidationError("Unsupported file format. Only .txt, .pdf, .docx files are allowed.")
        return file

# --- NEW CustomUserCreationForm (Manual Password Handling) ---
class CustomUserCreationForm(forms.ModelForm): # Inherit from forms.ModelForm
    password = forms.CharField(label="Password", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Password confirmation", widget=forms.PasswordInput, help_text="Enter the same password as before, for verification.")
    email = forms.EmailField(required=True, label="Email Address")

    class Meta: # Meta class for forms.ModelForm
        model = User
        fields = ('username', 'email', 'password', 'password2')

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with that email address already exists.")
        return email

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("A user with that username already exists.")
        return username

    # --- NEW: clean_password method to apply password validators ---
    def clean_password(self):
        password = self.cleaned_data.get('password') # Get the password from cleaned data

        if not password: # This usually happens if 'required' is not met.
            # You might still get 'required' from default validation before this,
            # but it's good to be explicit here too.
            raise forms.ValidationError("This field is required.")

        # Run Django's AUTH_PASSWORD_VALIDATORS on the password
        try:
            # For a new user creation, pass user=None as the user instance does not exist yet.
            validate_password(password, user=None) 
        except ValidationError as e:
            # Re-raise the ValidationError to attach it to the 'password' field.
            raise forms.ValidationError(list(e.messages)) 

        return password # Always return the cleaned data

    def clean_password2(self):
        password = self.cleaned_data.get('password') # Get the first password (should be cleaned now)
        password2 = self.cleaned_data.get('password2')

        # Check for password mismatch
        if password and password2 and password != password2:
            raise forms.ValidationError("The two password fields didn't match.")
        
        # We don't run validate_password here anymore, it's done in clean_password.
        return password2

    # Override the default save method to hash the password manually
    def save(self, commit=True):
        user = super().save(commit=False) # Create user object without saving password yet
        user.set_password(self.cleaned_data["password"]) # Hash the password using Django's method
        if commit:
            user.save()
        return user
