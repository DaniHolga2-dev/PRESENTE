# PRESENTE

PRESENTE es una aplicación web que he desarrollado para llevar el control de asistencia de los alumnos en clases presenciales utilizando códigos QR.

La idea es bastante sencilla: el profesor crea sus grupos y las clases correspondientes y, cuando comienza una clase, puede abrir la asistencia y generar un código QR. Los alumnos que están en clase escanean ese código y la aplicación registra su asistencia y la hora a la que han entrado.

El proyecto está desarrollado principalmente con Python y Django.

## ¿Qué puede hacer el profesor?

Desde su cuenta, el profesor puede:

- Crear grupos y asignaturas.
- Añadir alumnos a un grupo.
- Crear las clases que se van a impartir.
- Abrir y cerrar la asistencia de una clase.
- Generar el código QR de cada sesión.
- Consultar la asistencia de los alumnos.
- Ver quién ha asistido, quién ha llegado tarde y quién ha faltado.
- Consultar estadísticas de asistencia.
- Revisar las justificaciones enviadas por los alumnos.
- Aceptar o rechazar una justificación.

## ¿Qué puede hacer el alumno?

El alumno dispone de su propia cuenta y puede:

- Consultar el grupo al que pertenece.
- Ver la información de su asignatura y profesor.
- Consultar sus clases.
- Registrar su asistencia mediante el QR.
- Consultar su historial de asistencia.
- Ver su porcentaje de asistencia, retrasos y faltas.
- Justificar una ausencia y adjuntar la documentación correspondiente.
- Consultar si una justificación ha sido aceptada o rechazada.

## Diseño

La aplicación está preparada para utilizarse tanto desde un ordenador como desde un teléfono móvil.

Esto es especialmente importante para los alumnos, ya que el registro de asistencia mediante QR está pensado principalmente para realizarse desde el móvil.

## Tecnologías utilizadas

Para desarrollar el proyecto he utilizado:

- Python
- Django
- SQLite
- HTML
- CSS
- JavaScript
- QRCode
- Pillow
- Git y GitHub

## Cómo instalar el proyecto

Primero hay que clonar el repositorio:

```bash
git clone https://github.com/DaniHolga2-dev/PRESENTE.git
```

Entramos en la carpeta:

```bash
cd PRESENTE
```

Creamos el entorno virtual:

```bash
python -m venv venv
```

En Windows CMD se puede activar con:

```bash
venv\Scripts\activate
```

Si se utiliza PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

En algunos equipos PowerShell puede bloquear la ejecución del script por la política de seguridad. Si ocurre, se puede habilitar temporalmente para esa terminal con:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Después se vuelve a activar el entorno virtual:

```powershell
.\venv\Scripts\Activate.ps1
```

Una vez activado, instalamos las dependencias:

```bash
pip install -r requirements.txt
```

Después creamos la base de datos ejecutando las migraciones:

```bash
python manage.py migrate
```

## Datos de prueba

Para facilitar la prueba de la aplicación he añadido un comando que crea automáticamente una serie de datos de ejemplo.

De esta forma no es necesario crear manualmente un profesor, alumnos, grupos y clases después de instalar el proyecto.

Para cargar estos datos hay que ejecutar:

```bash
python manage.py cargar_demo
```

El comando crea automáticamente:

- Un profesor.
- Un grupo de Desarrollo de Aplicaciones Web.
- Cuatro alumnos.
- Varias clases.
- Diferentes registros de asistencia.
- Casos de alumnos presentes, con retraso y ausentes.
- Una justificación pendiente de ejemplo.

Esto permite entrar directamente en la aplicación y probar sus principales funciones.

## Credenciales de prueba

Los usuarios que se crean mediante `cargar_demo` son únicamente cuentas ficticias para poder probar la aplicación.

### Profesor

```text
Usuario: admin
Correo: admin@presente.com
Contraseña: 123456bL
```

### Alumnos

**Daniel Holgado González**

```text
Correo: danielholgadogonzalez@hotmail.com
Contraseña: 123456789
```

**Indira Huertas Lucendo**

```text
Correo: indirahuertaslucendo@hotmail.com
Contraseña: 123456789
```

**Sergio Cuéllar Almagro**

```text
Correo: sergiocuellaralmagro@hotmail.com
Contraseña: 123456789
```

**Diego del Toro Mota**

```text
Correo: diegodeltoromota@hotmail.com
Contraseña: 123456789
```

Por último, iniciamos el servidor:

```bash
python manage.py runserver
```

La aplicación estará disponible en:

```text
http://127.0.0.1:8000/
```

## Base de datos

Durante el desarrollo he utilizado SQLite.

El archivo `db.sqlite3` no está incluido en el repositorio, por lo que cada instalación del proyecto comienza con una base de datos nueva.

La estructura de la base de datos se crea automáticamente ejecutando:

```bash
python manage.py migrate
```

Después, si se quieren utilizar los datos de prueba, se pueden generar ejecutando:

```bash
python manage.py cargar_demo
```

## Dependencias

Las librerías necesarias están incluidas en `requirements.txt`.

Actualmente el proyecto utiliza Django, Pillow y QRCode junto con sus dependencias.

## Estructura del proyecto

```text
PRESENTE/
│
├── asistencia/
│   ├── management/
│   │   └── commands/
│   │       └── cargar_demo.py
│   ├── migrations/
│   ├── static/
│   ├── templates/
│   ├── forms.py
│   ├── models.py
│   └── views.py
│
├── presente/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── manage.py
├── requirements.txt
├── .gitignore
└── README.md
```

## Autor

Proyecto desarrollado por **DaniHolga2-dev**.