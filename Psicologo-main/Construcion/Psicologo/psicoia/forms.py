from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError

from .models import Usuario, Sesion,Mensaje,RespuestaDASS

class RegistroForm(UserCreationForm):

    email = forms.EmailField(
        required=True,
        label="Correo electrónico",
        widget=forms.EmailInput(attrs={
            'placeholder': 'tu@correo.com',
            'class': 'field__input',
        }),
    )

    consentimiento_privacidad = forms.BooleanField(
        required=True,
        label="Acepto la política de privacidad y el manejo ético de mis datos",
        error_messages={
            'required': 'Debes aceptar la política de privacidad para continuar.'
        },
    )

    class Meta:
        model = Usuario
        fields = [
            'username',
            'email',
            'password1',
            'password2',
            'consentimiento_privacidad'
        ]

        labels = {
            'username': 'Nombre de usuario',
        }

        widgets = {
            'username': forms.TextInput(attrs={
                'placeholder': 'Tu nombre de usuario',
                'class': 'field__input',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['password1'].widget.attrs.update({
            'placeholder': 'Contraseña',
            'class': 'field__input',
        })

        self.fields['password2'].widget.attrs.update({
            'placeholder': 'Confirmar contraseña',
            'class': 'field__input',
        })


class LoginForm(AuthenticationForm):

    username = forms.CharField(
        label="Usuario",
        widget=forms.TextInput(attrs={
            'placeholder': 'Tu nombre de usuario',
            'class': 'form-input',
            'autofocus': True,
        }),
    )

    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Contraseña',
            'class': 'form-input',
        }),
    )



class MensajeForm(forms.Form):
    contenido = forms.CharField(
        label="",
        max_length=500,
        widget=forms.TextInput(attrs={
            'placeholder': 'Comparte cómo te sientes...',
            'class': 'chat-input',
            'autocomplete': 'off',
        }),
        error_messages={
            'required':  'Escribe un mensaje antes de enviar.',
            'max_length': 'El mensaje no puede superar los 500 caracteres.',
        },
    )

    def clean_contenido(self):
        contenido = self.cleaned_data.get('contenido', '').strip()
        if not contenido:
            raise ValidationError('El mensaje no puede estar vacío.')
        return contenido



class RespuestaDASS21Form(forms.ModelForm):

    RESPUESTA_CHOICES = [
        (0, '0 – No me aplicó nada'),
        (1, '1 – Me aplicó un poco, o durante parte del tiempo'),
        (2, '2 – Me aplicó bastante, o durante una buena parte del tiempo'),
        (3, '3 – Me aplicó mucho, o la mayor parte del tiempo'),
    ]

    respuesta = forms.TypedChoiceField(
        choices=RESPUESTA_CHOICES,
        coerce=int,
        label="Tu respuesta",
        widget=forms.RadioSelect(attrs={'class': 'dass-radio'}),
        error_messages={'required': 'Selecciona una opción para continuar.'},
    )

    class Meta:
        model  = RespuestaDASS
        fields = ['respuesta']

    def save(self, sesion, numero_item, subescala, mensaje=None, commit=True):
        instancia = super().save(commit=False)
        instancia.sesion      = sesion
        instancia.numero_item = numero_item
        instancia.subescala   = subescala
        instancia.mensaje     = mensaje
        if commit:
            instancia.save()
        return instancia



class FinalizarSesionForm(forms.ModelForm):

    class Meta:
        model  = Sesion
        fields = ['estado']
        widgets = {
            'estado': forms.HiddenInput(),  # la view fija el valor 'completada'
        }



class EliminarCuentaForm(forms.Form):

    password = forms.CharField(
        label="Confirma tu contraseña para eliminar la cuenta",
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Tu contraseña actual',
            'class': 'form-input form-input--danger',
        }),
    )
    confirmar = forms.BooleanField(
        required=True,
        label="Entiendo que esta acción es irreversible y se eliminarán todos mis datos",
        error_messages={
            'required': 'Debes marcar esta casilla para confirmar.'
        },
    )

    def __init__(self, usuario, *args, **kwargs):
        self.usuario = usuario
        super().__init__(*args, **kwargs)

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if not self.usuario.check_password(password):
            raise ValidationError('La contraseña es incorrecta.')
        return password