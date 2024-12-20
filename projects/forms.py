from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Project, Issue, JoinRequest, User, CalendarEvent, Comment

class ProjectForm(forms.ModelForm):
    due_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="Due Date"
    )
    class Meta:
        model = Project
        fields = ['name', 'description', 'due_date']  

class IssueForm(forms.ModelForm):
    due_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False)
    class Meta:
        model = Issue
        fields = ['title', 'description', 'status', 'assigned_to', 'due_date']

class JoinRequestForm(forms.ModelForm):
    class Meta:
        model = JoinRequest
        fields = []

class FileUploadForm(forms.Form):
    title = forms.CharField(max_length=255)
    description = forms.CharField(widget=forms.Textarea)
    keywords = forms.CharField(max_length=255)
    file = forms.FileField()

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user

class CalendarEventForm(forms.ModelForm):
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))

    class Meta:
        model = CalendarEvent
        fields = ['title', 'start_date', 'end_date', 'is_meeting']

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']