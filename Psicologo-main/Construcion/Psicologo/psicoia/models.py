from django.contrib.auth.models import AbstractUser
from django.db import models


class Usuario(AbstractUser):
    class Meta:
        verbose_name        = "Usuario"
        verbose_name_plural = "Usuarios"


class Sesion(models.Model):
    ESTADO_CHOICES = [
        ('activa',     'Activa'),
        ('completada', 'Completada'),
        ('cancelada',  'Cancelada'),
    ]

    usuario      = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='sesiones')
    fecha_inicio = models.DateTimeField(auto_now_add=True)
    fecha_fin    = models.DateTimeField(null=True, blank=True)
    estado       = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='activa')
    tokens_usados           = models.PositiveIntegerField(default=0)
    protocolo_crisis_activo = models.BooleanField(default=False)


    estado_dass = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"Sesion #{self.pk} – {self.usuario.username} ({self.estado})"

    class Meta:
        verbose_name        = "Sesión"
        verbose_name_plural = "Sesiones"
        ordering            = ['-fecha_inicio']


class Mensaje(models.Model):
    ROL_CHOICES = [
        ('user',      'Usuario'),
        ('assistant', 'Asistente'),
        ('system',    'Sistema'),
    ]
    EMOCION_CHOICES = [
        ('neutral',  'Neutral'),
        ('tristeza', 'Tristeza'),
        ('ansiedad', 'Ansiedad'),
        ('alegria',  'Alegría'),
        ('miedo',    'Miedo'),
        ('enojo',    'Enojo'),
        ('sorpresa', 'Sorpresa'),
        ('apatia',   'Apatía'),
    ]

    sesion         = models.ForeignKey(Sesion, on_delete=models.CASCADE, related_name='mensajes')
    rol            = models.CharField(max_length=10, choices=ROL_CHOICES)
    contenido      = models.TextField()
    timestamp      = models.DateTimeField(auto_now_add=True)
    emocion_nlp    = models.CharField(max_length=20, choices=EMOCION_CHOICES, default='neutral')
    tokens_mensaje = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"[{self.rol}] {self.contenido[:60]}"

    class Meta:
        verbose_name        = "Mensaje"
        verbose_name_plural = "Mensajes"
        ordering            = ['timestamp']


class AnalisisFacial(models.Model):
    EMOCION_CHOICES = [
        ('neutral',  'Neutral'), ('tristeza', 'Tristeza'), ('ansiedad', 'Ansiedad'),
        ('alegria',  'Alegría'), ('miedo',    'Miedo'),    ('enojo',    'Enojo'),
        ('sorpresa', 'Sorpresa'), ('apatia',  'Apatía'),
    ]
    mensaje              = models.OneToOneField(Mensaje, on_delete=models.CASCADE, related_name='analisis_facial', null=True, blank=True)
    sesion               = models.ForeignKey(Sesion, on_delete=models.CASCADE, related_name='analisis_faciales')
    timestamp            = models.DateTimeField(auto_now_add=True)
    emocion_predominante = models.CharField(max_length=20, choices=EMOCION_CHOICES, default='neutral')
    confianza            = models.FloatField(default=0.0)

    def __str__(self):
        return f"Facial msg#{self.mensaje_id} – {self.emocion_predominante} ({self.confianza:.0%})"

    class Meta:
        verbose_name        = "Análisis Facial"
        verbose_name_plural = "Análisis Faciales"
        ordering            = ['timestamp']


class RespuestaDASS(models.Model):
    SUBESCALA_CHOICES = [('D', 'Depresión'), ('A', 'Ansiedad'), ('S', 'Estrés')]
    sesion      = models.ForeignKey(Sesion, on_delete=models.CASCADE, related_name='respuestas_dass')
    mensaje     = models.OneToOneField(Mensaje, on_delete=models.SET_NULL, null=True, blank=True, related_name='respuesta_dass')
    numero_item = models.PositiveSmallIntegerField()
    respuesta   = models.PositiveSmallIntegerField()
    subescala   = models.CharField(max_length=1, choices=SUBESCALA_CHOICES)

    def __str__(self):
        return f"DASS ítem {self.numero_item} ({self.subescala}) = {self.respuesta}"

    class Meta:
        verbose_name        = "Respuesta DASS-21"
        verbose_name_plural = "Respuestas DASS-21"
        unique_together     = ('sesion', 'numero_item')


class Diagnostico(models.Model):
    NIVEL_CHOICES = [
        ('normal', 'Normal'), ('leve', 'Leve'), ('moderado', 'Moderado'),
        ('severo', 'Severo'), ('muy_severo', 'Muy severo'),
    ]
    sesion           = models.OneToOneField(Sesion, on_delete=models.CASCADE, related_name='diagnostico')
    puntuacion_D     = models.PositiveSmallIntegerField(default=0)
    puntuacion_A     = models.PositiveSmallIntegerField(default=0)
    puntuacion_S     = models.PositiveSmallIntegerField(default=0)
    nivel_D          = models.CharField(max_length=20, choices=NIVEL_CHOICES, default='normal')
    nivel_A          = models.CharField(max_length=20, choices=NIVEL_CHOICES, default='normal')
    nivel_S          = models.CharField(max_length=20, choices=NIVEL_CHOICES, default='normal')
    nivel_global     = models.CharField(max_length=20, choices=NIVEL_CHOICES, default='normal')
    confianza_global = models.FloatField(default=0.0)
    fecha            = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Diagnóstico sesión #{self.sesion.pk} – {self.nivel_global}"

    class Meta:
        verbose_name        = "Diagnóstico"
        verbose_name_plural = "Diagnósticos"


class Recomendacion(models.Model):
    TIPO_CHOICES = [
        ('respiracion', 'Ejercicio de respiración'), ('mindfulness', 'Mindfulness'),
        ('actividad', 'Actividad física'), ('escritura', 'Escritura / diario'),
        ('social', 'Contacto social'), ('profesional', 'Derivación a profesional'),
        ('psicoeducacion', 'Psicoeducación'), ('otro', 'Otro'),
    ]
    diagnostico         = models.ForeignKey(Diagnostico, on_delete=models.CASCADE, related_name='recomendaciones')
    tipo                = models.CharField(max_length=20, choices=TIPO_CHOICES)
    descripcion         = models.TextField()
    derivar_profesional = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.get_tipo_display()} – {'⚠ derivar' if self.derivar_profesional else 'apoyo'}"

    class Meta:
        verbose_name        = "Recomendación"
        verbose_name_plural = "Recomendaciones"