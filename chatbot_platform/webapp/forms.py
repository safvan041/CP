from django import forms
from core.models import KnowledgeBase
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class KnowledgeBaseForm(forms.ModelForm):
    class Meta:
        model = KnowledgeBase
        fields = ['title', 'file']

    # Optionally, you can add custom validation to restrict file types, size, etc.
    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Allow only certain file extensions (optional)
            allowed_extensions = ['.txt', '.pdf', '.docx', '.doc']
            extension = file.name.split('.')[-1].lower()
            if f'.{extension}' not in allowed_extensions:
                raise forms.ValidationError("Unsupported file format. Only .txt, .pdf, .docx  files are allowed.")
        return file

class CustomUserCreationForm(UserCreationForm):
    """
    A custom user creation form that extends Django's UserCreationForm
    to apply AUTH_PASSWORD_VALIDATORS during signup.
    """
    email = forms.EmailField(required=True, label="Email Address")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email',) # Add 'email' to the default fields
                                                        # UserCreationForm.Meta.fields already includes 'username' and 'password'

    # ensuring email is unique:
    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with that email address already exists.")
        return email