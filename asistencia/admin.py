from django.contrib import admin
from .models import Profesor, Grupo, Alumno, Clase, Asistencia, Justificacion

admin.site.register(Profesor)
admin.site.register(Grupo)
admin.site.register(Alumno)
admin.site.register(Clase)
admin.site.register(Asistencia)
admin.site.register(Justificacion)