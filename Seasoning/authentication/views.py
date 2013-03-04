from django.template.response import TemplateResponse
from authentication.forms import ResendActivationEmailForm,\
    EmailAuthenticationForm, EmailUserCreationForm
from django.contrib.sites.models import RequestSite
from django.contrib.auth.views import login as auth_login
from registration.views import register as auth_register
from django.http import HttpResponse

def resend_activation_email(request):
    
    errormessage = None
    
    if request.method == "POST":
        
        form = ResendActivationEmailForm(data=request.POST)
        
        if form.is_valid():            
            site = RequestSite(request)
                    
            form.cleaned_data['email'].send_activation_email(site)
                    
            context = {'done': True}
            
            return TemplateResponse(request, 'registration/resend_activation_email.html', context)
        
    else:
        form = ResendActivationEmailForm()
        
    context = {
        'done': False,
        'form': form,
        'error': errormessage
    }
        
    return TemplateResponse(request, 'registration/resend_activation_email.html', context)

def login(request):    
    if request.is_ajax():
        pass
    else:
        return auth_login(request, authentication_form=EmailAuthenticationForm)
    
def register(request):
    if request.is_ajax():
        if request.method == 'POST':
            form = EmailAuthenticationForm(data=request.POST)
            form.is_valid()
            
            if request.POST['field'] == 'username':
                #print form.username.errors
                return HttpResponse(None,'application/javascript')
    else:
        return auth_register(request, 'Seasoning.registration.backends.UserProfileRegistrationBackend', form_class=EmailUserCreationForm)