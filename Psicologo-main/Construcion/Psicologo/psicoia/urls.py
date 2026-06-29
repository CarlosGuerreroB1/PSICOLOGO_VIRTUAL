
from django.urls import path
from . import views

app_name = 'psicoia'

urlpatterns = [
    path('',                        views.home,             name='index'),
    path('login/',                  views.login,            name='login'),
    path('registro/',               views.registro,         name='registro'),
    path('logout/',                 views.logout,           name='logout'),
    path('chat/',                   views.chat_view,        name='chat'),
    path('mensaje/',                views.procesar_mensaje, name='procesar_mensaje'),
    path('facial/',                 views.analizar_facial,  name='analizar_facial'),
    path('finalizar/',              views.finalizar_sesion, name='finalizar_sesion'),
    path('nueva-sesion/',           views.nueva_sesion,     name='nueva_sesion'),
    path('diagnostico/',            views.ver_diagnostico,  name='diagnostico'),
    path('historial/',              views.historial,        name='historial'),
    path('historial/<int:sesion_id>/', views.detalle_sesion, name='detalle_sesion'),
]