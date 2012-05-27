from django import forms
from categories.models import Category

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ('name', 'description', 'image', 'sort_order',)

    def __init__(self, *args, **kwargs):
        super(CategoryForm, self).__init__(*args, **kwargs)
        self.fields['name'].error_messages['required'] = 'Please enter name'
        self.fields['sort_order'].error_messages['required'] = 'Please enter sort order'
