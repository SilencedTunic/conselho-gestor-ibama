from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path("", views.nova_pauta, name="nova_pauta"),
    path("acompanhar/", views.acompanhar, name="acompanhar"),
    path(
        "gestao/entrar/",
        auth_views.LoginView.as_view(template_name="pauta/gestao_login.html"),
        name="gestao_login",
    ),
    path("gestao/sair/", auth_views.LogoutView.as_view(), name="gestao_logout"),
    path("gestao/", views.gestao_painel, name="gestao_painel"),
    path("gestao/pauta/<int:pk>/editar/", views.gestao_item_editar, name="gestao_item_editar"),
    path("gestao/pauta-final/<int:reuniao_id>/", views.gestao_pauta_final, name="gestao_pauta_final"),
]
