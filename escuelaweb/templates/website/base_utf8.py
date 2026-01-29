{% load static %}
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Mi Sitio Web{% endblock %}</title>
    
    <link rel="stylesheet" href="{% static 'css/bootstrap.min.css' %}">


    <link rel="stylesheet" href="{% static 'css/style.css' %}">
</head>
<body>
    {% include 'website/header.html' %}
	<style>
        body {

            background-image:
                linear-gradient(rgba(50, 50, 50, 0.5), rgba(50, 50, 50, 0.5)),
                url("/static/img/fondo.jpg");
            background-size: cover;
            background-repeat: no-repeat;
            background-attachment: fixed;
            background-position: center;
            background-size: cover;
            background-blend-mode: darken;
            color: white;
        }
    </style>
    
    
    <main>
        {% block content %}
        <!-- Contenido dinÃ¡mico de cada pÃ¡gina -->
         
        {% endblock %}
    </main>

    {% include 'website/footer.html'%}
    
<script src="{% static 'js/popper.min.js' %}"></script>
<script>
    // Script de cierre por inactividad
    let tiempoInactividad = 5 * 60 * 1000; // 5 minutos
    let temporizador;

    function reiniciarTemporizador() {
      clearTimeout(temporizador);
      temporizador = setTimeout(cerrarSesion, tiempoInactividad);
    }

    function cerrarSesion() {
      alert("Tu sesión ha expirado por inactividad.");
      window.location.href = "/logout/"; // Cambia si tu ruta logout es diferente
    }

    window.onload = reiniciarTemporizador;
    document.onmousemove = reiniciarTemporizador;
    document.onkeypress = reiniciarTemporizador;
  </script>

 	

</body>
</html>
