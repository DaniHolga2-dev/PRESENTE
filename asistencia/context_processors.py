from .models import Justificacion


def notificaciones_profesor(request):

    profesor_id = request.session.get("profesor_id")

    if not profesor_id:
        return {
            "justificaciones_pendientes": 0
        }

    justificaciones_pendientes = (
        Justificacion.objects
        .filter(
            estado="pendiente",
            asistencia__clase__grupo__profesor_id=profesor_id
        )
        .count()
    )

    return {
        "justificaciones_pendientes": justificaciones_pendientes
    }