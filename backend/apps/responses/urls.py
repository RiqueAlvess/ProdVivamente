from django.urls import path
from . import views

urlpatterns = [
    path('', views.ResponseListView.as_view(), name='response-list'),
    path('survey/<uuid:token>/status/', views.SurveyStatusView.as_view(), name='survey-status'),
    path('survey/<uuid:token>/lgpd/', views.SurveyLGPDView.as_view(), name='survey-lgpd'),
    path('survey/<uuid:token>/demographics/', views.SurveyDemographicsView.as_view(), name='survey-demographics'),
    path('survey/<uuid:token>/answer/', views.SurveyAnswerView.as_view(), name='survey-answer'),
    path('survey/<uuid:token>/submit/', views.SurveySubmitView.as_view(), name='survey-submit'),
]
