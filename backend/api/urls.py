from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token

from .views import (
    ask,
    evaluation_run_detail,
    evaluation_runs,
    run_evaluation,
    health_check,
    overview,
    queries,
    search,
)

urlpatterns = [
    path('health/', health_check, name='health-check'),
    path('login/', obtain_auth_token, name='api-login'),
    path('overview/', overview, name='overview'),
    path('search/', search, name='search'),
    path('ask/', ask, name='ask'),
    path('queries/', queries, name='queries'),
    path('evaluation-runs/', evaluation_runs, name='evaluation-runs'),
    path('evaluation-runs/run/', run_evaluation, name='run-evaluation'),
    path('evaluation-runs/<int:run_id>/', evaluation_run_detail, name='evaluation-run-detail'),
]
