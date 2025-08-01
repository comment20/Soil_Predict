from django import forms

class SoilImageForm(forms.Form):
    image = forms.ImageField(
        label="Choisir une image du sol",
        widget=forms.ClearableFileInput(attrs={
            'accept': 'image/*',
            'class': 'custom-file-input'
        })
    )
    



