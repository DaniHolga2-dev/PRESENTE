import uuid

from django.db import models


class Profesor(models.Model):

    nombre = models.CharField(
        max_length=100
    )

    apellidos = models.CharField(
        max_length=150
    )

    email = models.EmailField(
        unique=True
    )

    foto = models.ImageField(
        upload_to='profesores/',
        blank=True,
        null=True
    )

    def __str__(self):
        return f"{self.nombre} {self.apellidos}"


class Grupo(models.Model):

    nombre = models.CharField(
        max_length=100
    )

    asignatura = models.CharField(
        max_length=150
    )

    profesor = models.ForeignKey(
        Profesor,
        on_delete=models.CASCADE
    )

    def __str__(self):
        return f"{self.asignatura} - {self.nombre}"


class Alumno(models.Model):

    nombre = models.CharField(
        max_length=100
    )

    apellidos = models.CharField(
        max_length=150
    )

    carrera = models.CharField(
        max_length=150
    )

    curso = models.CharField(
        max_length=50
    )

    email = models.EmailField(
        unique=True
    )

    password = models.CharField(
        max_length=128
    )

    foto = models.ImageField(
        upload_to='alumnos/',
        blank=True,
        null=True
    )

    grupo = models.ForeignKey(
        Grupo,
        on_delete=models.CASCADE
    )

    def __str__(self):
        return f"{self.nombre} {self.apellidos}"


class Clase(models.Model):

    grupo = models.ForeignKey(
        Grupo,
        on_delete=models.CASCADE
    )

    fecha = models.DateField()

    hora_inicio = models.TimeField()

    asistencia_abierta = models.BooleanField(
        default=False
    )

    # Token que se introduce dentro del código QR.
    # Se irá sustituyendo cada 10 segundos mientras
    # la asistencia permanezca abierta.
    token_qr = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True
    )

    # Guarda el momento exacto en el que se creó
    # el token QR actualmente válido.
    token_qr_generado_en = models.DateTimeField(
        blank=True,
        null=True
    )

    def __str__(self):
        return f"{self.grupo} - {self.fecha}"


class Asistencia(models.Model):

    ESTADOS = [
        ('presente', 'Presente'),
        ('tarde', 'Tarde'),
        ('ausente', 'Ausente'),
    ]

    alumno = models.ForeignKey(
        Alumno,
        on_delete=models.CASCADE
    )

    clase = models.ForeignKey(
        Clase,
        on_delete=models.CASCADE
    )

    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default='ausente'
    )

    hora_registro = models.TimeField(
        blank=True,
        null=True
    )

    class Meta:

        constraints = [
            models.UniqueConstraint(
                fields=[
                    'alumno',
                    'clase'
                ],
                name='asistencia_unica_por_alumno_clase'
            )
        ]

    def __str__(self):

        return (
            f"{self.alumno} - "
            f"{self.clase} - "
            f"{self.estado}"
        )


class Justificacion(models.Model):

    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('aprobada', 'Aprobada'),
        ('rechazada', 'Rechazada'),
    ]

    asistencia = models.OneToOneField(
        Asistencia,
        on_delete=models.CASCADE
    )

    motivo = models.TextField()

    documento = models.ImageField(
        upload_to='justificaciones/',
        blank=True,
        null=True
    )

    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default='pendiente'
    )

    fecha_solicitud = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):

        return (
            f"Justificación de "
            f"{self.asistencia.alumno} - "
            f"{self.estado}"
        )


class SolicitudSoporte(models.Model):

    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('aprobada', 'Aprobada'),
        ('rechazada', 'Rechazada'),
    ]

    alumno = models.ForeignKey(
        Alumno,
        on_delete=models.CASCADE
    )

    clase = models.ForeignKey(
        Clase,
        on_delete=models.CASCADE
    )

    motivo = models.TextField()

    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default='pendiente'
    )

    fecha_solicitud = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):

        return (
            f"{self.alumno} - "
            f"{self.clase} - "
            f"{self.estado}"
        )