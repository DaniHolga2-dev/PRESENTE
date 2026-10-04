from .models import Justificacion, SolicitudSoporte


def notificaciones_profesor(request):

    profesor_id = request.session.get("profesor_id")

    if not profesor_id:

        return {
            "notificaciones_profesor": [],
            "total_notificaciones_profesor": 0,
        }


    justificaciones = (
        Justificacion.objects
        .filter(
            asistencia__clase__grupo__profesor_id=profesor_id,
            estado="pendiente"
        )
        .select_related(
            "asistencia__alumno",
            "asistencia__clase",
            "asistencia__clase__grupo"
        )
        .order_by("-fecha_solicitud")
    )


    solicitudes_soporte = (
        SolicitudSoporte.objects
        .filter(
            clase__grupo__profesor_id=profesor_id,
            estado="pendiente"
        )
        .select_related(
            "alumno",
            "clase",
            "clase__grupo"
        )
        .order_by("-fecha_solicitud")
    )


    notificaciones = []


    for justificacion in justificaciones:

        notificaciones.append({
            "tipo": "justificacion",
            "titulo": "Nueva justificación",
            "alumno": (
                f"{justificacion.asistencia.alumno.nombre} "
                f"{justificacion.asistencia.alumno.apellidos}"
            ),
            "fecha": justificacion.fecha_solicitud,
            "id": justificacion.id,
        })


    for solicitud in solicitudes_soporte:

        notificaciones.append({
            "tipo": "soporte",
            "titulo": "Nueva solicitud de soporte",
            "alumno": (
                f"{solicitud.alumno.nombre} "
                f"{solicitud.alumno.apellidos}"
            ),
            "fecha": solicitud.fecha_solicitud,
            "id": solicitud.id,
        })


    notificaciones.sort(
        key=lambda notificacion: notificacion["fecha"],
        reverse=True
    )


    return {
        "notificaciones_profesor": notificaciones,
        "total_notificaciones_profesor": len(notificaciones),
    }