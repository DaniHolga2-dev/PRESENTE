import base64
import math
import os
import uuid
from datetime import datetime, timedelta
from io import BytesIO

import qrcode

from django.contrib import messages
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import User
from django.db import transaction
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone

from .forms import RegistroAlumnoForm
from .models import (
    Profesor,
    Grupo,
    Alumno,
    Clase,
    Asistencia,
    Justificacion,
    SolicitudSoporte,
)


# =========================================================
# FUNCIONES AUXILIARES
# =========================================================

def generar_qr_base64(url):
    qr = qrcode.make(url)
    buffer = BytesIO()
    qr.save(buffer, format='PNG')

    return base64.b64encode(
        buffer.getvalue()
    ).decode('utf-8')


def calcular_distancia_metros(lat1, lon1, lat2, lon2):
    radio_tierra = 6371000

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)

    diferencia_lat = math.radians(
        lat2 - lat1
    )

    diferencia_lon = math.radians(
        lon2 - lon1
    )

    a = (
        math.sin(diferencia_lat / 2) ** 2
        + math.cos(lat1_rad)
        * math.cos(lat2_rad)
        * math.sin(diferencia_lon / 2) ** 2
    )

    c = 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a)
    )

    return radio_tierra * c


# =========================================================
# GENERAL
# =========================================================

def inicio(request):
    profesor_id = request.session.get('profesor_id')
    alumno_id = request.session.get('alumno_id')

    if profesor_id:
        profesor = Profesor.objects.filter(id=profesor_id).first()

        if profesor:
            return render(
                request,
                'asistencia/inicio.html',
                {
                    'profesor': profesor,
                    'sesion_profesor': True,
                }
            )

        request.session.pop('profesor_id', None)

    if alumno_id:
        alumno = Alumno.objects.filter(id=alumno_id).first()

        if alumno:
            return render(
                request,
                'asistencia/inicio.html',
                {
                    'alumno': alumno,
                    'sesion_alumno': True,
                }
            )

        request.session.pop('alumno_id', None)

    return render(
        request,
        'asistencia/inicio.html',
        {
            'sesion_profesor': False,
            'sesion_alumno': False,
        }
    )


def seleccionar_login(request):
    return render(
        request,
        'asistencia/login.html'
    )


# =========================================================
# LOGIN PROFESOR
# =========================================================

def login_profesor(request):
    if request.session.get('profesor_id'):
        return redirect(
            'panel_profesor'
        )

    if request.method == 'POST':
        username = request.POST.get(
            'username'
        )

        password = request.POST.get(
            'password'
        )

        usuario = authenticate(
            request,
            username=username,
            password=password
        )

        if usuario is not None:
            try:
                profesor = Profesor.objects.get(
                    email=usuario.email
                )

            except Profesor.DoesNotExist:
                profesor = None

            if profesor:
                request.session[
                    'profesor_id'
                ] = profesor.id

                request.session.pop(
                    'alumno_id',
                    None
                )

                return redirect(
                    'panel_profesor'
                )

            messages.error(
                request,
                'No existe un perfil de profesor asociado.'
            )

        else:
            messages.error(
                request,
                'Usuario o contraseña incorrectos.'
            )

    return render(
        request,
        'asistencia/login_profesor.html'
    )


# =========================================================
# REGISTRO PROFESOR
# =========================================================

def registro_profesor(request):
    if request.session.get('profesor_id'):
        return redirect(
            'panel_profesor'
        )

    if request.method == 'POST':
        nombre = request.POST.get(
            'nombre',
            ''
        ).strip()

        apellidos = request.POST.get(
            'apellidos',
            ''
        ).strip()

        email = request.POST.get(
            'email',
            ''
        ).strip()

        password = request.POST.get(
            'password',
            ''
        )

        password2 = request.POST.get(
            'password2',
            ''
        )

        if not all([
            nombre,
            apellidos,
            email,
            password,
            password2
        ]):
            messages.error(
                request,
                'Completa todos los campos.'
            )

            return render(
                request,
                'asistencia/registro_profesor.html'
            )

        if password != password2:
            messages.error(
                request,
                'Las contraseñas no coinciden.'
            )

            return render(
                request,
                'asistencia/registro_profesor.html'
            )

        if Profesor.objects.filter(
            email__iexact=email
        ).exists():
            messages.error(
                request,
                'Ya existe un profesor con ese correo.'
            )

            return render(
                request,
                'asistencia/registro_profesor.html'
            )

        if User.objects.filter(
            username__iexact=email
        ).exists():
            messages.error(
                request,
                'Ya existe una cuenta con ese correo.'
            )

            return render(
                request,
                'asistencia/registro_profesor.html'
            )

        try:
            with transaction.atomic():
                profesor = Profesor.objects.create(
                    nombre=nombre,
                    apellidos=apellidos,
                    email=email
                )

                User.objects.create_user(
                    username=email,
                    email=email,
                    password=password,
                    first_name=nombre,
                    last_name=apellidos
                )

                request.session[
                    'profesor_id'
                ] = profesor.id

                request.session.pop(
                    'alumno_id',
                    None
                )

            messages.success(
                request,
                'Cuenta creada correctamente.'
            )

            return redirect(
                'panel_profesor'
            )

        except Exception:
            messages.error(
                request,
                'No se ha podido crear la cuenta.'
            )

    return render(
        request,
        'asistencia/registro_profesor.html'
    )


# =========================================================
# LOGOUT PROFESOR
# =========================================================

def logout_profesor(request):
    request.session.pop(
        'profesor_id',
        None
    )

    return redirect(
        'inicio'
    )


# =========================================================
# PANEL PROFESOR
# =========================================================

def panel_profesor(request):
    profesor_id = request.session.get(
        'profesor_id'
    )

    if not profesor_id:
        return redirect(
            'seleccionar_login'
        )

    profesor = get_object_or_404(
        Profesor,
        id=profesor_id
    )

    grupos = Grupo.objects.filter(
        profesor=profesor
    )

    return render(
        request,
        'asistencia/panel_profesor.html',
        {
            'profesor': profesor,
            'grupos': grupos,
        }
    )


# =========================================================
# CREAR GRUPO
# =========================================================

def crear_grupo(request,):
    profesor_id = request.session.get(
        'profesor_id'
    )

    if not profesor_id:
        return redirect(
            'seleccionar_login'
        )

    profesor = get_object_or_404(
        Profesor,
        id=profesor_id
    )

    if request.method == 'POST':
        nombre = request.POST.get(
            'nombre'
        )

        asignatura = request.POST.get(
            'asignatura'
        )

        if nombre and asignatura:
            Grupo.objects.create(
                nombre=nombre,
                asignatura=asignatura,
                profesor=profesor
            )

            messages.success(
                request,
                'Grupo creado correctamente.'
            )

            return redirect(
                'panel_profesor'
            )

        messages.error(
            request,
            'Completa todos los campos.'
        )

    return render(
        request,
        'asistencia/crear_grupo.html',
        {
            'profesor': profesor
        }
    )


# =========================================================
# DETALLE GRUPO
# =========================================================

def detalle_grupo(request, grupo_id):
    profesor_id = request.session.get(
        'profesor_id'
    )

    if not profesor_id:
        return redirect(
            'seleccionar_login'
        )

    grupo = get_object_or_404(
        Grupo,
        id=grupo_id,
        profesor_id=profesor_id
    )

    alumnos = Alumno.objects.filter(
        grupo=grupo
    ).order_by(
        'apellidos',
        'nombre'
    )

    clases = Clase.objects.filter(
        grupo=grupo
    ).order_by(
        'fecha',
        'hora_inicio'
    )

    return render(
        request,
        'asistencia/detalle_grupo.html',
        {
            'grupo': grupo,
            'alumnos': alumnos,
            'clases': clases,
        }
    )


# =========================================================
# CAMBIAR COLOR GRUPO
# =========================================================

def cambiar_color_grupo(request, grupo_id):
    profesor_id = request.session.get(
        'profesor_id'
    )

    if not profesor_id:
        return redirect(
            'seleccionar_login'
        )

    grupo = get_object_or_404(
        Grupo,
        id=grupo_id,
        profesor_id=profesor_id
    )

    if request.method == 'POST':
        color = request.POST.get(
            'color'
        )

        colores_validos = [
            opcion[0]
            for opcion in Grupo.COLORES
        ]

        if color in colores_validos:
            grupo.color = color

            grupo.save(
                update_fields=[
                    'color'
                ]
            )

    return redirect(
        'detalle_grupo',
        grupo_id=grupo.id
    )


# =========================================================
# CREAR CLASE
# =========================================================

def crear_clase(request, grupo_id):
    profesor_id = request.session.get(
        'profesor_id'
    )

    if not profesor_id:
        return redirect(
            'seleccionar_login'
        )

    grupo = get_object_or_404(
        Grupo,
        id=grupo_id,
        profesor_id=profesor_id
    )

    if request.method == 'POST':
        fecha = request.POST.get(
            'fecha'
        )

        hora_inicio = request.POST.get(
            'hora_inicio'
        )

        if fecha and hora_inicio:
            Clase.objects.create(
                grupo=grupo,
                fecha=fecha,
                hora_inicio=hora_inicio
            )

            messages.success(
                request,
                'Clase creada correctamente.'
            )

            return redirect(
                'detalle_grupo',
                grupo_id=grupo.id
            )

        messages.error(
            request,
            'Indica la fecha y la hora.'
        )

    return render(
        request,
        'asistencia/crear_clase.html',
        {
            'grupo': grupo
        }
    )


# =========================================================
# CLASES PROFESOR
# =========================================================

def clases_profesor(request):
    profesor_id = request.session.get('profesor_id')

    if not profesor_id:
        return redirect('seleccionar_login')

    profesor = get_object_or_404(
        Profesor,
        id=profesor_id
    )

    clases = (
        Clase.objects.filter(
            grupo__profesor=profesor
        )
        .select_related('grupo')
        .order_by(
            '-fecha',
            '-hora_inicio'
        )
    )

    return render(
        request,
        'asistencia/clases_profesor.html',
        {
            'profesor': profesor,
            'clases': clases,
        }
    )


# =========================================================
# GESTIONAR ASISTENCIA
# =========================================================

def gestionar_asistencia(request, clase_id):
    profesor_id = request.session.get('profesor_id')

    if not profesor_id:
        return redirect('seleccionar_login')

    clase = get_object_or_404(
        Clase,
        id=clase_id,
        grupo__profesor_id=profesor_id
    )

    alumnos = Alumno.objects.filter(
        grupo=clase.grupo
    ).order_by(
        'apellidos',
        'nombre'
    )

    registros = []
    total_presentes = 0
    total_tardes = 0
    total_ausentes = 0
    total_pendientes = 0

    for alumno in alumnos:
        asistencia = Asistencia.objects.filter(
            alumno=alumno,
            clase=clase
        ).first()

        registros.append({
            'alumno': alumno,
            'asistencia': asistencia,
        })

        if asistencia is None:
            total_pendientes += 1

        elif asistencia.estado == 'presente':
            total_presentes += 1

        elif asistencia.estado == 'tarde':
            total_tardes += 1

        elif asistencia.estado == 'ausente':
            total_ausentes += 1

    total_alumnos = alumnos.count()

    qr_base64 = None
    url_qr = None

    if clase.asistencia_abierta:
        ahora = timezone.now()

        # Si no existe token o el actual tiene 5 segundos
        # o más, generamos uno nuevo.
        if (
            not clase.token_qr_generado_en
            or (
                ahora -
                clase.token_qr_generado_en
            ).total_seconds() >= 5
        ):
            clase.token_qr = uuid.uuid4()
            clase.token_qr_generado_en = ahora

            clase.save(
                update_fields=[
                    'token_qr',
                    'token_qr_generado_en'
                ]
            )

        url_qr = request.build_absolute_uri(
            reverse(
                'registrar_asistencia',
                args=[clase.token_qr]
            )
        )

        qr_base64 = generar_qr_base64(
            url_qr
        )

    return render(
        request,
        'asistencia/gestionar_asistencia.html',
        {
            'clase': clase,
            'registros': registros,
            'qr_base64': qr_base64,
            'url_qr': url_qr,
            'total_alumnos': total_alumnos,
            'total_presentes': total_presentes,
            'total_tardes': total_tardes,
            'total_ausentes': total_ausentes,
            'total_pendientes': total_pendientes,
        }
    )


# =========================================================
# ABRIR ASISTENCIA
# UBICACIÓN DEL PROFESOR + PRIMER TOKEN QR
# =========================================================

def abrir_asistencia(request, clase_id):
    profesor_id = request.session.get('profesor_id')

    if not profesor_id:
        return redirect('seleccionar_login')

    clase = get_object_or_404(
        Clase,
        id=clase_id,
        grupo__profesor_id=profesor_id
    )

    if request.method != 'POST':
        messages.error(
            request,
            'Para abrir la asistencia es necesario verificar tu ubicación.'
        )

        return redirect(
            'gestionar_asistencia',
            clase_id=clase.id
        )

    latitud = request.POST.get(
        'latitud_profesor'
    )

    longitud = request.POST.get(
        'longitud_profesor'
    )

    if not latitud or not longitud:
        messages.error(
            request,
            'No se ha podido obtener tu ubicación. '
            'Debes permitir el acceso a la ubicación '
            'para abrir la asistencia.'
        )

        return redirect(
            'gestionar_asistencia',
            clase_id=clase.id
        )

    try:
        latitud = float(latitud)
        longitud = float(longitud)

    except (TypeError, ValueError):
        messages.error(
            request,
            'La ubicación recibida no es válida.'
        )

        return redirect(
            'gestionar_asistencia',
            clase_id=clase.id
        )

    if not (
        -90 <= latitud <= 90
        and
        -180 <= longitud <= 180
    ):
        messages.error(
            request,
            'La ubicación recibida está fuera '
            'de los límites permitidos.'
        )

        return redirect(
            'gestionar_asistencia',
            clase_id=clase.id
        )

    # Guardamos el punto de referencia del profesor.
    clase.latitud_profesor = latitud
    clase.longitud_profesor = longitud

    # Abrimos asistencia.
    clase.asistencia_abierta = True

    # Creamos el primer QR.
    clase.token_qr = uuid.uuid4()
    clase.token_qr_generado_en = timezone.now()

    clase.save(
        update_fields=[
            'asistencia_abierta',
            'token_qr',
            'token_qr_generado_en',
            'latitud_profesor',
            'longitud_profesor',
        ]
    )

    messages.success(
        request,
        'La asistencia se ha abierto correctamente. '
        'Ubicación del aula guardada.'
    )

    return redirect(
        'gestionar_asistencia',
        clase_id=clase.id
    )


# =========================================================
# CERRAR ASISTENCIA
# =========================================================

def cerrar_asistencia(request, clase_id):
    profesor_id = request.session.get('profesor_id')

    if not profesor_id:
        return redirect('seleccionar_login')

    clase = get_object_or_404(
        Clase,
        id=clase_id,
        grupo__profesor_id=profesor_id
    )

    alumnos = Alumno.objects.filter(
        grupo=clase.grupo
    )

    # Los alumnos que no hayan fichado pasan a ausente.
    for alumno in alumnos:
        Asistencia.objects.get_or_create(
            alumno=alumno,
            clase=clase,
            defaults={
                'estado': 'ausente'
            }
        )

    clase.asistencia_abierta = False
    clase.token_qr_generado_en = None

    clase.save(
        update_fields=[
            'asistencia_abierta',
            'token_qr_generado_en'
        ]
    )

    messages.success(
        request,
        'La asistencia se ha cerrado correctamente.'
    )

    return redirect(
        'gestionar_asistencia',
        clase_id=clase.id
    )


# =========================================================
# RENOVAR QR - PROFESOR
# =========================================================

def renovar_qr(request, clase_id):
    profesor_id = request.session.get('profesor_id')

    if not profesor_id:
        return JsonResponse(
            {
                'ok': False,
                'error': 'No autorizado.'
            },
            status=403
        )

    clase = get_object_or_404(
        Clase,
        id=clase_id,
        grupo__profesor_id=profesor_id
    )

    if not clase.asistencia_abierta:
        return JsonResponse(
            {
                'ok': False,
                'cerrada': True,
                'error': 'La asistencia está cerrada.'
            },
            status=400
        )

    clase.token_qr = uuid.uuid4()
    clase.token_qr_generado_en = timezone.now()

    clase.save(
        update_fields=[
            'token_qr',
            'token_qr_generado_en'
        ]
    )

    url_qr = request.build_absolute_uri(
        reverse(
            'registrar_asistencia',
            args=[clase.token_qr]
        )
    )

    qr_base64 = generar_qr_base64(
        url_qr
    )

    return JsonResponse(
        {
            'ok': True,
            'qr_base64': qr_base64,
            'url_qr': url_qr,
            'token_qr': str(clase.token_qr),
            'valido_segundos': 5,
        }
    )


# =========================================================
# QR ACTUAL PARA EL ALUMNO
# =========================================================

def qr_clase(request, clase_id):
    alumno_id = request.session.get('alumno_id')

    if not alumno_id:
        return JsonResponse(
            {
                'ok': False,
                'error': 'No autorizado.'
            },
            status=403
        )

    alumno = get_object_or_404(
        Alumno,
        id=alumno_id
    )

    # Impide consultar el QR de una clase
    # perteneciente a otro grupo.
    clase = get_object_or_404(
        Clase,
        id=clase_id,
        grupo=alumno.grupo
    )

    if not clase.asistencia_abierta:
        return JsonResponse(
            {
                'ok': False,
                'cerrada': True,
                'error': 'La asistencia está cerrada.'
            },
            status=400
        )

    # Si el alumno ya ha fichado no necesita
    # seguir recibiendo códigos QR.
    if Asistencia.objects.filter(
        alumno=alumno,
        clase=clase
    ).exists():
            return JsonResponse(
            {
                'ok': False,
                'ya_registrada': True,
                'error': 'Ya has registrado tu asistencia.'
            },
            status=400
        )

    ahora = timezone.now()

    # El mismo token es compartido por profesor y alumnos.
    # Solo se renueva cuando han transcurrido 5 segundos.
    if (
        not clase.token_qr_generado_en
        or (
            ahora -
            clase.token_qr_generado_en
        ).total_seconds() >= 5
    ):
        clase.token_qr = uuid.uuid4()
        clase.token_qr_generado_en = ahora

        clase.save(
            update_fields=[
                'token_qr',
                'token_qr_generado_en'
            ]
        )

    url_qr = request.build_absolute_uri(
        reverse(
            'registrar_asistencia',
            args=[clase.token_qr]
        )
    )

    qr_base64 = generar_qr_base64(
        url_qr
    )

    return JsonResponse(
        {
            'ok': True,
            'clase_id': clase.id,
            'token_qr': str(clase.token_qr),
            'qr_base64': qr_base64,
            'url_qr': url_qr,
            'valido_segundos': 5,
        }
    )


# =========================================================
# CONTROL GENERAL DE ASISTENCIA - PROFESOR
# =========================================================

def control_asistencia(request):
    profesor_id = request.session.get('profesor_id')

    if not profesor_id:
        return redirect('seleccionar_login')

    profesor = get_object_or_404(
        Profesor,
        id=profesor_id
    )

    grupos = Grupo.objects.filter(
        profesor=profesor
    ).order_by(
        'asignatura',
        'nombre'
    )

    grupos_con_datos = []

    total_alumnos_global = 0
    total_registros_global = 0
    total_presentes_global = 0
    total_tardes_global = 0
    total_ausentes_global = 0

    for grupo in grupos:
        alumnos = Alumno.objects.filter(
            grupo=grupo
        ).order_by(
            'apellidos',
            'nombre'
        )

        clases = Clase.objects.filter(
            grupo=grupo
        )

        total_clases_grupo = clases.count()

        alumnos_con_datos = []

        presentes_grupo = 0
        tardes_grupo = 0
        ausentes_grupo = 0
        registros_grupo = 0

        for alumno in alumnos:
            asistencias = Asistencia.objects.filter(
                alumno=alumno,
                clase__grupo=grupo
            )

            presentes = asistencias.filter(
                estado='presente'
            ).count()

            tardes = asistencias.filter(
                estado='tarde'
            ).count()

            ausentes = asistencias.filter(
                estado='ausente'
            ).count()

            total_registros = (
                presentes +
                tardes +
                ausentes
            )

            asistencias_validas = (
                presentes +
                tardes
            )

            if total_registros > 0:
                porcentaje = round(
                    (
                        asistencias_validas /
                        total_registros
                    ) * 100,
                    1
                )
            else:
                porcentaje = 0

            alumnos_con_datos.append({
                'alumno': alumno,
                'presentes': presentes,
                'tardes': tardes,
                'ausentes': ausentes,
                'total_registros': total_registros,
                'porcentaje': porcentaje,
            })

            presentes_grupo += presentes
            tardes_grupo += tardes
            ausentes_grupo += ausentes
            registros_grupo += total_registros

        asistencias_validas_grupo = (
            presentes_grupo +
            tardes_grupo
        )

        if registros_grupo > 0:
            porcentaje_grupo = round(
                (
                    asistencias_validas_grupo /
                    registros_grupo
                ) * 100,
                1
            )
        else:
            porcentaje_grupo = 0

        total_alumnos_grupo = alumnos.count()

        grupos_con_datos.append({
            'grupo': grupo,
            'alumnos': alumnos_con_datos,
            'total_alumnos': total_alumnos_grupo,
            'total_clases': total_clases_grupo,
            'presentes': presentes_grupo,
            'tardes': tardes_grupo,
            'ausentes': ausentes_grupo,
            'total_registros': registros_grupo,
            'porcentaje': porcentaje_grupo,
        })

        total_alumnos_global += total_alumnos_grupo
        total_registros_global += registros_grupo
        total_presentes_global += presentes_grupo
        total_tardes_global += tardes_grupo
        total_ausentes_global += ausentes_grupo

    asistencias_validas_global = (
        total_presentes_global +
        total_tardes_global
    )

    if total_registros_global > 0:
        porcentaje_global = round(
            (
                asistencias_validas_global /
                total_registros_global
            ) * 100,
            1
        )
    else:
        porcentaje_global = 0

    justificaciones_pendientes = (
        Justificacion.objects.filter(
            asistencia__clase__grupo__profesor=profesor,
            estado='pendiente'
        ).count()
    )

    ultimos_registros = (
        Asistencia.objects.filter(
            clase__grupo__profesor=profesor,
            estado__in=[
                'presente',
                'tarde'
            ]
        )
        .select_related(
            'alumno',
            'clase',
            'clase__grupo'
        )
        .exclude(
            hora_registro__isnull=True
        )
        .order_by(
            '-clase__fecha',
            '-hora_registro'
        )[:5]
    )

    hoy = timezone.localdate()
    ahora = timezone.localtime()

    proximas_query = (
        Clase.objects.filter(
            grupo__profesor=profesor,
            fecha__gte=hoy
        )
        .select_related('grupo')
        .order_by(
            'fecha',
            'hora_inicio'
        )
    )

    proximas_clases = []

    for clase in proximas_query:
        if (
            clase.fecha == hoy and
            clase.hora_inicio < ahora.time()
        ):
            continue

        proximas_clases.append(clase)

        if len(proximas_clases) == 3:
            break

    return render(
        request,
        'asistencia/control_asistencia.html',
        {
            'profesor': profesor,
            'grupos_con_datos': grupos_con_datos,
            'total_grupos': grupos.count(),
            'total_alumnos': total_alumnos_global,
            'total_presentes': total_presentes_global,
            'total_tardes': total_tardes_global,
            'total_ausentes': total_ausentes_global,
            'total_registros': total_registros_global,
            'porcentaje_global': porcentaje_global,
            'justificaciones_pendientes': justificaciones_pendientes,
            'ultimos_registros': ultimos_registros,
            'proximas_clases': proximas_clases,
        }
    )


# =========================================================
# REGISTROS DE ASISTENCIA - PROFESOR
# =========================================================

def registros_asistencia(request):
    profesor_id = request.session.get('profesor_id')

    if not profesor_id:
        return redirect('seleccionar_login')

    profesor = get_object_or_404(
        Profesor,
        id=profesor_id
    )

    registros = (
        Asistencia.objects.filter(
            clase__grupo__profesor=profesor
        )
        .select_related(
            'alumno',
            'clase',
            'clase__grupo'
        )
        .order_by(
            '-clase__fecha',
            '-hora_registro'
        )
    )

    return render(
        request,
        'asistencia/registros_asistencia.html',
        {
            'profesor': profesor,
            'registros': registros,
        }
    )


# =========================================================
# NOTIFICACIONES PROFESOR
# =========================================================

def notificaciones_profesor(request):
    profesor_id = request.session.get('profesor_id')

    if not profesor_id:
        return redirect('seleccionar_login')

    profesor = get_object_or_404(
        Profesor,
        id=profesor_id
    )

    justificaciones = (
        Justificacion.objects.filter(
            asistencia__clase__grupo__profesor_id=profesor_id,
            estado='pendiente'
        )
        .select_related(
            'asistencia',
            'asistencia__alumno',
            'asistencia__clase',
            'asistencia__clase__grupo'
        )
        .order_by('-fecha_solicitud')
    )

    solicitudes_soporte = (
        SolicitudSoporte.objects.filter(
            clase__grupo__profesor_id=profesor_id,
            estado='pendiente'
        )
        .select_related(
            'alumno',
            'clase',
            'clase__grupo'
        )
        .order_by('-fecha_solicitud')
    )

    notificaciones = []

    for justificacion in justificaciones:
        notificaciones.append({
            'tipo': 'justificacion',
            'titulo': 'Nueva justificación',
            'alumno': justificacion.asistencia.alumno,
            'grupo': justificacion.asistencia.clase.grupo,
            'fecha': justificacion.fecha_solicitud,
            'objeto': justificacion,
        })

    for solicitud in solicitudes_soporte:
        notificaciones.append({
            'tipo': 'soporte',
            'titulo': 'Nueva solicitud de soporte',
            'alumno': solicitud.alumno,
            'grupo': solicitud.clase.grupo,
            'fecha': solicitud.fecha_solicitud,
            'objeto': solicitud,
        })

    notificaciones.sort(
        key=lambda notificacion: notificacion['fecha'],
        reverse=True
    )

    return render(
        request,
        'asistencia/notificaciones_profesor.html',
        {
            'profesor': profesor,
            'notificaciones': notificaciones,
            'total_notificaciones': len(notificaciones),
        }
    )


# =========================================================
# JUSTIFICACIONES PROFESOR
# =========================================================

def justificaciones_profesor(request):
    profesor_id = request.session.get('profesor_id')

    if not profesor_id:
        return redirect('seleccionar_login')

    justificaciones = (
        Justificacion.objects.filter(
            asistencia__clase__grupo__profesor_id=profesor_id
        )
        .select_related(
            'asistencia',
            'asistencia__alumno',
            'asistencia__clase',
            'asistencia__clase__grupo'
        )
        .order_by('-fecha_solicitud')
    )

    pendientes = justificaciones.filter(
        estado='pendiente'
    )

    return render(
        request,
        'asistencia/justificaciones_profesor.html',
        {
            'justificaciones': justificaciones,
            'pendientes': pendientes,
        }
    )


def aprobar_justificacion(
    request,
    justificacion_id
):
    profesor_id = request.session.get('profesor_id')

    if not profesor_id:
        return redirect('seleccionar_login')

    justificacion = get_object_or_404(
        Justificacion,
        id=justificacion_id,
        asistencia__clase__grupo__profesor_id=profesor_id
    )

    justificacion.estado = 'aprobada'

    justificacion.save(
        update_fields=[
            'estado'
        ]
    )

    messages.success(
        request,
        'La justificación ha sido aprobada.'
    )

    return redirect(
        'justificaciones_profesor'
    )


def rechazar_justificacion(
    request,
    justificacion_id
):
    profesor_id = request.session.get('profesor_id')

    if not profesor_id:
        return redirect('seleccionar_login')

    justificacion = get_object_or_404(
        Justificacion,
        id=justificacion_id,
        asistencia__clase__grupo__profesor_id=profesor_id
    )

    justificacion.estado = 'rechazada'

    justificacion.save(
        update_fields=[
            'estado'
        ]
    )

    messages.success(
        request,
        'La justificación ha sido rechazada.'
    )

    return redirect(
        'justificaciones_profesor'
    )


# =========================================================
# VER DOCUMENTO JUSTIFICACIÓN
# =========================================================

def ver_documento_justificacion(
    request,
    justificacion_id
):
    justificacion = get_object_or_404(
        Justificacion.objects.select_related(
            'asistencia',
            'asistencia__alumno',
            'asistencia__clase',
            'asistencia__clase__grupo'
        ),
        id=justificacion_id
    )

    alumno_id = request.session.get(
        'alumno_id'
    )

    profesor_id = request.session.get(
        'profesor_id'
    )

    autorizado = False

    if (
        alumno_id and
        justificacion.asistencia.alumno_id
        == alumno_id
    ):
        autorizado = True

    if (
        profesor_id and
        justificacion.asistencia.clase.grupo.profesor_id
        == profesor_id
    ):
        autorizado = True

    if not autorizado:
        raise Http404

    if not justificacion.documento:
        raise Http404

    try:
        archivo = justificacion.documento.open(
            'rb'
        )

        return FileResponse(
            archivo,
            filename=os.path.basename(
                justificacion.documento.name
            )
        )

    except FileNotFoundError:
        raise Http404


# =========================================================
# SOPORTE PROFESOR
# =========================================================

def soporte_profesor(request):
    profesor_id = request.session.get('profesor_id')

    if not profesor_id:
        return redirect('seleccionar_login')

    solicitudes = (
        SolicitudSoporte.objects.filter(
            clase__grupo__profesor_id=profesor_id
        )
        .select_related(
            'alumno',
            'clase',
            'clase__grupo'
        )
        .order_by('-fecha_solicitud')
    )

    pendientes = solicitudes.filter(
        estado='pendiente'
    )

    return render(
        request,
        'asistencia/soporte_profesor.html',
        {
            'solicitudes': solicitudes,
            'pendientes': pendientes,
        }
    )


def aprobar_soporte(request, solicitud_id):
    profesor_id = request.session.get('profesor_id')

    if not profesor_id:
        return redirect('seleccionar_login')

    solicitud = get_object_or_404(
        SolicitudSoporte,
        id=solicitud_id,
        clase__grupo__profesor_id=profesor_id
    )

    asistencia, creada = (
        Asistencia.objects.get_or_create(
            alumno=solicitud.alumno,
            clase=solicitud.clase,
            defaults={
                'estado': 'presente',
                'hora_registro': timezone.localtime().time(),
            }
        )
    )

    if not creada:
        asistencia.estado = 'presente'

        if not asistencia.hora_registro:
            asistencia.hora_registro = (
                timezone.localtime().time()
            )

        asistencia.save(
            update_fields=[
                'estado',
                'hora_registro'
            ]
        )

    solicitud.estado = 'aprobada'

    solicitud.save(
        update_fields=[
            'estado'
        ]
    )

    messages.success(
        request,
        'La asistencia ha sido confirmada.'
    )

    return redirect(
        'soporte_profesor'
    )


def rechazar_soporte(request, solicitud_id):
    profesor_id = request.session.get('profesor_id')

    if not profesor_id:
        return redirect('seleccionar_login')

    solicitud = get_object_or_404(
        SolicitudSoporte,
        id=solicitud_id,
        clase__grupo__profesor_id=profesor_id
    )

    solicitud.estado = 'rechazada'

    solicitud.save(
        update_fields=[
            'estado'
        ]
    )

    messages.success(
        request,
        'La solicitud ha sido rechazada.'
    )

    return redirect(
        'soporte_profesor'
    )


# =========================================================
# LOGIN ALUMNO
# =========================================================

def login_alumno(request):
    if request.session.get('alumno_id'):
        return redirect('grupo_alumno')

    if request.method == 'POST':
        email = request.POST.get(
            'email',
            ''
        ).strip()

        password = request.POST.get(
            'password',
            ''
        )

        try:
            alumno = Alumno.objects.get(
                email__iexact=email
            )

            if check_password(
                password,
                alumno.password
            ):
                request.session[
                    'alumno_id'
                ] = alumno.id

                request.session.pop(
                    'profesor_id',
                    None
                )

                return redirect(
                    'grupo_alumno'
                )

            messages.error(
                request,
                'Correo o contraseña incorrectos.'
            )

        except Alumno.DoesNotExist:
            messages.error(
                request,
                'Correo o contraseña incorrectos.'
            )

    return render(
        request,
        'asistencia/login_alumno.html'
    )


# =========================================================
# REGISTRO ALUMNO
# =========================================================

def registro_alumno(request):
    if request.session.get('alumno_id'):
        return redirect('grupo_alumno')

    if request.method == 'POST':
        form = RegistroAlumnoForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():
            alumno = form.save()

            request.session[
                'alumno_id'
            ] = alumno.id

            request.session.pop(
                'profesor_id',
                None
            )

            messages.success(
                request,
                'Cuenta creada correctamente.'
            )

            return redirect(
                'grupo_alumno'
            )

    else:
        form = RegistroAlumnoForm()

    return render(
        request,
        'asistencia/registro_alumno.html',
        {
            'form': form
        }
    )


# =========================================================
# GRUPO ALUMNO
# =========================================================

def grupo_alumno(request):
    alumno_id = request.session.get(
        'alumno_id'
    )

    if not alumno_id:
        return redirect(
            'seleccionar_login'
        )

    alumno = get_object_or_404(
        Alumno,
        id=alumno_id
    )

    grupo = alumno.grupo

    if not grupo:
        messages.error(
            request,
            'Actualmente no perteneces a ningún grupo.'
        )

        return redirect(
            'inicio'
        )

    profesor = grupo.profesor

    alumnos = Alumno.objects.filter(
        grupo=grupo
    ).order_by(
        'apellidos',
        'nombre'
    )

    return render(
        request,
        'asistencia/grupo_alumno.html',
        {
            'alumno': alumno,
            'grupo': grupo,
            'profesor': profesor,
            'alumnos': alumnos,
        }
    )


# =========================================================
# CLASES ALUMNO
# =========================================================

def clases_alumno(request):
    alumno_id = request.session.get(
        'alumno_id'
    )

    if not alumno_id:
        return redirect(
            'seleccionar_login'
        )

    alumno = get_object_or_404(
        Alumno,
        id=alumno_id
    )

    clases = (
        Clase.objects.filter(
            grupo=alumno.grupo
        )
        .select_related('grupo')
        .order_by(
            '-fecha',
            '-hora_inicio'
        )
    )

    asistencias = {
        asistencia.clase_id: asistencia
        for asistencia in Asistencia.objects.filter(
            alumno=alumno,
            clase__grupo=alumno.grupo
        )
    }

    clases_con_estado = []

    for clase in clases:
        asistencia = asistencias.get(
            clase.id
        )

        if asistencia:
            estado = asistencia.estado

            estado_texto = (
                asistencia.get_estado_display()
            )

        elif clase.asistencia_abierta:
            estado = 'abierta'
            estado_texto = 'Asistencia abierta'

        else:
            estado = 'pendiente'
            estado_texto = 'Pendiente'

        clases_con_estado.append({
            'clase': clase,
            'asistencia': asistencia,
            'estado': estado,
            'estado_texto': estado_texto,
        })

    return render(
        request,
        'asistencia/clases_alumno.html',
        {
            'alumno': alumno,
            'clases': clases,
            'clases_con_estado': clases_con_estado,
        }
    )


# =========================================================
# ASISTENCIA ALUMNO
# =========================================================

def asistencia_alumno(request):
    alumno_id = request.session.get(
        'alumno_id'
    )

    if not alumno_id:
        return redirect(
            'seleccionar_login'
        )

    alumno = get_object_or_404(
        Alumno,
        id=alumno_id
    )

    grupo = alumno.grupo

    asistencias = Asistencia.objects.none()

    total_registros = 0
    total_presentes = 0
    total_tardes = 0
    total_ausencias = 0
    porcentaje_asistencia = 0

    proximas_clases = []
    clases_hoy = []

    if grupo:

        # ---------------------------------------------
        # HISTORIAL
        # ---------------------------------------------

        asistencias = (
            Asistencia.objects.filter(
                alumno=alumno,
                clase__grupo=grupo
            )
            .select_related(
                'clase',
                'clase__grupo'
            )
            .order_by(
                '-clase__fecha',
                '-clase__hora_inicio'
            )
        )

        total_registros = (
            asistencias.count()
        )

        total_presentes = (
            asistencias.filter(
                estado='presente'
            ).count()
        )

        total_tardes = (
            asistencias.filter(
                estado='tarde'
            ).count()
        )

        total_ausencias = (
            asistencias.filter(
                estado='ausente'
            ).count()
        )

        if total_registros > 0:
            porcentaje_asistencia = round(
                (
                    (
                        total_presentes +
                        total_tardes
                    ) /
                    total_registros
                ) * 100,
                1
            )

        hoy = timezone.localdate()
        ahora = timezone.localtime()

        # ---------------------------------------------
        # PRÓXIMAS CLASES
        # ---------------------------------------------

        proximas_query = (
            Clase.objects.filter(
                grupo=grupo,
                fecha__gte=hoy
            )
            .select_related('grupo')
            .order_by(
                'fecha',
                'hora_inicio'
            )
        )

        for clase in proximas_query:
            if (
                clase.fecha == hoy
                and
                clase.hora_inicio < ahora.time()
            ):
                continue

            proximas_clases.append(
                clase
            )

            if len(proximas_clases) == 3:
                break

        # ---------------------------------------------
        # CLASES DE HOY
        # ---------------------------------------------

        clases_hoy_query = (
            Clase.objects.filter(
                grupo=grupo,
                fecha=hoy
            )
            .select_related('grupo')
            .order_by('hora_inicio')
        )

        for clase in clases_hoy_query:
            asistencia = (
                Asistencia.objects.filter(
                    alumno=alumno,
                    clase=clase
                ).first()
            )

            qr_base64 = None
            url_registro = None
            token_qr = None

            # El QR solo aparece si:
            # - la asistencia está abierta
            # - el alumno todavía no ha fichado
            if (
                clase.asistencia_abierta
                and
                not asistencia
            ):
                ahora_qr = timezone.now()

                if (
                    not clase.token_qr_generado_en
                    or (
                        ahora_qr -
                        clase.token_qr_generado_en
                    ).total_seconds() >= 5
                ):
                    clase.token_qr = uuid.uuid4()

                    clase.token_qr_generado_en = (
                        ahora_qr
                    )

                    clase.save(
                        update_fields=[
                            'token_qr',
                            'token_qr_generado_en'
                        ]
                    )

                url_registro = reverse(
                    'registrar_asistencia',
                    args=[
                        clase.token_qr
                    ]
                )

                qr_base64 = generar_qr_base64(
                    request.build_absolute_uri(
                        url_registro
                    )
                )

                token_qr = str(
                    clase.token_qr
                )

            clases_hoy.append({
                'clase': clase,
                'asistencia': asistencia,
                'qr_base64': qr_base64,
                'url_registro': url_registro,
                'token_qr': token_qr,
            })

    return render(
        request,
        'asistencia/asistencia_alumno.html',
        {
            'alumno': alumno,
            'grupo': grupo,
            'asistencias': asistencias,
            'total_registros': total_registros,
            'total_presentes': total_presentes,
            'total_tardes': total_tardes,
            'total_ausencias': total_ausencias,
            'porcentaje_asistencia': porcentaje_asistencia,
            'proximas_clases': proximas_clases,
            'clases_hoy': clases_hoy,
        }
    )


# =========================================================
# JUSTIFICACIONES ALUMNO
# =========================================================

def justificaciones_alumno(request):
    alumno_id = request.session.get(
        'alumno_id'
    )

    if not alumno_id:
        return redirect(
            'seleccionar_login'
        )

    alumno = get_object_or_404(
        Alumno,
        id=alumno_id
    )

    ausencias_disponibles = (
        Asistencia.objects.filter(
            alumno=alumno,
            estado='ausente',
            justificacion__isnull=True
        )
        .select_related(
            'clase',
            'clase__grupo'
        )
        .order_by(
            '-clase__fecha'
        )
    )

    justificaciones = (
        Justificacion.objects.filter(
            asistencia__alumno=alumno
        )
        .select_related(
            'asistencia',
            'asistencia__clase',
            'asistencia__clase__grupo'
        )
        .order_by(
            '-fecha_solicitud'
        )
    )

    if request.method == 'POST':
        asistencia_id = request.POST.get(
            'asistencia'
        )

        motivo = request.POST.get(
            'motivo',
            ''
        ).strip()

        documento = request.FILES.get(
            'documento'
        )

        asistencia = (
            Asistencia.objects.filter(
                id=asistencia_id,
                alumno=alumno,
                estado='ausente'
            ).first()
        )

        if not asistencia:
            messages.error(
                request,
                'Selecciona una falta válida.'
            )

        elif Justificacion.objects.filter(
            asistencia=asistencia
        ).exists():
            messages.error(
                request,
                'Esta falta ya tiene una justificación.'
            )

        elif not motivo:
            messages.error(
                request,
                'Indica el motivo de la ausencia.'
            )

        elif (
            documento
            and not documento.content_type.startswith(
                'image/'
            )
        ):
            messages.error(
                request,
                'El justificante debe ser una imagen.'
            )

        elif (
            documento
            and documento.size >
            5 * 1024 * 1024
        ):
            messages.error(
                request,
                'La imagen no puede superar los 5 MB.'
            )

        else:
            Justificacion.objects.create(
                asistencia=asistencia,
                motivo=motivo,
                documento=documento
            )

            messages.success(
                request,
                'La justificación ha sido enviada al profesor.'
            )

            return redirect(
                'justificaciones_alumno'
            )

    return render(
        request,
        'asistencia/justificaciones_alumno.html',
        {
            'alumno': alumno,
            'ausencias_disponibles': ausencias_disponibles,
            'justificaciones': justificaciones,
        }
    )


# =========================================================
# SOPORTE GENERAL / ALUMNO
# =========================================================

def soporte(request):
    alumno_id = request.session.get(
        'alumno_id'
    )

    alumno = None

    if alumno_id:
        alumno = Alumno.objects.filter(
            id=alumno_id
        ).first()

    if alumno:
        clases = (
            Clase.objects.filter(
                grupo=alumno.grupo
            )
            .select_related('grupo')
            .order_by(
                '-fecha',
                '-hora_inicio'
            )
        )

    else:
        clases = (
            Clase.objects.select_related(
                'grupo'
            )
            .order_by(
                '-fecha',
                '-hora_inicio'
            )
        )

    if request.method == 'POST':
        email = request.POST.get(
            'email',
            ''
        ).strip()

        clase_id = request.POST.get(
            'clase'
        )

        motivo = request.POST.get(
            'motivo',
            ''
        ).strip()

        if not email or not clase_id or not motivo:
            messages.error(
                request,
                'Completa todos los campos.'
            )

        else:
            alumno_solicitud = (
                Alumno.objects.filter(
                    email__iexact=email
                ).first()
            )

            if not alumno_solicitud:
                messages.error(
                    request,
                    'No existe ningún alumno registrado con ese correo.'
                )

            else:
                clase = Clase.objects.filter(
                    id=clase_id,
                    grupo=alumno_solicitud.grupo
                ).first()

                if not clase:
                    messages.error(
                        request,
                        'La clase seleccionada no pertenece a tu grupo.'
                    )

                elif SolicitudSoporte.objects.filter(
                    alumno=alumno_solicitud,
                    clase=clase,
                    estado='pendiente'
                ).exists():
                    messages.error(
                        request,
                        'Ya tienes una solicitud pendiente para esta clase.'
                    )

                else:
                    SolicitudSoporte.objects.create(
                        alumno=alumno_solicitud,
                        clase=clase,
                        motivo=motivo
                    )

                    messages.success(
                        request,
                        'La solicitud ha sido enviada al profesor.'
                    )

                    return redirect(
                        'soporte'
                    )

    return render(
        request,
        'asistencia/soporte.html',
        {
            'alumno': alumno,
            'clases': clases,
        }
    )


# =========================================================
# LOGOUT ALUMNO
# =========================================================

def logout_alumno(request):
    request.session.pop(
        'alumno_id',
        None
    )

    return redirect(
        'inicio'
    )


# =========================================================
# REGISTRAR ASISTENCIA MEDIANTE QR + UBICACIÓN
# =========================================================

def registrar_asistencia(request, token):
    alumno_id = request.session.get('alumno_id')

    if not alumno_id:
        messages.error(
            request,
            'Debes iniciar sesión como alumno para registrar tu asistencia.'
        )
        return redirect('login_alumno')

    alumno = get_object_or_404(
        Alumno,
        id=alumno_id
    )

    clase = Clase.objects.filter(
        token_qr=token
    ).select_related(
        'grupo'
    ).first()

    if not clase:
        messages.error(
            request,
            'Este código QR ya no es válido.'
        )
        return redirect('asistencia_alumno')

    # -----------------------------------------------------
    # ASISTENCIA ABIERTA
    # -----------------------------------------------------

    if not clase.asistencia_abierta:
        messages.error(
            request,
            'La asistencia de esta clase está cerrada.'
        )
        return redirect('asistencia_alumno')

    # -----------------------------------------------------
    # GRUPO CORRECTO
    # -----------------------------------------------------

    if alumno.grupo_id != clase.grupo_id:
        messages.error(
            request,
            'Este código QR no pertenece a tu grupo.'
        )
        return redirect('asistencia_alumno')

    # -----------------------------------------------------
    # EVITAR DOBLE FICHAJE
    # -----------------------------------------------------

    if Asistencia.objects.filter(
        alumno=alumno,
        clase=clase
    ).exists():
        messages.info(
            request,
            'Tu asistencia ya está registrada.'
        )
        return redirect('asistencia_alumno')

    # -----------------------------------------------------
    # VALIDAR TOKEN DE 5 SEGUNDOS
    # -----------------------------------------------------

    if not clase.token_qr_generado_en:
        messages.error(
            request,
            'Este código QR ha caducado.'
        )
        return redirect('asistencia_alumno')

    segundos_token = (
        timezone.now() -
        clase.token_qr_generado_en
    ).total_seconds()

    if segundos_token > 5:
        messages.error(
            request,
            'El código QR ha caducado. Utiliza el código actualizado.'
        )
        return redirect('asistencia_alumno')

    # -----------------------------------------------------
    # GET: MOSTRAR PANTALLA PARA OBTENER UBICACIÓN
    # -----------------------------------------------------

    if request.method != 'POST':
        return render(
            request,
            'asistencia/registrar_asistencia.html',
            {
                'alumno': alumno,
                'clase': clase,
                'token': token,
            }
        )

    # -----------------------------------------------------
    # UBICACIÓN DEL ALUMNO
    # -----------------------------------------------------

    latitud_alumno = request.POST.get(
        'latitud_alumno'
    )

    longitud_alumno = request.POST.get(
        'longitud_alumno'
    )

    if not latitud_alumno or not longitud_alumno:
        messages.error(
            request,
            'No se ha podido obtener tu ubicación. '
            'Debes permitir el acceso a la ubicación.'
        )

        return redirect(
            'registrar_asistencia',
            token=token
        )

    try:
        latitud_alumno = float(
            latitud_alumno
        )

        longitud_alumno = float(
            longitud_alumno
        )

    except (TypeError, ValueError):
        messages.error(
            request,
            'La ubicación recibida no es válida.'
        )

        return redirect(
            'registrar_asistencia',
            token=token
        )

    if not (
        -90 <= latitud_alumno <= 90
        and
        -180 <= longitud_alumno <= 180
    ):
        messages.error(
            request,
            'La ubicación recibida no es válida.'
        )

        return redirect(
            'registrar_asistencia',
            token=token
        )

    # -----------------------------------------------------
    # UBICACIÓN DEL PROFESOR
    # -----------------------------------------------------

    if (
        clase.latitud_profesor is None
        or
        clase.longitud_profesor is None
    ):
        messages.error(
            request,
            'No existe una ubicación de referencia para esta clase.'
        )
        return redirect('asistencia_alumno')

    # -----------------------------------------------------
    # DISTANCIA PROFESOR ↔ ALUMNO
    # -----------------------------------------------------

    distancia = calcular_distancia_metros(
        float(clase.latitud_profesor),
        float(clase.longitud_profesor),
        latitud_alumno,
        longitud_alumno
    )

    DISTANCIA_MAXIMA_METROS = 100

    if distancia > DISTANCIA_MAXIMA_METROS:
        messages.error(
            request,
            'No puedes registrar la asistencia porque '
            'no te encuentras suficientemente cerca del aula.'
        )
        return redirect('asistencia_alumno')

    # -----------------------------------------------------
    # VOLVER A LEER LA CLASE
    #
    # Mientras el móvil obtenía la ubicación podrían haber
    # cambiado el QR o cerrado la asistencia.
    # -----------------------------------------------------

    clase.refresh_from_db()

    if not clase.asistencia_abierta:
        messages.error(
            request,
            'La asistencia se ha cerrado.'
        )
        return redirect('asistencia_alumno')

    # El token recibido debe seguir siendo exactamente
    # el token actual de la clase.

    if clase.token_qr != token:
        messages.error(
            request,
            'El código QR ha cambiado. Utiliza el nuevo código.'
        )
        return redirect('asistencia_alumno')

    if not clase.token_qr_generado_en:
        messages.error(
            request,
            'El código QR ya no es válido.'
        )
        return redirect('asistencia_alumno')

    segundos_token = (
        timezone.now() -
        clase.token_qr_generado_en
    ).total_seconds()

    if segundos_token > 5:
        messages.error(
            request,
            'El código QR ha caducado. Utiliza el código actualizado.'
        )
        return redirect('asistencia_alumno')

    # -----------------------------------------------------
    # PRESENTE / TARDE
    #
    # Hasta 10 minutos después del inicio = presente.
    # A partir de +10 minutos = tarde.
    # -----------------------------------------------------

    ahora_local = timezone.localtime()

    inicio_clase = timezone.make_aware(
        datetime.combine(
            clase.fecha,
            clase.hora_inicio
        ),
        timezone.get_current_timezone()
    )

    limite_presente = (
        inicio_clase +
        timedelta(minutes=10)
    )

    if ahora_local < limite_presente:
        estado = 'presente'
    else:
        estado = 'tarde'

    # -----------------------------------------------------
    # REGISTRAR
    # -----------------------------------------------------

    asistencia, creada = Asistencia.objects.get_or_create(
        alumno=alumno,
        clase=clase,
        defaults={
            'estado': estado,
            'hora_registro': ahora_local.time(),
        }
    )

    if not creada:
        messages.info(
            request,
            'Tu asistencia ya estaba registrada.'
        )
        return redirect('asistencia_alumno')

    messages.success(
        request,
        'Asistencia registrada correctamente.'
    )

    return redirect('asistencia_alumno')
    # =========================================================
# INFORMES PROFESOR
# =========================================================

def informes_profesor(request):
    profesor_id = request.session.get('profesor_id')

    if not profesor_id:
        return redirect('seleccionar_login')

    profesor = get_object_or_404(
        Profesor,
        id=profesor_id
    )

    grupos = Grupo.objects.filter(
        profesor=profesor
    )

    alumnos = Alumno.objects.filter(
        grupo__profesor=profesor
    ).distinct()

    asistencias = Asistencia.objects.filter(
        clase__grupo__profesor=profesor
    )

    total_grupos = grupos.count()
    total_alumnos = alumnos.count()
    total_registros = asistencias.count()

    total_presentes = asistencias.filter(
        estado='presente'
    ).count()

    total_tardes = asistencias.filter(
        estado='tarde'
    ).count()

    total_ausentes = asistencias.filter(
        estado='ausente'
    ).count()

    if total_registros:
        porcentaje_presentes = round(
            total_presentes /
            total_registros * 100,
            1
        )

        porcentaje_tardes = round(
            total_tardes /
            total_registros * 100,
            1
        )

        porcentaje_ausentes = round(
            total_ausentes /
            total_registros * 100,
            1
        )

        porcentaje_global = round(
            (
                total_presentes +
                total_tardes
            ) /
            total_registros * 100,
            1
        )

    else:
        porcentaje_presentes = 0
        porcentaje_tardes = 0
        porcentaje_ausentes = 0
        porcentaje_global = 0

    return render(
        request,
        'asistencia/informes_profesor.html',
        {
            'profesor': profesor,
            'total_grupos': total_grupos,
            'total_alumnos': total_alumnos,
            'total_registros': total_registros,
            'total_presentes': total_presentes,
            'total_tardes': total_tardes,
            'total_ausentes': total_ausentes,
            'porcentaje_presentes': porcentaje_presentes,
            'porcentaje_tardes': porcentaje_tardes,
            'porcentaje_ausentes': porcentaje_ausentes,
            'porcentaje_global': porcentaje_global,
        }
    )


# =========================================================
# INFORMES ALUMNO
# =========================================================

def informes_alumno(request):
    alumno_id = request.session.get('alumno_id')

    if not alumno_id:
        return redirect('seleccionar_login')

    alumno = get_object_or_404(
        Alumno,
        id=alumno_id
    )

    asistencias = (
        Asistencia.objects.filter(
            alumno=alumno
        )
        .select_related(
            'clase',
            'clase__grupo'
        )
        .order_by(
            '-clase__fecha',
            '-clase__hora_inicio'
        )
    )

    total_registros = asistencias.count()

    total_presentes = asistencias.filter(
        estado='presente'
    ).count()

    total_tardes = asistencias.filter(
        estado='tarde'
    ).count()

    total_ausencias = asistencias.filter(
        estado='ausente'
    ).count()

    if total_registros:
        porcentaje_presentes = round(
            total_presentes /
            total_registros * 100,
            1
        )

        porcentaje_tardes = round(
            total_tardes /
            total_registros * 100,
            1
        )

        porcentaje_ausencias = round(
            total_ausencias /
            total_registros * 100,
            1
        )

        porcentaje_asistencia = round(
            (
                total_presentes +
                total_tardes
            ) /
            total_registros * 100,
            1
        )

    else:
        porcentaje_presentes = 0
        porcentaje_tardes = 0
        porcentaje_ausencias = 0
        porcentaje_asistencia = 0

    return render(
        request,
        'asistencia/informes_alumno.html',
        {
            'alumno': alumno,
            'asistencias': asistencias,
            'total_registros': total_registros,
            'total_presentes': total_presentes,
            'total_tardes': total_tardes,
            'total_ausencias': total_ausencias,
            'porcentaje_presentes': porcentaje_presentes,
            'porcentaje_tardes': porcentaje_tardes,
            'porcentaje_ausencias': porcentaje_ausencias,
            'porcentaje_asistencia': porcentaje_asistencia,
        }
    )


# =========================================================
# AJUSTES PROFESOR
# =========================================================

def ajustes_profesor(request):
    profesor_id = request.session.get('profesor_id')

    if not profesor_id:
        return redirect('seleccionar_login')

    profesor = get_object_or_404(
        Profesor,
        id=profesor_id
    )

    return render(
        request,
        'asistencia/ajustes_profesor.html',
        {
            'profesor': profesor
        }
    )


# =========================================================
# AJUSTES ALUMNO
# =========================================================

def ajustes_alumno(request):
    alumno_id = request.session.get('alumno_id')

    if not alumno_id:
        return redirect('seleccionar_login')

    alumno = get_object_or_404(
        Alumno,
        id=alumno_id
    )

    return render(
        request,
        'asistencia/ajustes_alumno.html',
        {
            'alumno': alumno
        }
    )


# =========================================================
# BORRAR CLASES - PROFESOR
# =========================================================

def borrar_clases(request):
    profesor_id = request.session.get('profesor_id')

    if not profesor_id:
        return redirect('seleccionar_login')

    if request.method != 'POST':
        return redirect('clases_profesor')

    clases_ids = request.POST.getlist('clases')

    if not clases_ids:
        messages.error(
            request,
            'Selecciona al menos una clase para eliminar.'
        )
        return redirect('clases_profesor')

    clases = Clase.objects.filter(
        id__in=clases_ids,
        grupo__profesor_id=profesor_id
    )

    cantidad = clases.count()

    if cantidad == 0:
        messages.error(
            request,
            'No se ha encontrado ninguna clase válida para eliminar.'
        )
        return redirect('clases_profesor')

    clases.delete()

    if cantidad == 1:
        messages.success(
            request,
            'La clase se ha eliminado correctamente.'
        )

    else:
        messages.success(
            request,
            f'Se han eliminado {cantidad} clases correctamente.'
        )

    return redirect('clases_profesor')