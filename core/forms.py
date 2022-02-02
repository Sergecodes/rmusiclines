from django import forms

from accounts.models.artists.models import ArtistPhoto


class ArtistPhotoForm(forms.ModelForm):
    class Meta:
        model = ArtistPhoto
        fields = ['photo']

    def clean_photo(self):
        print("about to clean photo")
        print(self.cleaned_data)
        return self.cleaned_data['photo']

    def clean(self):
        print(self.data)
        print(self.cleaned_data)
        print(self.fields)
        print(self.files)
        print(self.errors)
        print(self.non_field_errors())
