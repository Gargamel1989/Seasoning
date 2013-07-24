from __future__ import absolute_import
from django.shortcuts import render, get_object_or_404, redirect
from .models import Question, Topic
from django.utils import simplejson
from django.http.response import HttpResponse
from django.core.exceptions import PermissionDenied
from django.forms.models import modelform_factory

def topic_list(request):
    topics = Topic.objects.all().prefetch_related()
    return render(request, 'faq/topic_list.html', {'topics': topics})

def topic_detail(request, topic_id):
    topic = get_object_or_404(Topic, pk=topic_id)
    questions = Question.objects.filter(topic=topic)
    return render(request, 'faq/topic_detail.html', {'topic': topic,
                                                     'questions': questions})

def question_detail(request, question_id):
    """
    Ajax view function for fetching question data
    
    """
    if request.is_ajax():
        question = get_object_or_404(Question, pk=id)
        question_json = simplejson.dumps(question)
        return HttpResponse(question_json, mimetype='application/javascript')
    raise PermissionDenied


"""
Administrative views
"""

def admin_list(request):
    if not request.user.is_superuser:
        raise PermissionDenied
    
    topics = Topic.objects.all().prefetch_related()
    return render(request, 'admin/faq_list.html', {'topics': topics})

def admin_edit_question(request, question_id=None):
    if not request.user.is_superuser:
        raise PermissionDenied
    
    if question_id:
        question = Question.objects.get(pk=question_id)
        new = False
    else:
        question = Question()
        new = True
    
    QuestionForm = modelform_factory(Question)
    
    if request.method == 'POST':
        question_form = QuestionForm(request.POST, instance=question)
        
        if question_form.is_valid():
            question_form.save()
            return redirect(admin_list)
    else:
        question_form = QuestionForm(instance=question)
    
    return render(request, 'admin/edit_question.html', {'new': new,
                                                        'question_form': question_form})
    return render(request, '')