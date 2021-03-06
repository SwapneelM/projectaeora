from django import forms
from django.forms import ModelForm
from .models import Query, UserPreferences


class QueryForm(ModelForm):
    question = forms.CharField(widget=forms.TextInput(attrs={'autocomplete': 'off', 'placeholder': 'Type a message'}),
                            label='', max_length=256)

    class Meta:
        model = Query
        exclude = ['created_at']


class UserPreferencesForm(ModelForm):
    COLOUR_SCHEME_CHOICES = (
        ('indigo', 'Indigo'),
        ('dark', 'Dark'),
        ('light', 'Light'),
    )

    colour_scheme = forms.ChoiceField(choices=COLOUR_SCHEME_CHOICES, required=False)
    companies = forms.CharField(widget=forms.HiddenInput(), required=False)
    sectors = forms.CharField(widget=forms.HiddenInput(), required=False)
    days_old = forms.IntegerField(label='How old should the news be? (days)',
                    widget=forms.NumberInput(attrs={'type':'range', 'min': 1, 'max': 14}))

    class Meta:
        model = UserPreferences
        fields = '__all__'
