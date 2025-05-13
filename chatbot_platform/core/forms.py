from django import forms
from .models import KnowledgeBase

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
