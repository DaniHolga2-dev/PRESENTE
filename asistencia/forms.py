from django import forms
from django.contrib.auth.hashers import make_password

from .models import Alumno


class RegistroAlumnoForm(forms.ModelForm):

    password = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Contraseña'
            }
        )
    )

    password_confirmacion = forms.CharField(
        label='Repetir contraseña',
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Repite la contraseña'
            }
        )
    )


    class Meta:

        model = Alumno

        fields = [
            'nombre',
            'apellidos',
            'carrera',
            'curso',
            'grupo',
            'email',
            'foto',
        ]

        widgets = {

            'nombre': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Nombre'
                }
            ),

            'apellidos': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Apellidos'
                }
            ),

            'carrera': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Carrera'
                }
            ),

            'curso': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Curso'
                }
            ),

            'grupo': forms.Select(
                attrs={
                    'class': 'form-select'
                }
            ),

            'email': forms.EmailInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'correo@universidad.es'
                }
            ),

            'foto': forms.FileInput(
                attrs={
                    'class': 'form-control'
                }
            ),
        }


    def clean(self):

        cleaned_data = super().clean()

        password = cleaned_data.get(
            'password'
        )

        password_confirmacion = cleaned_data.get(
            'password_confirmacion'
        )

        if password and password_confirmacion:

            if password != password_confirmacion:

                raise forms.ValidationError(
                    'Las contraseñas no coinciden.'
                )

        return cleaned_data


    def save(self, commit=True):

        alumno = super().save(
            commit=False
        )

        alumno.password = make_password(
            self.cleaned_data['password']
        )

        if commit:
            alumno.save()

        return alumno