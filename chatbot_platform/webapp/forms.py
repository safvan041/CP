from django import forms
from core.models import KnowledgeBase, KnowledgeBaseSourceFile 
from django.contrib.auth.models import User




class KnowledgeBaseForm(forms.ModelForm):

    # files = forms.FileField(
        
    #     label="Upload Source Files",
    #     help_text="Select one or more .txt, .pdf, or .docx files."
    # )

    class Meta:
        model = KnowledgeBase
        fields = ['title'] 

    # Optionally, you can add custom validation to restrict file types, size, etc.
    # def clean_files(self): 
    #     uploaded_files = self.cleaned_data.get('files')
    #     if not uploaded_files:
    #         raise forms.ValidationError("Please upload at least one file for the Knowledge Base.")

    #     allowed_extensions = ['.txt', '.pdf', '.docx']
    #     for uploaded_file in uploaded_files:
    #         ext = '.' + uploaded_file.name.split('.')[-1].lower()
    #         if f'.{extension}' not in allowed_extensions:
    #             raise forms.ValidationError(f"File '{uploaded_file.name}' has an unsupported type. Only {', '.join(allowed_extensions)} are allowed.")
            
    #         # Example: Add file size limit (e.g., 50MB per file)
    #         if uploaded_file.size > 50 * 1024 * 1024: # 50 MB
    #             raise forms.ValidationError(f"File '{uploaded_file.name}' is too large. Max size is 50MB.")
    #     return uploaded_files
