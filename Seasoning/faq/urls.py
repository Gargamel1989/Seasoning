from django.conf.urls import patterns, url
from faq.views import topic_list, topic_detail, question_detail,\
    admin_list, admin_edit_question

urlpatterns = patterns('',
    url(regex = r'^$',
        view = topic_list,
        name = 'faq_topic_list',
    ),
    url(regex = r'^(\d*)/$',
        view = topic_detail,
        name = 'faq_topic_detail',
    ),
    url(regex = r'^question/(\d*)/$',
        view = question_detail,
        name = 'faq_question_detail',
    ),
    url(r'^admin/$', admin_list),
    url(r'^admin/edit/$', admin_edit_question),
    url(r'^admin/edit/(\d*)/$', admin_edit_question),
)