import base64
import json
import os
import uuid

from datetime import datetime, timedelta
from io import BytesIO

import qrcode

from django.contrib import messages
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import check_password
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
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
# FUNCIONES AUXILIARES QR
# =========================================================

def generar_qr_base64(url):

    qr = qrcode.make(url)

    buffer = BytesIO()

    qr.save(
        buffer,
        format='PNG'
    )

    return base64.b64encode(
        buffer.getvalue()
    ).decode('utf-8')


# =========================================================
# INICIO
# =========================================================

def inicio(request):

    return render(
        request,
        'asistencia/inicio.html'
    )


def seleccionar_login(request):

    return render(
        request,
        'asistencia/login.html'
    )


# =========================================================
# PROFESOR
# =========================================================

def login_profesor(request):

    if request.session.get('profesor_id'):
        return redirect('panel_profesor')

    if request.method == 'POST':

        username = request.POST.get('username')
        password = request.POST.get('password')

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

                request.session['profesor_id'] = profesor.id

                request.session.pop(
                    'alumno_id',
                    None
                )

                return redirect('panel_profesor')

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


def panel_profesor(request):

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

    return render(
        request,
        'asistencia/panel_profesor.html',
        {
            'profesor': profesor,
            'grupos': grupos,
        }
    )


def crear_grupo(request):

    profesor_id = request.session.get('profesor_id')

    if not profesor_id:
        return redirect('seleccionar_login')

    profesor = get_object_or_404(
        Profesor,
        id=profesor_id
    )

    if request.method == 'POST':

        nombre = request.POST.get('nombre')
        asignatura = request.POST.get('asignatura')

        if nombre and asignatura:

            Grupo.objects.create(
                nombre=nombre,
                asignatura=asignatura,
                profesor=profesor
            )

            return redirect('panel_profesor')

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


def detalle_grupo(request, grupo_id):

    profesor_id = request.session.get('profesor_id')

    if not profesor_id:
        return redirect('seleccionar_login')

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


def crear_clase(request, grupo_id):

    profesor_id = request.session.get('profesor_id')

    if not profesor_id:
        return redirect('seleccionar_login')

    grupo = get_object_or_404(
        Grupo,
        id=grupo_id,
        profesor_id=profesor_id
    )

    if request.method == 'POST':

        fecha = request.POST.get('fecha')
        hora_inicio = request.POST.get('hora_inicio')

        if fecha and hora_inicio:

            Clase.objects.create(
                grupo=grupo,
                fecha=fecha,
                hora_inicio=hora_inicio
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
# PROFESOR - ASISTENCIA DE UNA CLASE
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

    asistencias = Asistencia.objects.filter(
        clase=clase
    ).select_related(
        'alumno'
    )

    asistencias_por_alumno = {
        asistencia.alumno_id: asistencia
        for asistencia in asistencias
    }

    registros = []

    for alumno in alumnos:

        asistencia = asistencias_por_alumno.get(
            alumno.id
        )

        if asistencia:

            registros.append({
                'alumno': alumno,
                'estado': asistencia.estado,
                'hora_registro': asistencia.hora_registro,
            })

        else:

            registros.append({
                'alumno': alumno,
                'estado': 'pendiente',
                'hora_registro': None,
            })

    total_alumnos = len(registros)

    total_presentes = sum(
        1
        for registro in registros
        if registro['estado'] == 'presente'
    )

    total_tardes = sum(
        1
        for registro in registros
        if registro['estado'] == 'tarde'
    )

    total_ausentes = sum(
        1
        for registro in registros
        if registro['estado'] == 'ausente'
    )

    total_pendientes = sum(
        1
        for registro in registros
        if registro['estado'] == 'pendiente'
    )

    qr_base64 = None
    url_qr = None

    if clase.asistencia_abierta:

        if not clase.token_qr_generado_en:

            clase.token_qr = uuid.uuid4()
            clase.token_qr_generado_en = timezone.now()

            clase.save(
                update_fields=[
                    'token_qr',
                    'token_qr_generado_en'
                ]
            )

        url_qr = request.build_absolute_uri(
            f'/asistencia/registrar/{clase.token_qr}/'
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


def abrir_asistencia(request, clase_id):

    profesor_id = request.session.get('profesor_id')

    if not profesor_id:
        return redirect('seleccionar_login')

    clase = get_object_or_404(
        Clase,
        id=clase_id,
        grupo__profesor_id=profesor_id
    )

    clase.token_qr = uuid.uuid4()
    clase.token_qr_generado_en = timezone.now()
    clase.asistencia_abierta = True

    clase.save()

    return redirect(
        'gestionar_asistencia',
        clase_id=clase.id
    )


def renovar_qr(request, clase_id):

    profesor_id = request.session.get('profesor_id')

    if not profesor_id:

        return JsonResponse(
            {
                'ok': False,
                'cerrada': True
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
                'cerrada': True
            }
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
        f'/asistencia/registrar/{clase.token_qr}/'
    )

    qr_base64 = generar_qr_base64(
        url_qr
    )

    return JsonResponse(
        {
            'ok': True,
            'qr_base64': qr_base64,
            'url_qr': url_qr
        }
    )


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

    return redirect(
        'gestionar_asistencia',
        clase_id=clase.id
    )


# =========================================================
# PROFESOR - CONTROL GENERAL DE ASISTENCIA
# =========================================================

def control_asistencia(request):

    profesor_id = request.session.get(
        'profesor_id'
    )

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

    total_alumnos_global = 0
    total_registros_global = 0
    total_presentes_global = 0
    total_tardes_global = 0
    total_ausentes_global = 0

    for grupo in grupos:

        alumnos = Alumno.objects.filter(
            grupo=grupo
        )

        total_alumnos_global += alumnos.count()

        asistencias = Asistencia.objects.filter(
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

        total_presentes_global += presentes
        total_tardes_global += tardes
        total_ausentes_global += ausentes

        total_registros_global += (
            presentes +
            tardes +
            ausentes
        )

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


    # =====================================================
    # JUSTIFICACIONES PENDIENTES
    # =====================================================

    justificaciones_pendientes = (
        Justificacion.objects.filter(
            asistencia__clase__grupo__profesor=profesor,
            estado='pendiente'
        ).count()
    )


    # =====================================================
    # ÚLTIMOS REGISTROS
    # =====================================================

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


    # =====================================================
    # PRÓXIMAS CLASES
    # =====================================================

    hoy = timezone.localdate()
    ahora = timezone.localtime()

    proximas_clases_query = (
        Clase.objects.filter(
            grupo__profesor=profesor,
            fecha__gte=hoy
        )
        .select_related(
            'grupo'
        )
        .order_by(
            'fecha',
            'hora_inicio'
        )
    )

    proximas_clases = []

    for clase in proximas_clases_query:

        if (
            clase.fecha == hoy and
            clase.hora_inicio < ahora.time()
        ):
            continue

        proximas_clases.append(
            clase
        )

        if len(proximas_clases) == 3:
            break


    # =====================================================
    # CLASES DE HOY
    # =====================================================

    clases_hoy = (
        Clase.objects.filter(
            grupo__profesor=profesor,
            fecha=hoy
        )
        .select_related(
            'grupo'
        )
        .order_by(
            'hora_inicio'
        )
    )


    # =====================================================
    # QR DE LAS CLASES QUE YA ESTÉN ABIERTAS
    # =====================================================

    clases_hoy_datos = []

    for clase in clases_hoy:

        qr_base64 = None

        if clase.asistencia_abierta:

            if not clase.token_qr_generado_en:

                clase.token_qr = uuid.uuid4()
                clase.token_qr_generado_en = timezone.now()

                clase.save(
                    update_fields=[
                        'token_qr',
                        'token_qr_generado_en'
                    ]
                )

            url_qr = request.build_absolute_uri(
                f'/asistencia/registrar/{clase.token_qr}/'
            )

            qr_base64 = generar_qr_base64(
                url_qr
            )

        clases_hoy_datos.append({
            'clase': clase,
            'qr_base64': qr_base64,
        })


    # =====================================================
    # RENDER
    # =====================================================

    return render(
        request,
        'asistencia/control_asistencia.html',
        {
            'profesor': profesor,

            'total_grupos':
                grupos.count(),

            'total_alumnos':
                total_alumnos_global,

            'total_presentes':
                total_presentes_global,

            'total_tardes':
                total_tardes_global,

            'total_ausentes':
                total_ausentes_global,

            'total_registros':
                total_registros_global,

            'porcentaje_global':
                porcentaje_global,

            'justificaciones_pendientes':
                justificaciones_pendientes,

            'ultimos_registros':
                ultimos_registros,

            'proximas_clases':
                proximas_clases,

            'clases_hoy':
                clases_hoy_datos,
        }
    )


# =========================================================
# PROFESOR - TODOS LOS REGISTROS DE ASISTENCIA
# =========================================================

def registros_asistencia(request):

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
# PROFESOR - SOPORTE
# =========================================================

def soporte_profesor(request):

    profesor_id = request.session.get('profesor_id')

    if not profesor_id:
        return redirect('seleccionar_login')

    solicitudes = SolicitudSoporte.objects.filter(
        clase__grupo__profesor_id=profesor_id
    ).select_related(
        'alumno',
        'clase',
        'clase__grupo'
    ).order_by(
        '-fecha_solicitud'
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

    asistencia, creada = Asistencia.objects.get_or_create(
        alumno=solicitud.alumno,
        clase=solicitud.clase,
        defaults={
            'estado': 'presente'
        }
    )

    if not creada:

        asistencia.estado = 'presente'
        asistencia.save()

    solicitud.estado = 'aprobada'
    solicitud.save()

    messages.success(
        request,
        'La asistencia ha sido confirmada.'
    )

    return redirect('soporte_profesor')


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
    solicitud.save()

    messages.success(
        request,
        'La solicitud ha sido rechazada.'
    )

    return redirect('soporte_profesor')


# =========================================================
# PROFESOR - JUSTIFICACIONES
# =========================================================

def justificaciones_profesor(request):

    profesor_id = request.session.get('profesor_id')

    if not profesor_id:
        return redirect('seleccionar_login')

    justificaciones = Justificacion.objects.filter(
        asistencia__clase__grupo__profesor_id=profesor_id
    ).select_related(
        'asistencia',
        'asistencia__alumno',
        'asistencia__clase',
        'asistencia__clase__grupo'
    ).order_by(
        '-fecha_solicitud'
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


def aprobar_justificacion(request, justificacion_id):

    profesor_id = request.session.get('profesor_id')

    if not profesor_id:
        return redirect('seleccionar_login')

    justificacion = get_object_or_404(
        Justificacion,
        id=justificacion_id,
        asistencia__clase__grupo__profesor_id=profesor_id
    )

    justificacion.estado = 'aprobada'
    justificacion.save()

    messages.success(
        request,
        'La justificación ha sido aprobada.'
    )

    return redirect(
        'justificaciones_profesor'
    )


def rechazar_justificacion(request, justificacion_id):

    profesor_id = request.session.get('profesor_id')

    if not profesor_id:
        return redirect('seleccionar_login')

    justificacion = get_object_or_404(
        Justificacion,
        id=justificacion_id,
        asistencia__clase__grupo__profesor_id=profesor_id
    )

    justificacion.estado = 'rechazada'
    justificacion.save()

    messages.success(
        request,
        'La justificación ha sido rechazada.'
    )

    return redirect(
        'justificaciones_profesor'
    )


def ver_documento_justificacion(
    request,
    justificacion_id
):

    justificacion = get_object_or_404(
        Justificacion,
        id=justificacion_id
    )

    autorizado = False

    alumno_id = request.session.get(
        'alumno_id'
    )

    profesor_id = request.session.get(
        'profesor_id'
    )

    if (
        alumno_id and
        justificacion.asistencia.alumno_id == alumno_id
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


def logout_profesor(request):

    request.session.pop(
        'profesor_id',
        None
    )

    return redirect('inicio')


# =========================================================
# ALUMNO
# =========================================================

def login_alumno(request):

    if request.session.get('alumno_id'):
        return redirect('panel_alumno')

    if request.method == 'POST':

        email = request.POST.get('email')
        password = request.POST.get('password')

        try:

            alumno = Alumno.objects.get(
                email=email
            )

            if check_password(
                password,
                alumno.password
            ):

                request.session['alumno_id'] = alumno.id

                request.session.pop(
                    'profesor_id',
                    None
                )

                return redirect('panel_alumno')

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


def registro_alumno(request):

    if request.session.get('alumno_id'):
        return redirect('panel_alumno')

    if request.method == 'POST':

        form = RegistroAlumnoForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            alumno = form.save()

            request.session['alumno_id'] = alumno.id

            request.session.pop(
                'profesor_id',
                None
            )

            return redirect('panel_alumno')

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
# CLASES - PROFESOR Y ALUMNO
# =========================================================

def clases_profesor(request):

    profesor_id = request.session.get(
        'profesor_id'
    )

    if not profesor_id:
        return redirect('seleccionar_login')

    profesor = get_object_or_404(
        Profesor,
        id=profesor_id
    )

    clases = Clase.objects.filter(
        grupo__profesor=profesor
    ).select_related(
        'grupo'
    ).order_by(
        '-fecha',
        '-hora_inicio'
    )

    return render(
        request,
        'asistencia/clases_profesor.html',
        {
            'profesor': profesor,
            'clases': clases,
        }
    )


def clases_alumno(request):

    alumno_id = request.session.get(
        'alumno_id'
    )

    if not alumno_id:
        return redirect('seleccionar_login')

    alumno = get_object_or_404(
        Alumno,
        id=alumno_id
    )

    clases = Clase.objects.filter(
        grupo=alumno.grupo
    ).order_by(
        '-fecha',
        '-hora_inicio'
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
            'estado': estado,
            'estado_texto': estado_texto,
        })

    return render(
        request,
        'asistencia/clases_alumno.html',
        {
            'alumno': alumno,

            'clases_con_estado':
                clases_con_estado,
        }
    )
# =========================================================
# FICHAJE QR
# =========================================================

def registrar_asistencia(request, token):

    alumno_id = request.session.get(
        'alumno_id'
    )

    if not alumno_id:

        messages.error(
            request,
            'Debes iniciar sesión como alumno para registrar la asistencia.'
        )

        return redirect('login_alumno')

    alumno = get_object_or_404(
        Alumno,
        id=alumno_id
    )

    clase = Clase.objects.filter(
        token_qr=token
    ).first()

    if not clase:

        messages.error(
            request,
            'Este código QR ha caducado.'
        )

        return redirect('panel_alumno')

    if alumno.grupo_id != clase.grupo_id:

        messages.error(
            request,
            'Este código QR no pertenece a tu grupo.'
        )

        return redirect('panel_alumno')

    if not clase.asistencia_abierta:

        messages.error(
            request,
            'La asistencia de esta clase está cerrada.'
        )

        return redirect('panel_alumno')

    if not clase.token_qr_generado_en:

        messages.error(
            request,
            'Este código QR ha caducado.'
        )

        return redirect('panel_alumno')

    tiempo_transcurrido = (
        timezone.now() -
        clase.token_qr_generado_en
    ).total_seconds()

    if tiempo_transcurrido > 10:

        messages.error(
            request,
            'Este código QR ha caducado. Escanea el código actual.'
        )

        return redirect('panel_alumno')

    asistencia_existente = (
        Asistencia.objects.filter(
            alumno=alumno,
            clase=clase
        ).first()
    )

    if asistencia_existente:

        messages.info(
            request,
            'Tu asistencia ya estaba registrada.'
        )

        return redirect('panel_alumno')

    ahora = timezone.localtime()

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

    if ahora < limite_presente:

        estado = 'presente'

    else:

        estado = 'tarde'

    Asistencia.objects.create(
        alumno=alumno,
        clase=clase,
        estado=estado,
        hora_registro=ahora.time()
    )

    messages.success(
        request,
        'Asistencia registrada correctamente.'
    )

    return redirect('panel_alumno')


# =========================================================
# SOPORTE ALUMNO
# =========================================================

def soporte(request):

    clases = Clase.objects.select_related(
        'grupo'
    ).order_by(
        '-fecha',
        '-hora_inicio'
    )

    if request.method == 'POST':

        email = request.POST.get('email')
        clase_id = request.POST.get('clase')
        motivo = request.POST.get('motivo')

        if not email or not clase_id or not motivo:

            messages.error(
                request,
                'Completa todos los campos.'
            )

        else:

            alumno = Alumno.objects.filter(
                email__iexact=email
            ).first()

            if not alumno:

                messages.error(
                    request,
                    'No existe ningún alumno registrado con ese correo.'
                )

            else:

                clase = Clase.objects.filter(
                    id=clase_id,
                    grupo=alumno.grupo
                ).first()

                if not clase:

                    messages.error(
                        request,
                        'La clase seleccionada no pertenece a tu grupo.'
                    )

                else:

                    existe = (
                        SolicitudSoporte.objects.filter(
                            alumno=alumno,
                            clase=clase,
                            estado='pendiente'
                        ).exists()
                    )

                    if existe:

                        messages.error(
                            request,
                            'Ya tienes una solicitud pendiente para esta clase.'
                        )

                    else:

                        SolicitudSoporte.objects.create(
                            alumno=alumno,
                            clase=clase,
                            motivo=motivo
                        )

                        messages.success(
                            request,
                            'La solicitud ha sido enviada al profesor.'
                        )

                        return redirect('soporte')

    return render(
        request,
        'asistencia/soporte.html',
        {
            'clases': clases
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
        return redirect('seleccionar_login')

    alumno = get_object_or_404(
        Alumno,
        id=alumno_id
    )

    ausencias_disponibles = (
        Asistencia.objects.filter(
            alumno=alumno,
            estado='ausente',
            justificacion__isnull=True
        ).select_related(
            'clase',
            'clase__grupo'
        ).order_by(
            '-clase__fecha'
        )
    )

    justificaciones = (
        Justificacion.objects.filter(
            asistencia__alumno=alumno
        ).select_related(
            'asistencia',
            'asistencia__clase',
            'asistencia__clase__grupo'
        ).order_by(
            '-fecha_solicitud'
        )
    )

    if request.method == 'POST':

        asistencia_id = request.POST.get(
            'asistencia'
        )

        motivo = request.POST.get(
            'motivo'
        )

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
            documento and
            not documento.content_type.startswith(
                'image/'
            )
        ):

            messages.error(
                request,
                'El justificante debe ser una imagen.'
            )

        elif (
            documento and
            documento.size > 5 * 1024 * 1024
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

            'ausencias_disponibles':
                ausencias_disponibles,

            'justificaciones':
                justificaciones,
        }
    )


# =========================================================
# PANEL ALUMNO
# =========================================================

def panel_alumno(request):

    alumno_id = request.session.get(
        'alumno_id'
    )

    if not alumno_id:
        return redirect('seleccionar_login')

    alumno = get_object_or_404(
        Alumno,
        id=alumno_id
    )

    asistencias = (
        Asistencia.objects.filter(
            alumno=alumno
        ).select_related(
            'clase',
            'clase__grupo'
        ).order_by(
            '-clase__fecha',
            '-clase__hora_inicio'
        )
    )

    presentes = asistencias.filter(
        estado='presente'
    )

    tardes = asistencias.filter(
        estado='tarde'
    )

    ausencias = asistencias.filter(
        estado='ausente'
    )

    justificaciones_pendientes = (
        Justificacion.objects.filter(
            asistencia__alumno=alumno,
            estado='pendiente'
        ).select_related(
            'asistencia',
            'asistencia__clase'
        ).order_by(
            '-asistencia__clase__fecha'
        )
    )

    total_registros = asistencias.count()

    total_presentes = presentes.count()

    total_tardes = tardes.count()

    total_ausencias = ausencias.count()

    total_asistencias = (
        total_presentes +
        total_tardes
    )

    if total_registros > 0:

        porcentaje_asistencia = round(
            (
                total_asistencias /
                total_registros
            ) * 100,
            1
        )

    else:

        porcentaje_asistencia = 0


    # =====================================================
    # GRÁFICO DE EVOLUCIÓN DE ASISTENCIA
    # =====================================================

    asistencias_cronologicas = (
        Asistencia.objects.filter(
            alumno=alumno
        ).select_related(
            'clase'
        ).order_by(
            'clase__fecha',
            'clase__hora_inicio'
        )
    )

    grafico_fechas = []
    grafico_porcentajes = []

    clases_acumuladas = 0
    asistencias_acumuladas = 0

    for asistencia in asistencias_cronologicas:

        clases_acumuladas += 1

        if asistencia.estado in [
            'presente',
            'tarde'
        ]:

            asistencias_acumuladas += 1

        porcentaje_acumulado = round(
            (
                asistencias_acumuladas /
                clases_acumuladas
            ) * 100,
            1
        )

        grafico_fechas.append(
            asistencia.clase.fecha.strftime(
                '%d/%m'
            )
        )

        grafico_porcentajes.append(
            porcentaje_acumulado
        )


    # Convertimos los datos a JSON para que posteriormente
    # JavaScript pueda utilizarlos directamente en el gráfico.

    grafico_fechas_json = json.dumps(
        grafico_fechas
    )

    grafico_porcentajes_json = json.dumps(
        grafico_porcentajes
    )


    return render(
        request,
        'asistencia/panel_alumno.html',
        {
            'alumno': alumno,
            'asistencias': asistencias,
            'presentes': presentes,
            'tardes': tardes,
            'ausencias': ausencias,

            'justificaciones_pendientes':
                justificaciones_pendientes,

            'total_registros':
                total_registros,

            'total_presentes':
                total_presentes,

            'total_tardes':
                total_tardes,

            'total_ausencias':
                total_ausencias,

            'porcentaje_asistencia':
                porcentaje_asistencia,

            # DATOS DEL GRÁFICO

            'grafico_fechas':
                grafico_fechas_json,

            'grafico_porcentajes':
                grafico_porcentajes_json,
        }
    )


# =========================================================
# ALUMNO - MI GRUPO
# =========================================================

def grupo_alumno(request):

    alumno_id = request.session.get(
        'alumno_id'
    )

    if not alumno_id:
        return redirect('seleccionar_login')

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

        return redirect('panel_alumno')

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


def logout_alumno(request):

    request.session.pop(
        'alumno_id',
        None
    )

    return redirect('inicio')