from datetime import time, timedelta

from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from asistencia.models import (
    Profesor,
    Grupo,
    Alumno,
    Clase,
    Asistencia,
    Justificacion,
)


class Command(BaseCommand):

    help = (
        'Crea los usuarios y datos necesarios '
        'para probar PRESENTE.'
    )


    @transaction.atomic
    def handle(self, *args, **options):

        self.stdout.write(
            'Preparando datos de demostración...'
        )


        # =====================================================
        # PROFESOR
        # =====================================================

        usuario_profesor, creado = (
            User.objects.get_or_create(
                username='admin'
            )
        )

        usuario_profesor.email = (
            'admin@presente.com'
        )

        usuario_profesor.first_name = (
            'Profesor'
        )

        usuario_profesor.last_name = (
            'Demo'
        )

        usuario_profesor.is_staff = True

        usuario_profesor.set_password(
            '123456bL'
        )

        usuario_profesor.save()


        profesor, creado = (
            Profesor.objects.update_or_create(
                email='admin@presente.com',
                defaults={
                    'nombre': 'Profesor',
                    'apellidos': 'Demo',
                }
            )
        )


        # =====================================================
        # GRUPO
        # =====================================================

        grupo, creado = (
            Grupo.objects.update_or_create(
                profesor=profesor,
                nombre='Desarrollo de Aplicaciones Web',
                defaults={
                    'asignatura':
                        'Desarrollo de Aplicaciones Web',
                }
            )
        )


        # =====================================================
        # ALUMNOS
        # =====================================================

        datos_alumnos = [

            {
                'nombre': 'Daniel',
                'apellidos':
                    'Holgado González',
                'email':
                    'danielholgadogonzalez@hotmail.com',
            },

            {
                'nombre': 'Indira',
                'apellidos':
                    'Huertas Lucendo',
                'email':
                    'indirahuertaslucendo@hotmail.com',
            },

            {
                'nombre': 'Sergio',
                'apellidos':
                    'Cuéllar Almagro',
                'email':
                    'sergiocuellaralmagro@hotmail.com',
            },

            {
                'nombre': 'Diego',
                'apellidos':
                    'Del Toro Mota',
                'email':
                    'diegodeltoromota@hotmail.com',
            },

        ]


        alumnos = {}


        for datos in datos_alumnos:

            alumno, creado = (
                Alumno.objects.update_or_create(
                    email=datos['email'],
                    defaults={
                        'nombre':
                            datos['nombre'],

                        'apellidos':
                            datos['apellidos'],

                        'carrera':
                            'Desarrollo de Aplicaciones Web',

                        'curso':
                            '2º',

                        'password':
                            make_password(
                                '123456789'
                            ),

                        'grupo':
                            grupo,
                    }
                )
            )

            alumnos[
                datos['nombre']
            ] = alumno


        # =====================================================
        # CLASES
        # =====================================================

        hoy = timezone.localdate()

        fechas_clases = [

            hoy - timedelta(days=14),
            hoy - timedelta(days=12),
            hoy - timedelta(days=10),
            hoy - timedelta(days=7),
            hoy - timedelta(days=5),
            hoy - timedelta(days=2),

        ]


        clases = []


        for fecha in fechas_clases:

            clase, creada = (
                Clase.objects.get_or_create(
                    grupo=grupo,
                    fecha=fecha,
                    hora_inicio=time(
                        hour=9,
                        minute=0
                    ),
                    defaults={
                        'asistencia_abierta':
                            False,
                    }
                )
            )

            clases.append(
                clase
            )


        # =====================================================
        # ASISTENCIAS
        # =====================================================

        patrones = {

            'Daniel': [
                'presente',
                'presente',
                'tarde',
                'presente',
                'ausente',
                'presente',
            ],

            'Indira': [
                'presente',
                'presente',
                'presente',
                'presente',
                'presente',
                'tarde',
            ],

            'Sergio': [
                'presente',
                'tarde',
                'ausente',
                'presente',
                'presente',
                'presente',
            ],

            'Diego': [
                'ausente',
                'presente',
                'tarde',
                'presente',
                'ausente',
                'presente',
            ],

        }


        for nombre, estados in patrones.items():

            alumno = alumnos[nombre]

            for clase, estado in zip(
                clases,
                estados
            ):

                if estado == 'presente':

                    hora_registro = time(
                        hour=9,
                        minute=3
                    )

                elif estado == 'tarde':

                    hora_registro = time(
                        hour=9,
                        minute=15
                    )

                else:

                    hora_registro = None


                Asistencia.objects.update_or_create(
                    alumno=alumno,
                    clase=clase,
                    defaults={
                        'estado':
                            estado,

                        'hora_registro':
                            hora_registro,
                    }
                )


        # =====================================================
        # JUSTIFICACIÓN DE EJEMPLO
        # =====================================================

        ausencia_daniel = (
            Asistencia.objects.filter(
                alumno=alumnos['Daniel'],
                estado='ausente'
            )
            .order_by('clase__fecha')
            .first()
        )


        if ausencia_daniel:

            Justificacion.objects.update_or_create(
                asistencia=ausencia_daniel,
                defaults={
                    'motivo':
                        (
                            'Ausencia de prueba '
                            'para comprobar el sistema '
                            'de justificaciones.'
                        ),

                    'estado':
                        'pendiente',
                }
            )


        # =====================================================
        # RESULTADO
        # =====================================================

        self.stdout.write('')

        self.stdout.write(
            self.style.SUCCESS(
                'Datos de demostración creados correctamente.'
            )
        )

        self.stdout.write('')

        self.stdout.write(
            '----------------------------------------'
        )

        self.stdout.write(
            'PROFESOR'
        )

        self.stdout.write(
            'Usuario: admin'
        )

        self.stdout.write(
            'Correo: admin@presente.com'
        )

        self.stdout.write(
            'Contraseña: 123456bL'
        )

        self.stdout.write(
            '----------------------------------------'
        )

        self.stdout.write(
            'ALUMNOS'
        )

        self.stdout.write(
            'Contraseña común: 123456789'
        )

        self.stdout.write('')

        self.stdout.write(
            'Daniel: '
            'danielholgadogonzalez@hotmail.com'
        )

        self.stdout.write(
            'Indira: '
            'indirahuertaslucendo@hotmail.com'
        )

        self.stdout.write(
            'Sergio: '
            'sergiocuellaralmagro@hotmail.com'
        )

        self.stdout.write(
            'Diego: '
            'diegodeltoromota@hotmail.com'
        )

        self.stdout.write(
            '----------------------------------------'
        )

        self.stdout.write('')

        self.stdout.write(
            'Para iniciar PRESENTE:'
        )

        self.stdout.write(
            'python manage.py runserver'
        )