from django import forms
from .models import Product,Order,Deal, Contact,CoAdmin
from django.contrib.auth.models import User

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'category', 'description', 'price','commission', 'stock', 'image', 'is_available']



class OrderForm(forms.ModelForm):
    
    province = forms.ChoiceField(
        choices=[
            ('', 'Select Province'),
            ('Province 1', 'Province 1'),
            ('Province 2', 'Province 2'),
            ('Bagmati', 'Bagmati'),
            ('Gandaki', 'Gandaki'),
            ('Lumbini', 'Lumbini'),
            ('Karnali', 'Karnali'),
            ('Sudurpashchim', 'Sudurpashchim'),
        ],
        required=True
    )
    city = forms.CharField(required=True)
    street_address = forms.CharField(required=True, widget=forms.Textarea(attrs={'rows': 2}))
    delivery_instructions = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 2}))
    payment_method = forms.ChoiceField(
        choices=[
            ('cash_on_delivery', 'Cash on Delivery'),
            ('credit_card', 'Credit/Debit Card'),
            ('mobile_payment', 'Mobile Payment'),
            ('bank_transfer', 'Bank Transfer'),
        ],
        required=True
    )
    def clean(self):
        cleaned_data = super().clean()
        province = cleaned_data.get('province')
        city = cleaned_data.get('city')
        
        # Validate city exists in province
        if province and city:
            valid_cities = {
                "Province 1": ["Biratnagar", "Dharan", "Itahari", "Damak", "Birtamod", "Mechinagar", "Urlabari"],
                "Province 2": ["Janakpur", "Birgunj", "Simara", "Kalaiya", "Malangwa", "Jaleshwar", "Rajbiraj"],
                "Bagmati": ["Kathmandu", "Lalitpur", "Bhaktapur", "Hetauda", "Bharatpur", "Bidur", "Dhulikhel"],
                "Gandaki": ["Pokhara", "Damauli", "Gorkha", "Waling", "Syangja", "Baglung", "Besisahar"],
                "Lumbini": ["Butwal", "Bhairahawa", "Nepalgunj", "Tulsipur", "Ghorahi", "Tansen", "Kapilvastu"],
                "Karnali": ["Birendranagar", "Jumla", "Dailekh", "Salyan", "Rukum", "Jajarkot", "Dolpa"],
                "Sudurpashchim": ["Dhangadhi", "Mahendranagar", "Tikapur", "Dadeldhura", "Dipayal", "Bajhang", "Bajura"]
            }
            
            if city not in valid_cities.get(province, []):
                self.add_error('city', f"'{city}' is not a valid city in {province}.")
        
        return cleaned_data
    class Meta:
        model = Order
        fields = [ 'customer_name', 'customer_email', 'customer_phone',
            'province', 'city', 'street_address', 'delivery_instructions',
            'quantity', 'payment_method']
        
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)  # Get the user from kwargs
        super(OrderForm, self).__init__(*args, **kwargs)    
    def clean_customer_email(self):
        email = self.cleaned_data.get('customer_email')
        
        # If user is authenticated and has an email, validate it matches
        if self.user and self.user.is_authenticated and self.user.email:
            if email != self.user.email:
                raise forms.ValidationError(
                    f"This email doesn't match your account email ({self.user.email}). "
                    "Please use your account email or log out to use a different email."
                )
        
        return email   


class CartOrderForm(forms.ModelForm):
    province = forms.ChoiceField(
        choices=[
            ('', 'Select Province'),
            ('Province 1', 'Province 1'),
            ('Province 2', 'Province 2'),
            ('Bagmati', 'Bagmati'),
            ('Gandaki', 'Gandaki'),
            ('Lumbini', 'Lumbini'),
            ('Karnali', 'Karnali'),
            ('Sudurpashchim', 'Sudurpashchim'),
        ],
        required=True,
        widget=forms.Select(attrs={'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring focus:ring-blue-500 focus:ring-opacity-50', 'id': 'province-select'})
    )
    city = forms.CharField(
        required=True,
        widget=forms.Select(attrs={'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring focus:ring-blue-500 focus:ring-opacity-50', 'id': 'city-select'})
    )
    street_address = forms.CharField(
        required=True, 
        widget=forms.Textarea(attrs={'rows': 2, 'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring focus:ring-blue-500 focus:ring-opacity-50'})
    )
    delivery_instructions = forms.CharField(
        required=False, 
        widget=forms.Textarea(attrs={'rows': 2, 'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring focus:ring-blue-500 focus:ring-opacity-50'})
    )
    payment_method = forms.ChoiceField(
        choices=[
            ('', 'Select Payment Method'),
            ('cash_on_delivery', 'Cash on Delivery'),
            ('credit_card', 'Credit/Debit Card'),
            ('mobile_payment', 'Mobile Payment'),
            ('bank_transfer', 'Bank Transfer'),
        ],
        required=True,
        widget=forms.Select(attrs={'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring focus:ring-blue-500 focus:ring-opacity-50'})
    )
    
    def clean(self):
        cleaned_data = super().clean()
        province = cleaned_data.get('province')
        city = cleaned_data.get('city')
        
        # Validate city exists in province
        if province and city:
            valid_cities = {
                "Province 1": ["Biratnagar", "Dharan", "Itahari", "Damak", "Birtamod", "Mechinagar", "Urlabari"],
                "Province 2": ["Janakpur", "Birgunj", "Simara", "Kalaiya", "Malangwa", "Jaleshwar", "Rajbiraj"],
                "Bagmati": ["Kathmandu", "Lalitpur", "Bhaktapur", "Hetauda", "Bharatpur", "Bidur", "Dhulikhel"],
                "Gandaki": ["Pokhara", "Damauli", "Gorkha", "Waling", "Syangja", "Baglung", "Besisahar"],
                "Lumbini": ["Butwal", "Bhairahawa", "Nepalgunj", "Tulsipur", "Ghorahi", "Tansen", "Kapilvastu"],
                "Karnali": ["Birendranagar", "Jumla", "Dailekh", "Salyan", "Rukum", "Jajarkot", "Dolpa"],
                "Sudurpashchim": ["Dhangadhi", "Mahendranagar", "Tikapur", "Dadeldhura", "Dipayal", "Bajhang", "Bajura"]
            }
            
            if city not in valid_cities.get(province, []):
                self.add_error('city', f"'{city}' is not a valid city in {province}.")
        
        return cleaned_data
    
    class Meta:
        model = Order
        fields = [
            'customer_name', 'customer_email', 'customer_phone',
            'province', 'city', 'street_address', 'delivery_instructions',
            'quantity', 'payment_method'
        ]
        widgets = {
            'customer_name': forms.TextInput(attrs={'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring focus:ring-blue-500 focus:ring-opacity-50'}),
            'customer_email': forms.EmailInput(attrs={'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring focus:ring-blue-500 focus:ring-opacity-50'}),
            'customer_phone': forms.TextInput(attrs={'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring focus:ring-blue-500 focus:ring-opacity-50'}),
            'quantity': forms.NumberInput(attrs={'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring focus:ring-blue-500 focus:ring-opacity-50', 'min': '1'}),
        }
        
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)  # Get the user from kwargs
        super(CartOrderForm, self).__init__(*args, **kwargs)
        
    def clean_customer_email(self):
        email = self.cleaned_data.get('customer_email')
        
        # If user is authenticated and has an email, validate it matches
        if self.user and self.user.is_authenticated and self.user.email:
            if email != self.user.email:
                raise forms.ValidationError(
                    f"This email doesn't match your account email ({self.user.email}). "
                    "Please use your account email or log out to use a different email."
                )
        
        return email     

class DealForm(forms.ModelForm):
    class Meta:
        model = Deal
        fields = [
            'title', 
            'description', 
            'image',
            # Wholesale-specific fields
            'min_order',
            'lead_time',
            'origin',
            'shipping_terms',
            'certifications',
            # Shipping destinations
            'ship_domestic',
            'ship_international',
            'ship_north_america',
            'ship_europe',
            'ship_asia',
            'ship_australia',
            'ship_africa',
            'ship_south_america',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
            'certifications': forms.Textarea(attrs={'rows': 3, 'placeholder': 'List any certifications, compliance standards, or quality assurances'}),
            'min_order': forms.NumberInput(attrs={'placeholder': 'Minimum quantity per order'}),
            'lead_time': forms.TextInput(attrs={'placeholder': 'e.g., 2-3 weeks'}),
            'origin': forms.TextInput(attrs={'placeholder': 'Country or region of manufacture'}),
            'shipping_terms': forms.TextInput(attrs={'placeholder': 'e.g., FOB, CIF, EXW'}),
        }
        labels = {
            'min_order': 'Minimum Order Quantity',
            'lead_time': 'Lead Time',
            'origin': 'Country/Region of Origin',
            'shipping_terms': 'Shipping Terms',
            'certifications': 'Certifications & Compliance',
            'ship_domestic': 'Domestic Shipping Available',
            'ship_international': 'International Shipping Available',
            'ship_north_america': 'Ships to North America',
            'ship_europe': 'Ships to Europe',
            'ship_asia': 'Ships to Asia',
            'ship_australia': 'Ships to Australia/Oceania',
            'ship_africa': 'Ships to Africa',
            'ship_south_america': 'Ships to South America',
        }
        help_texts = {
            'min_order': 'The minimum number of units that can be ordered',
            'lead_time': 'Estimated time from order to delivery',
            'shipping_terms': 'Standard international shipping terms (FOB, CIF, etc.)',
        }

class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ['name', 'email', 'phone', 'message']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 4}),
        }

class CoAdminRegistrationForm(forms.ModelForm):
    class Meta:
        model = CoAdmin
        fields = ['name', 'email', 'phone_number', 'address', 'date_of_birth', 
                 'photo', 'dob_certificate', 'nationality_card_front', 'nationality_card_back']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'block w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 sm:text-sm'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'block w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 sm:text-sm'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'block w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 sm:text-sm'
            }),
            'address': forms.Textarea(attrs={
                'class': 'block w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 sm:text-sm',
                'rows': 3
            }),
            'date_of_birth': forms.DateInput(attrs={
                'class': 'block w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 sm:text-sm',
                'type': 'date'
            }),
            'photo': forms.FileInput(attrs={
                'class': 'hidden'
            }),
            'dob_certificate': forms.FileInput(attrs={
                'class': 'hidden',
                'required': False
            }),
            'nationality_card_front': forms.FileInput(attrs={
                'class': 'hidden',
                'required': False
            }),
            'nationality_card_back': forms.FileInput(attrs={
                'class': 'hidden',
                'required': False
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make these fields optional in the form
        self.fields['dob_certificate'].required = False
        self.fields['nationality_card_front'].required = False
        self.fields['nationality_card_back'].required = False
        
        # Make email field read-only if it's pre-filled
        if 'initial' in kwargs and 'email' in kwargs['initial']:
            self.fields['email'].widget.attrs['readonly'] = True
            self.fields['email'].help_text = "Email is linked to your account and cannot be changed here."
    
    def clean(self):
        cleaned_data = super().clean()
        dob_certificate = cleaned_data.get('dob_certificate')
        nationality_front = cleaned_data.get('nationality_card_front')
        
        # Check if at least one of DOB certificate or nationality card is provided
        if not dob_certificate and not nationality_front:
            raise forms.ValidationError(
                "You must provide either a DOB certificate or nationality card (front)."
            )
        
        # If nationality front is provided, back should also be provided
        if nationality_front and not cleaned_data.get('nationality_card_back'):
            self.add_error('nationality_card_back', "If you provide the front of the nationality card, you must also provide the back.")
        
        return cleaned_data