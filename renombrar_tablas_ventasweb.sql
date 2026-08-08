-- Script para renombrar todas las tablas de escuelaweb_* a ventasweb_*
-- Ejecutar en PostgreSQL

-- Tablas principales de tenant models
ALTER TABLE IF EXISTS escuelaweb_client RENAME TO ventasweb_client;
ALTER TABLE IF EXISTS escuelaweb_domain RENAME TO ventasweb_domain;

-- Tablas de modelos principales
ALTER TABLE IF EXISTS escuelaweb_customuser RENAME TO ventasweb_customuser;
ALTER TABLE IF EXISTS escuelaweb_customuser_groups RENAME TO ventasweb_customuser_groups;
ALTER TABLE IF EXISTS escuelaweb_customuser_user_permissions RENAME TO ventasweb_customuser_user_permissions;
ALTER TABLE IF EXISTS escuelaweb_tutor RENAME TO ventasweb_tutor;
ALTER TABLE IF EXISTS escuelaweb_persona RENAME TO ventasweb_persona;
ALTER TABLE IF EXISTS escuelaweb_anhoescolar RENAME TO ventasweb_anhoescolar;
ALTER TABLE IF EXISTS escuelaweb_mensualidad RENAME TO ventasweb_mensualidad;
ALTER TABLE IF EXISTS escuelaweb_estudiante RENAME TO ventasweb_estudiante;
ALTER TABLE IF EXISTS escuelaweb_profesor RENAME TO ventasweb_profesor;
ALTER TABLE IF EXISTS escuelaweb_curso RENAME TO ventasweb_curso;
ALTER TABLE IF EXISTS escuelaweb_materia RENAME TO ventasweb_materia;
ALTER TABLE IF EXISTS escuelaweb_matricula RENAME TO ventasweb_matricula;
ALTER TABLE IF EXISTS escuelaweb_studentgroup RENAME TO ventasweb_studentgroup;
ALTER TABLE IF EXISTS escuelaweb_asistencia RENAME TO ventasweb_asistencia;
ALTER TABLE IF EXISTS escuelaweb_asistenciapersonal RENAME TO ventasweb_asistenciapersonal;
ALTER TABLE IF EXISTS escuelaweb_conceptopago RENAME TO ventasweb_conceptopago;
ALTER TABLE IF EXISTS escuelaweb_pago RENAME TO ventasweb_pago;
ALTER TABLE IF EXISTS escuelaweb_tarifaestudiante RENAME TO ventasweb_tarifaestudiante;
ALTER TABLE IF EXISTS escuelaweb_factura RENAME TO ventasweb_factura;
ALTER TABLE IF EXISTS escuelaweb_detallefactura RENAME TO ventasweb_detallefactura;
ALTER TABLE IF EXISTS escuelaweb_pagofactura RENAME TO ventasweb_pagofactura;
ALTER TABLE IF EXISTS escuelaweb_codigoanulacion RENAME TO ventasweb_codigoanulacion;
ALTER TABLE IF EXISTS escuelaweb_categoriaarticulo RENAME TO ventasweb_categoriaarticulo;
ALTER TABLE IF EXISTS escuelaweb_articulo RENAME TO ventasweb_articulo;
ALTER TABLE IF EXISTS escuelaweb_inventario RENAME TO ventasweb_inventario;
ALTER TABLE IF EXISTS escuelaweb_movimientoinventario RENAME TO ventasweb_movimientoinventario;
ALTER TABLE IF EXISTS escuelaweb_cuentacontable RENAME TO ventasweb_cuentacontable;
ALTER TABLE IF EXISTS escuelaweb_asientocontable RENAME TO ventasweb_asientocontable;
ALTER TABLE IF EXISTS escuelaweb_detallepago RENAME TO ventasweb_detallepago;
ALTER TABLE IF EXISTS escuelaweb_detallepagoconcepto RENAME TO ventasweb_detallepagoconcepto;
ALTER TABLE IF EXISTS escuelaweb_detallepagofactura RENAME TO ventasweb_detallepagofactura;

-- Tablas de subscripciones
ALTER TABLE IF EXISTS escuelaweb_plansuscripcion RENAME TO ventasweb_plansuscripcion;
ALTER TABLE IF EXISTS escuelaweb_suscripcion RENAME TO ventasweb_suscripcion;
ALTER TABLE IF EXISTS escuelaweb_historialsuscripcion RENAME TO ventasweb_historialsuscripcion;
ALTER TABLE IF EXISTS escuelaweb_pagosuscripcion RENAME TO ventasweb_pagosuscripcion;

-- Tablas de seguridad
ALTER TABLE IF EXISTS escuelaweb_securitylog RENAME TO ventasweb_securitylog;
ALTER TABLE IF EXISTS escuelaweb_ipblacklist RENAME TO ventasweb_ipblacklist;

-- Tablas POS
ALTER TABLE IF EXISTS escuelaweb_transaccionpos RENAME TO ventasweb_transaccionpos;
ALTER TABLE IF EXISTS escuelaweb_terminalestudiante RENAME TO ventasweb_terminalestudiante;

-- Tablas de ventas (si existen)
ALTER TABLE IF EXISTS escuelaweb_clientecorporativo RENAME TO ventasweb_clientecorporativo;
ALTER TABLE IF EXISTS escuelaweb_cotizacion RENAME TO ventasweb_cotizacion;
ALTER TABLE IF EXISTS escuelaweb_detallecotizacion RENAME TO ventasweb_detallecotizacion;
ALTER TABLE IF EXISTS escuelaweb_comisionvendedor RENAME TO ventasweb_comisionvendedor;
ALTER TABLE IF EXISTS escuelaweb_metavendedor RENAME TO ventasweb_metavendedor;

-- Tablas adicionales que puedan existir
ALTER TABLE IF EXISTS escuelaweb_notificacion RENAME TO ventasweb_notificacion;
ALTER TABLE IF EXISTS escuelaweb_configuracionescuela RENAME TO ventasweb_configuracionescuela;
ALTER TABLE IF EXISTS escuelaweb_horario RENAME TO ventasweb_horario;
ALTER TABLE IF EXISTS escuelaweb_aula RENAME TO ventasweb_aula;
ALTER TABLE IF EXISTS escuelaweb_periodo RENAME TO ventasweb_periodo;
ALTER TABLE IF EXISTS escuelaweb_calificacion RENAME TO ventasweb_calificacion;
ALTER TABLE IF EXISTS escuelaweb_tarea RENAME TO ventasweb_tarea;
ALTER TABLE IF EXISTS escuelaweb_entrega RENAME TO ventasweb_entrega;
ALTER TABLE IF EXISTS escuelaweb_comunicado RENAME TO ventasweb_comunicado;
ALTER TABLE IF EXISTS escuelaweb_evento RENAME TO ventasweb_evento;
ALTER TABLE IF EXISTS escuelaweb_documento RENAME TO ventasweb_documento;

-- Renombrar secuencias (sequences)
ALTER SEQUENCE IF EXISTS escuelaweb_client_id_seq RENAME TO ventasweb_client_id_seq;
ALTER SEQUENCE IF EXISTS escuelaweb_domain_id_seq RENAME TO ventasweb_domain_id_seq;
ALTER SEQUENCE IF EXISTS escuelaweb_customuser_id_seq RENAME TO ventasweb_customuser_id_seq;
ALTER SEQUENCE IF EXISTS escuelaweb_tutor_id_seq RENAME TO ventasweb_tutor_id_seq;
ALTER SEQUENCE IF EXISTS escuelaweb_persona_id_seq RENAME TO ventasweb_persona_id_seq;
ALTER SEQUENCE IF EXISTS escuelaweb_anhoescolar_id_seq RENAME TO ventasweb_anhoescolar_id_seq;
ALTER SEQUENCE IF EXISTS escuelaweb_mensualidad_id_seq RENAME TO ventasweb_mensualidad_id_seq;
ALTER SEQUENCE IF EXISTS escuelaweb_estudiante_id_seq RENAME TO ventasweb_estudiante_id_seq;
ALTER SEQUENCE IF EXISTS escuelaweb_profesor_id_seq RENAME TO ventasweb_profesor_id_seq;
ALTER SEQUENCE IF EXISTS escuelaweb_curso_id_seq RENAME TO ventasweb_curso_id_seq;
ALTER SEQUENCE IF EXISTS escuelaweb_materia_id_seq RENAME TO ventasweb_materia_id_seq;
ALTER SEQUENCE IF EXISTS escuelaweb_matricula_id_seq RENAME TO ventasweb_matricula_id_seq;
ALTER SEQUENCE IF EXISTS escuelaweb_studentgroup_id_seq RENAME TO ventasweb_studentgroup_id_seq;
ALTER SEQUENCE IF EXISTS escuelaweb_asistencia_id_seq RENAME TO ventasweb_asistencia_id_seq;
ALTER SEQUENCE IF EXISTS escuelaweb_asistenciapersonal_id_seq RENAME TO ventasweb_asistenciapersonal_id_seq;
ALTER SEQUENCE IF EXISTS escuelaweb_conceptopago_id_seq RENAME TO ventasweb_conceptopago_id_seq;
ALTER SEQUENCE IF EXISTS escuelaweb_pago_id_seq RENAME TO ventasweb_pago_id_seq;
ALTER SEQUENCE IF EXISTS escuelaweb_tarifaestudiante_id_seq RENAME TO ventasweb_tarifaestudiante_id_seq;
ALTER SEQUENCE IF EXISTS escuelaweb_factura_id_seq RENAME TO ventasweb_factura_id_seq;
ALTER SEQUENCE IF EXISTS escuelaweb_detallefactura_id_seq RENAME TO ventasweb_detallefactura_id_seq;
ALTER SEQUENCE IF EXISTS escuelaweb_pagofactura_id_seq RENAME TO ventasweb_pagofactura_id_seq;
ALTER SEQUENCE IF EXISTS escuelaweb_codigoanulacion_id_seq RENAME TO ventasweb_codigoanulacion_id_seq;
ALTER SEQUENCE IF EXISTS escuelaweb_categoriaarticulo_id_seq RENAME TO ventasweb_categoriaarticulo_id_seq;
ALTER SEQUENCE IF EXISTS escuelaweb_articulo_id_seq RENAME TO ventasweb_articulo_id_seq;
ALTER SEQUENCE IF EXISTS escuelaweb_plansuscripcion_id_seq RENAME TO ventasweb_plansuscripcion_id_seq;
ALTER SEQUENCE IF EXISTS escuelaweb_suscripcion_id_seq RENAME TO ventasweb_suscripcion_id_seq;
ALTER SEQUENCE IF EXISTS escuelaweb_securitylog_id_seq RENAME TO ventasweb_securitylog_id_seq;
ALTER SEQUENCE IF EXISTS escuelaweb_transaccionpos_id_seq RENAME TO ventasweb_transaccionpos_id_seq;

-- Actualizar la tabla django_migrations para reflejar el nuevo nombre de app
UPDATE django_migrations SET app = 'ventasweb' WHERE app = 'escuelaweb';

-- Verificar que todo se renombró correctamente
SELECT 'Tablas renombradas exitosamente' AS status;
