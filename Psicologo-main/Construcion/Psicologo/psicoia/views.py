import json

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import (
    authenticate,
    login as auth_login,
    logout as auth_logout,
)
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import ensure_csrf_cookie

from .forms import RegistroForm, LoginForm, MensajeForm
from .models import Sesion, Mensaje, AnalisisFacial, Diagnostico, Recomendacion, RespuestaDASS
from .service import chat, facial
from .service import dass as dass_service


# ── REGISTRO ──────────────────────────────────────────────────────────
def registro(request):
    if request.user.is_authenticated:
        return redirect('psicoia:chat')
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            auth_login(request, usuario)
            messages.success(request, f'¡Bienvenido/a, {usuario.username}!')
            return redirect('psicoia:chat')
        messages.error(request, 'Por favor corrige los errores del formulario.')
    else:
        form = RegistroForm()
    return render(request, 'account/registro.html', {'form': form})


# ── LOGIN ─────────────────────────────────────────────────────────────
def login(request):
    if request.user.is_authenticated:
        return redirect('psicoia:chat')
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            auth_login(request, form.get_user())
            return redirect(request.GET.get('next') or 'psicoia:chat')
        messages.error(request, 'Usuario o contraseña incorrectos.')
    else:
        form = LoginForm(request)
    return render(request, 'account/login.html', {'form': form})


# ── LOGOUT ────────────────────────────────────────────────────────────
@login_required
def logout(request):
    if request.method == 'POST':
        auth_logout(request)
        messages.info(request, 'Cerraste sesión correctamente.')
        return redirect('psicoia:login')
    return redirect('psicoia:chat')


# ── HOME ──────────────────────────────────────────────────────────────
def home(request):
    return render(request, 'index/base.html')


# ── CHAT ──────────────────────────────────────────────────────────────
@ensure_csrf_cookie
@login_required
def chat_view(request):
    sesion, creada = Sesion.objects.get_or_create(
        usuario=request.user,
        estado='activa',
        defaults={'estado': 'activa'},
    )
    if creada:
        Mensaje.objects.create(
            sesion=sesion,
            rol='assistant',
            contenido=(
                "¡Hola! Soy Empathy AI, tu compañero de apoyo emocional. "
                "Estoy aquí para escucharte con atención y sin juzgarte. "
                "¿Cómo te has sentido últimamente?"
            ),
        )

    mensajes = sesion.mensajes.all().order_by('timestamp')
    form     = MensajeForm()

    # Diagnóstico previo si existe
    diagnostico = getattr(sesion, 'diagnostico', None)

    return render(request, 'views/chat.html', {
        'sesion':      sesion,
        'mensajes':    mensajes,
        'form':        form,
        'diagnostico': diagnostico,
    })


# ── PROCESAR MENSAJE (AJAX) ───────────────────────────────────────────
RECURSOS_CRISIS = {
    'mensaje': 'Si estás en peligro inmediato, contacta ayuda de inmediato.',
    'lineas': [
        {'pais': 'Ecuador',       'telefono': '171 (opción salud mental)'},
        {'pais': 'Internacional', 'telefono': 'Línea local de prevención del suicidio'},
    ],
}


@login_required
@require_POST
def procesar_mensaje(request):
    sesion = get_object_or_404(Sesion, usuario=request.user, estado='activa')

    form = MensajeForm(request.POST)
    if not form.is_valid():
        return JsonResponse({'error': form.errors}, status=400)

    contenido_usuario = form.cleaned_data['contenido']

    # ── Detectar si quiere nueva sesión ──────────────────────────────
    if chat.quiere_nueva_sesion(contenido_usuario):
        Mensaje.objects.create(sesion=sesion, rol='user', contenido=contenido_usuario)
        msg_bot = Mensaje.objects.create(
            sesion=sesion, rol='assistant',
            contenido='Claro, puedo cerrar esta sesión. ¿Confirmas que quieres iniciar una nueva conversación desde cero?',
        )
        return JsonResponse({
            'respuesta': msg_bot.contenido,
            'emocion_detectada': 'neutral',
            'protocolo_crisis': False,
            'recursos_ayuda': None,
            'solicitar_nueva_sesion': True,
        })
    historial_previo  = list(sesion.mensajes.all().order_by('timestamp'))

    mensaje_usuario = Mensaje.objects.create(
        sesion=sesion, rol='user', contenido=contenido_usuario,
    )

    # Pasar sesion para que chat.py pueda leer/escribir estado_dass
    resultado = chat.generar_respuesta(historial_previo, contenido_usuario, sesion=sesion)

    mensaje_usuario.emocion_nlp = resultado['emocion_detectada']
    mensaje_usuario.save(update_fields=['emocion_nlp'])

    if resultado.get('riesgo_critico'):
        sesion.protocolo_crisis_activo = True
        sesion.save(update_fields=['protocolo_crisis_activo'])

    mensaje_bot = Mensaje.objects.create(
        sesion=sesion,
        rol='assistant',
        contenido=resultado['respuesta'],
        tokens_mensaje=resultado.get('tokens', 0),
    )

    sesion.tokens_usados += resultado.get('tokens', 0)
    sesion.save(update_fields=['tokens_usados'])

    # ── Si el DASS terminó → guardar diagnóstico en BD ───────────────
    diagnostico_data = None
    if resultado.get('diagnostico_calculado') and resultado.get('resultado_dass'):
        rd = resultado['resultado_dass']
        diag, _ = Diagnostico.objects.update_or_create(
            sesion=sesion,
            defaults={
                'puntuacion_D':     rd['puntuacion_D'],
                'puntuacion_A':     rd['puntuacion_A'],
                'puntuacion_S':     rd['puntuacion_S'],
                'nivel_D':          rd['nivel_D'],
                'nivel_A':          rd['nivel_A'],
                'nivel_S':          rd['nivel_S'],
                'nivel_global':     rd['nivel_global'],
                'confianza_global': rd['confianza_global'],
            }
        )
        # Guardar recomendaciones
        diag.recomendaciones.all().delete()
        for rec in rd['recomendaciones']:
            Recomendacion.objects.create(
                diagnostico=diag,
                tipo=rec['tipo'],
                descripcion=rec['descripcion'],
                derivar_profesional=rec['derivar'],
            )
        # Guardar respuestas DASS individuales
        estado_dass = sesion.estado_dass or {}
        for num_str, valor in estado_dass.get('respuestas', {}).items():
            num = int(num_str)
            item = dass_service.ITEMS_DASS[num - 1]
            RespuestaDASS.objects.update_or_create(
                sesion=sesion, numero_item=num,
                defaults={'respuesta': valor, 'subescala': item['sub']},
            )

        diagnostico_data = {
            'nivel_global': rd['nivel_global'],
            'nivel_D': rd['nivel_D'],
            'nivel_A': rd['nivel_A'],
            'nivel_S': rd['nivel_S'],
            'puntuacion_D': rd['puntuacion_D'],
            'puntuacion_A': rd['puntuacion_A'],
            'puntuacion_S': rd['puntuacion_S'],
            'recomendaciones': rd['recomendaciones'],
            'derivar_profesional': rd['derivar_profesional'],
        }

    estado_dass_actual = sesion.estado_dass or {}

    return JsonResponse({
        'respuesta':             mensaje_bot.contenido,
        'emocion_detectada':     resultado['emocion_detectada'],
        'protocolo_crisis':      resultado.get('riesgo_critico', False),
        'recursos_ayuda':        RECURSOS_CRISIS if resultado.get('riesgo_critico') else None,
        'item_dass':             resultado.get('item_dass'),
        'total_dass':            resultado.get('total_dass'),
        'diagnostico_calculado': resultado.get('diagnostico_calculado', False),
        'diagnostico':           diagnostico_data,
    })


# ── ANÁLISIS FACIAL (AJAX) ────────────────────────────────────────────
@login_required
@require_POST
def analizar_facial(request):
    try:
        data         = json.loads(request.body)
        frame_base64 = data.get('frame')
        mensaje_id   = data.get('mensaje_id')
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({'error': 'Payload inválido'}, status=400)

    if not frame_base64:
        return JsonResponse({'error': 'No se recibió ningún frame'}, status=400)

    sesion    = get_object_or_404(Sesion, usuario=request.user, estado='activa')
    resultado = facial.analizar_emocion_facial(frame_base64)

    mensaje_obj = None
    if mensaje_id:
        mensaje_obj = Mensaje.objects.filter(id=mensaje_id, sesion=sesion).first()

    AnalisisFacial.objects.create(
        sesion=sesion,
        mensaje=mensaje_obj,
        emocion_predominante=resultado['emocion'],
        confianza=resultado['confianza'],
    )

    return JsonResponse({
        'emocion':          resultado['emocion'],
        'confianza':        resultado['confianza'],
        'rostro_detectado': resultado['rostro_detectado'],
    })


# ── DIAGNÓSTICO (página de resultados) ───────────────────────────────
@login_required
def ver_diagnostico(request):
    sesion = Sesion.objects.filter(usuario=request.user).order_by('-fecha_inicio').first()
    if not sesion:
        return redirect('psicoia:chat')
    diagnostico = getattr(sesion, 'diagnostico', None)
    return render(request, 'views/diagnostico.html', {
        'sesion':      sesion,
        'diagnostico': diagnostico,
    })


# ── FINALIZAR SESIÓN ──────────────────────────────────────────────────
@login_required
@require_POST
def finalizar_sesion(request):
    sesion = get_object_or_404(Sesion, usuario=request.user, estado='activa')
    sesion.estado = 'completada'
    sesion.save(update_fields=['estado'])
    return redirect('psicoia:chat')


# ── NUEVA SESIÓN (AJAX) ───────────────────────────────────────────────
@login_required
@require_POST
def nueva_sesion(request):
    """
    Cierra la sesión activa y devuelve confirmación JSON.
    El JS redirige al chat donde se crea una sesión nueva automáticamente.
    """
    Sesion.objects.filter(usuario=request.user, estado='activa').update(estado='completada')
    return JsonResponse({'ok': True})


# ── HISTORIAL DE SESIONES ─────────────────────────────────────────────
@login_required
def historial(request):
    sesiones = Sesion.objects.filter(
        usuario=request.user
    ).exclude(estado='activa').order_by('-fecha_inicio')
    return render(request, 'views/historial.html', {'sesiones': sesiones})


# ── DETALLE DE SESIÓN ─────────────────────────────────────────────────
@login_required
def detalle_sesion(request, sesion_id):
    sesion = get_object_or_404(Sesion, id=sesion_id, usuario=request.user)
    mensajes    = sesion.mensajes.all().order_by('timestamp')
    diagnostico = getattr(sesion, 'diagnostico', None)
    return render(request, 'views/detalle_sesion.html', {
        'sesion':      sesion,
        'mensajes':    mensajes,
        'diagnostico': diagnostico,
    })

