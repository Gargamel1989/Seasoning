from __future__ import absolute_import
from django.shortcuts import render, get_object_or_404
from .models import Question, Topic
from django.utils import simplejson
from django.http.response import HttpResponse
from django.core.exceptions import PermissionDenied

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