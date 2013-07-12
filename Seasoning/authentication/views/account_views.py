from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from authentication.forms import AccountSettingsForm, DeleteAccountForm,\
    CheckActiveAuthenticationForm
from authentication.models import NewEmail, User
from django.contrib import messages
from django.contrib.sites.models import RequestSite
from django.shortcuts import render, redirect, get_object_or_404
from django.http.response import Http404
from django.views.decorators.debug import sensitive_post_parameters
from django.contrib.auth.forms import PasswordChangeForm
from django.template.response import TemplateResponse
from django.contrib.auth.views import login as django_login, logout
from django.utils.translation import ugettext_lazy as _

@login_required
def public_profile(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    recipes = user.recipes.all()
    
    return render(request, 'authentication/public_profile.html', {'user': user,
                                                                  'recipes': recipes})

@login_required
def account_settings(request):
    """
    Allow a user to change his account settings
    
    If the user has changed his email address, an activation email will be sent to this new
    address. The new address will not be activated until the link in this email has been
    clicked.
    
    If the user has an alternate email that should be activated, this will also be displayed
    on this page.
    
    """
    context = {}
    if request.method == "POST":
        user = get_user_model().objects.get(id=request.user.id)
        form = AccountSettingsForm(request.POST, request.FILES, instance=user)
        
        if form.is_valid():
            if form.new_email:
                # Send an activation email to the new email
                NewEmail.objects.create_inactive_email(user, form.new_email, RequestSite(request))
                messages.add_message(request, messages.INFO, _('An email has been sent to the new email address provided by you. Please follow the instructions '
                                                               'in this email to complete the changing of your email address.'))
            # New email address has been replaced by old email address in the form, so it will not be saved until activated
            form.save()
    else:
        form = AccountSettingsForm(instance=request.user)
    
    try:
        new_email = NewEmail.objects.get(user=request.user)
        context['new_email'] = new_email.email
    except NewEmail.DoesNotExist:
        pass
    
    context['form'] = form
    return render(request, 'authentication/account_settings.html', context)

@login_required
def change_email(request, activation_key):
    """
    This checks if the given activation key belongs to the current users new,
    inactive email address. If so, this new email address is activated, and
    the users old email address is deleted.
    
    """
    activated = NewEmail.objects.activate_email(request.user, activation_key)
    if activated:
        messages.add_message(request, messages.INFO, _('Your email address has been successfully changed.'))
        return redirect(account_settings)
    raise Http404

@sensitive_post_parameters()
@login_required
def change_password(request,
                    template_name='authentication/password_change_form.html',
                    password_change_form=PasswordChangeForm,
                    current_app=None, extra_context=None):
    """
    Provides a form where the users password can be changed.
    
    """
    if request.method == "POST":
        form = password_change_form(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            messages.add_message(request, messages.INFO, _('Your password has been successfully changed.'))
            return redirect(account_settings)
    
    form = password_change_form(user=request.user)
    context = {
        'form': form,
    }
    if extra_context is not None:
        context.update(extra_context)
    return TemplateResponse(request, template_name, context,
                            current_app=current_app)

@login_required
def account_delete(request):
    """
    Provides a method for deleting the users account
    
    """
    # TODO: test
    if request.method == 'POST':
        form = DeleteAccountForm(request.POST)
        if form.is_valid():
            user = User.objects.get(pk=request.user.id)
            logout(request)
            user.delete()
            return redirect('/')
    else:
        form = DeleteAccountForm()
    return render(request, 'authentication/account_delete.html', {'form': form})

def login(request):
    redirect_to = request.REQUEST.get('next', None)
    
    if redirect_to:
        next_string = '&next=' + redirect_to
    else:
        next_string = ''
    return django_login(request, template_name='authentication/login.html', 
                        authentication_form=CheckActiveAuthenticationForm,
                        extra_context={'next_string': next_string})
    
def list_users(request):
    users = User.objects.all()
    return render(request, 'admin/user_list.html', {'users': users})
