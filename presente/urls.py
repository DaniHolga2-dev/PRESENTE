from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

from asistencia import views


urlpatterns = [

    # =====================================================
    # GENERAL
    # =====================================================

    path(
        'admin/',
        admin.site.urls
    ),

    path(
        '',
        views.inicio,
        name='inicio'
    ),

    path(
        'login/',
        views.seleccionar_login,
        name='seleccionar_login'
    ),


    # =====================================================
    # PROFESOR
    # =====================================================

    path(
        'profesor/',
        views.login_profesor,
        name='login_profesor'
    ),

    path(
        'profesor/registro/',
        views.registro_profesor,
        name='registro_profesor'
    ),

    path(
        'profesor/panel/',
        views.panel_profesor,
        name='panel_profesor'
    ),

    path(
        'profesor/logout/',
        views.logout_profesor,
        name='logout_profesor'
    ),


    # =====================================================
    # GRUPOS PROFESOR
    # =====================================================

    path(
        'profesor/grupos/nuevo/',
        views.crear_grupo,
        name='crear_grupo'
    ),

    path(
        'profesor/grupos/<int:grupo_id>/',
        views.detalle_grupo,
        name='detalle_grupo'
    ),

    path(
        'profesor/grupos/<int:grupo_id>/color/',
        views.cambiar_color_grupo,
        name='cambiar_color_grupo'
    ),

    path(
        'profesor/grupos/<int:grupo_id>/clases/nueva/',
        views.crear_clase,
        name='crear_clase'
    ),


    # =====================================================
    # CLASES PROFESOR
    # =====================================================

    path(
        'profesor/clases/',
        views.clases_profesor,
        name='clases_profesor'
    ),

    path(
        'profesor/clases/borrar/',
        views.borrar_clases,
        name='borrar_clases'
    ),

    path(
        'profesor/clases/<int:clase_id>/asistencia/',
        views.gestionar_asistencia,
        name='gestionar_asistencia'
    ),

    path(
        'profesor/clases/<int:clase_id>/abrir/',
        views.abrir_asistencia,
        name='abrir_asistencia'
    ),

    path(
        'profesor/clases/<int:clase_id>/cerrar/',
        views.cerrar_asistencia,
        name='cerrar_asistencia'
    ),

    path(
        'profesor/clases/<int:clase_id>/renovar-qr/',
        views.renovar_qr,
        name='renovar_qr'
    ),


    # =====================================================
    # CONTROL DE ASISTENCIA PROFESOR
    # =====================================================

    path(
        'profesor/asistencia/',
        views.control_asistencia,
        name='control_asistencia'
    ),

    path(
        'profesor/asistencia/registros/',
        views.registros_asistencia,
        name='registros_asistencia'
    ),


    # =====================================================
    # NOTIFICACIONES PROFESOR
    # =====================================================

    path(
        'profesor/notificaciones/',
        views.notificaciones_profesor,
        name='notificaciones_profesor'
    ),


    # =====================================================
    # JUSTIFICACIONES PROFESOR
    # =====================================================

    path(
        'profesor/justificaciones/',
        views.justificaciones_profesor,
        name='justificaciones_profesor'
    ),

    path(
        'profesor/justificaciones/<int:justificacion_id>/aprobar/',
        views.aprobar_justificacion,
        name='aprobar_justificacion'
    ),

    path(
        'profesor/justificaciones/<int:justificacion_id>/rechazar/',
        views.rechazar_justificacion,
        name='rechazar_justificacion'
    ),

    path(
        'justificaciones/<int:justificacion_id>/documento/',
        views.ver_documento_justificacion,
        name='ver_documento_justificacion'
    ),


    # =====================================================
    # INFORMES PROFESOR
    # =====================================================

    path(
        'profesor/informes/',
        views.informes_profesor,
        name='informes_profesor'
    ),


    # =====================================================
    # SOPORTE PROFESOR
    # =====================================================

    path(
        'profesor/soporte/',
        views.soporte_profesor,
        name='soporte_profesor'
    ),

    path(
        'profesor/soporte/<int:solicitud_id>/aprobar/',
        views.aprobar_soporte,
        name='aprobar_soporte'
    ),

    path(
        'profesor/soporte/<int:solicitud_id>/rechazar/',
        views.rechazar_soporte,
        name='rechazar_soporte'
    ),


    # =====================================================
    # AJUSTES PROFESOR
    # =====================================================

    path(
        'profesor/ajustes/',
        views.ajustes_profesor,
        name='ajustes_profesor'
    ),


    # =====================================================
    # ALUMNO
    # =====================================================

    path(
        'alumno/',
        views.login_alumno,
        name='login_alumno'
    ),

    path(
        'alumno/registro/',
        views.registro_alumno,
        name='registro_alumno'
    ),

    path(
        'alumno/grupo/',
        views.grupo_alumno,
        name='grupo_alumno'
    ),

    path(
        'alumno/clases/',
        views.clases_alumno,
        name='clases_alumno'
    ),

    path(
        'alumno/asistencia/',
        views.asistencia_alumno,
        name='asistencia_alumno'
    ),


    # =====================================================
    # JUSTIFICACIONES ALUMNO
    # =====================================================

    path(
        'alumno/justificaciones/',
        views.justificaciones_alumno,
        name='justificaciones_alumno'
    ),


    # =====================================================
    # INFORMES ALUMNO
    # =====================================================

    path(
        'alumno/informes/',
        views.informes_alumno,
        name='informes_alumno'
    ),


    # =====================================================
    # AJUSTES ALUMNO
    # =====================================================

    path(
        'alumno/ajustes/',
        views.ajustes_alumno,
        name='ajustes_alumno'
    ),


    # =====================================================
    # LOGOUT ALUMNO
    # =====================================================

    path(
        'alumno/logout/',
        views.logout_alumno,
        name='logout_alumno'
    ),


    # =====================================================
    # QR Y REGISTRO DE ASISTENCIA
    # =====================================================

    path(
        'profesor/clases/<int:clase_id>/qr/',
        views.qr_clase,
        name='qr_clase'
    ),

    path(
        'asistencia/registrar/<uuid:token>/',
        views.registrar_asistencia,
        name='registrar_asistencia'
    ),


    # =====================================================
    # SOPORTE GENERAL / ALUMNO
    # =====================================================

    path(
        'soporte/',
        views.soporte,
        name='soporte'
    ),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )