-- --------------------------------------------------------
-- Host:                         127.0.0.1
-- Versión del servidor:         8.0.30 - MySQL Community Server - GPL
-- SO del servidor:              Win64
-- HeidiSQL Versión:             12.1.0.6537
-- --------------------------------------------------------

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET NAMES utf8 */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;


-- Volcando estructura de base de datos para crud_python
CREATE DATABASE IF NOT EXISTS `crud_python` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;
USE `crud_python`;

-- Volcando estructura para tabla crud_python.tbl_tipo_documento
CREATE TABLE `tbl_tipo_documento` (
  `id_tipo_documento` int NOT NULL AUTO_INCREMENT,
  `td_abreviacion` varchar(45) NOT NULL,
  `tipo_documento` varchar(45) NOT NULL,
  `fecha_registro` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `fecha_borrado` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id_tipo_documento`),
  UNIQUE KEY `unique_td_abreviacion` (`td_abreviacion`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Volcando estructura para tabla crud_python.tbl_tipo_empleado
CREATE TABLE `tbl_tipo_empleado` (
  `id_tipo_empleado` int NOT NULL AUTO_INCREMENT,
  `tipo_empleado` varchar(45) NOT NULL,
  `fecha_registro` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `fecha_borrado` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id_tipo_empleado`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Volcando estructura para tabla crud_python.tbl_empleados
CREATE TABLE `tbl_empleados` (
  `documento` varchar(50) NOT NULL,
  `id_empleado` int NOT NULL AUTO_INCREMENT,
  `id_empresa` int NOT NULL,
  `nombre_empleado` varchar(50) DEFAULT NULL,
  `apellido_empleado` varchar(50) DEFAULT NULL,
  `id_tipo_empleado` int DEFAULT NULL,
  `telefono_empleado` varchar(50) DEFAULT NULL,
  `email_empleado` varchar(50) DEFAULT NULL,
  `cargo` varchar(50) DEFAULT NULL,
  `foto_empleado` mediumtext,
  `fecha_registro` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `fecha_borrado` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id_empleado`),
  UNIQUE KEY `uq_empleado_documento` (`documento`),
  UNIQUE KEY `uq_empleado_email` (`email_empleado`),
  KEY `fk_empleado_empresa` (`id_empresa`),
  KEY `fk_empleado_tipo` (`id_tipo_empleado`),
  CONSTRAINT `fk_empleado_empresa` FOREIGN KEY (`id_empresa`) REFERENCES `tbl_empresas` (`id_empresa`),
  CONSTRAINT `fk_empleado_tipo` FOREIGN KEY (`id_tipo_empleado`) REFERENCES `tbl_tipo_empleado` (`id_tipo_empleado`)
) ENGINE=InnoDB AUTO_INCREMENT=313 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Volcando estructura para tabla crud_python.users
CREATE TABLE `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name_surname` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `email_user` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `pass_user` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `rol` varchar(45) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `created_user` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `fecha_borrado` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_email_user` (`email_user`)
) ENGINE=InnoDB AUTO_INCREMENT=53 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Volcando estructura para tabla crud_python.tbl_actividades
CREATE TABLE `tbl_actividades` (
  `id_actividad` int NOT NULL AUTO_INCREMENT,
  `codigo_actividad` varchar(50) NOT NULL,
  `nombre_actividad` varchar(50) DEFAULT NULL,
  `descripcion_actividad` varchar(200) DEFAULT NULL,
  `id_proceso` int NOT NULL,
  `fecha_registro` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `fecha_borrado` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id_actividad`),
  UNIQUE KEY `codigo_actividad_UNIQUE` (`codigo_actividad`),
  KEY `fk_actividad_proceso` (`id_proceso`),
  CONSTRAINT `fk_actividad_proceso` FOREIGN KEY (`id_proceso`) REFERENCES `tbl_procesos` (`id_proceso`)
) ENGINE=InnoDB AUTO_INCREMENT=0 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Volcando estructura para tabla crud_python.tbl_clientes
CREATE TABLE `tbl_clientes` (
  `id_cliente` int NOT NULL AUTO_INCREMENT,
  `id_tipo_documento` int DEFAULT NULL,
  `documento` varchar(50) NOT NULL,
  `nombre_cliente` varchar(50) DEFAULT NULL,
  `telefono_cliente` varchar(50) DEFAULT NULL,
  `email_cliente` varchar(50) DEFAULT NULL,
  `foto_cliente` mediumtext,
  `fecha_registro` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `fecha_borrado` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id_cliente`),
  UNIQUE KEY `uq_cliente_documento` (`documento`),
  KEY `idx_nombre_cliente` (`nombre_cliente`),
  KEY `idx_fecha_registro` (`fecha_registro`),
  KEY `fk_cliente_tipodoc` (`id_tipo_documento`),
  CONSTRAINT `fk_cliente_tipodoc` FOREIGN KEY (`id_tipo_documento`) REFERENCES `tbl_tipo_documento` (`id_tipo_documento`)
) ENGINE=InnoDB AUTO_INCREMENT=187 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Volcando estructura para tabla crud_python.tbl_jornadas
CREATE TABLE `tbl_jornadas` (
  `id_jornada` int NOT NULL AUTO_INCREMENT,
  `id_empleado` int NOT NULL,
  `nombre_empleado` varchar(50) DEFAULT NULL,
  `novedad_jornada_programada` varchar(200) DEFAULT NULL,
  `novedad_jornada` varchar(50) DEFAULT NULL,
  `fecha_hora_llegada_programada` datetime NOT NULL,
  `fecha_hora_salida_programada` datetime NOT NULL,
  `fecha_hora_llegada` datetime NOT NULL,
  `fecha_hora_salida` datetime NOT NULL,
  `fecha_registro` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `id_usuario_registro` int DEFAULT NULL,
  `usuario_registro` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id_jornada`),
  KEY `fk_jornada_empleado` (`id_empleado`),
  KEY `fk_jornada_users` (`id_usuario_registro`),
  CONSTRAINT `fk_jornada_empleado` FOREIGN KEY (`id_empleado`) REFERENCES `tbl_empleados` (`id_empleado`),
  CONSTRAINT `fk_jornada_users` FOREIGN KEY (`id_usuario_registro`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=22 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Volcando estructura para tabla crud_python.tbl_operaciones
CREATE TABLE `tbl_operaciones` (
  `id_operacion` int NOT NULL AUTO_INCREMENT,
  `id_empleado` int NOT NULL,
  `nombre_empleado` varchar(50) DEFAULT NULL,
  `id_proceso` int DEFAULT NULL,
  `id_actividad` int DEFAULT NULL,
  `proceso` varchar(50) DEFAULT NULL,
  `actividad` varchar(50) DEFAULT NULL,
  `codigo_op` int DEFAULT NULL,
  `id_op` int DEFAULT NULL,
  `cantidad` int DEFAULT NULL,
  `pieza_realizada` varchar(100) DEFAULT NULL,
  `novedad` mediumtext,
  `fecha_hora_inicio` datetime NOT NULL,
  `fecha_hora_fin` datetime NOT NULL,
  `fecha_registro` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `id_usuario_registro` int DEFAULT NULL,
  `usuario_registro` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id_operacion`),
  KEY `idx_id_empleado` (`id_empleado`),
  KEY `idx_fecha_registro` (`fecha_registro`),
  KEY `idx_id_operacion` (`id_operacion`),
  KEY `fk_operacion_proceso` (`id_proceso`),
  KEY `fk_operacion_orden` (`id_op`),
  KEY `fk_operacion_users` (`id_usuario_registro`),
  CONSTRAINT `fk_operacion_empleado` FOREIGN KEY (`id_empleado`) REFERENCES `tbl_empleados` (`id_empleado`),
  CONSTRAINT `fk_operacion_orden` FOREIGN KEY (`id_op`) REFERENCES `tbl_ordenproduccion` (`id_op`),
  CONSTRAINT `fk_operacion_proceso` FOREIGN KEY (`id_proceso`) REFERENCES `tbl_procesos` (`id_proceso`),
  CONSTRAINT `fk_operacion_users` FOREIGN KEY (`id_usuario_registro`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=129758 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Volcando estructura para tabla crud_python.tbl_ordenproduccion
CREATE TABLE `tbl_ordenproduccion` (
  `id_op` int NOT NULL AUTO_INCREMENT,
  `codigo_op` int NOT NULL,
  `id_cliente` int DEFAULT NULL,
  `nombre_cliente` varchar(50) DEFAULT NULL,
  `producto` varchar(200) DEFAULT NULL,
  `version` varchar(50) DEFAULT NULL,
  `cotizacion` varchar(50) DEFAULT NULL,
  `estado` varchar(50) DEFAULT NULL,
  `cantidad` int DEFAULT NULL,
  `medida` varchar(50) DEFAULT NULL,
  `referencia` varchar(100) DEFAULT NULL,
  `odi` varchar(50) DEFAULT NULL,
  `id_empleado` int DEFAULT NULL,
  `empleado` varchar(50) DEFAULT NULL,
  `id_supervisor` int DEFAULT NULL,
  `fecha` date DEFAULT NULL,
  `fecha_entrega` date DEFAULT NULL,
  `descripcion_general` text,
  `empaque` varchar(100) DEFAULT NULL,
  `materiales` text,
  `fecha_registro` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `id_usuario_registro` int DEFAULT NULL,
  `usuario_registro` varchar(50) DEFAULT NULL,
  `fecha_borrado` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id_op`),
  UNIQUE KEY `idx_codigo_op` (`codigo_op`),
  KEY `fk_orden_cliente` (`id_cliente`),
  KEY `fk_orden_empleado_reg` (`id_empleado`),
  KEY `fk_orden_supervisor` (`id_supervisor`),
  CONSTRAINT `fk_orden_cliente` FOREIGN KEY (`id_cliente`) REFERENCES `tbl_clientes` (`id_cliente`),
  CONSTRAINT `fk_orden_empleado_reg` FOREIGN KEY (`id_empleado`) REFERENCES `tbl_empleados` (`id_empleado`),
  CONSTRAINT `fk_orden_supervisor` FOREIGN KEY (`id_supervisor`) REFERENCES `tbl_empleados` (`id_empleado`)
) ENGINE=InnoDB AUTO_INCREMENT=10298 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Volcando estructura para tabla crud_python.tbl_procesos
CREATE TABLE `tbl_procesos` (
  `id_proceso` int NOT NULL AUTO_INCREMENT,
  `codigo_proceso` varchar(50) NOT NULL,
  `nombre_proceso` varchar(50) DEFAULT NULL,
  `descripcion_proceso` varchar(200) DEFAULT NULL,
  `fecha_registro` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `fecha_borrado` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id_proceso`),
  UNIQUE KEY `codigo_proceso_UNIQUE` (`codigo_proceso`)
) ENGINE=InnoDB AUTO_INCREMENT=18 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Volcando estructura para tabla crud_python.tbl_documentos_op
CREATE TABLE `tbl_documentos_op` (
  `id_documento` int NOT NULL AUTO_INCREMENT,
  `id_op` int NOT NULL,
  `documento_path` varchar(255) NOT NULL,
  `documento_nombre_original` varchar(255) NOT NULL,
  `fecha_registro` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `fecha_borrado` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id_documento`),
  KEY `fk_documento_op` (`id_op`),
  CONSTRAINT `fk_documento_op` FOREIGN KEY (`id_op`) REFERENCES `tbl_ordenproduccion` (`id_op`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=20 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Volcando estructura para tabla crud_python.tbl_orden_piezas
CREATE TABLE `tbl_orden_piezas` (
  `id_orden_pieza` int NOT NULL AUTO_INCREMENT,
  `id_op` int NOT NULL,
  `id_pieza` int NOT NULL,
  `cantidad` int DEFAULT NULL,
  `tamano` varchar(100) DEFAULT NULL,
  `montaje` varchar(100) DEFAULT NULL,
  `montaje_tamano` varchar(100) DEFAULT NULL,
  `material` varchar(100) DEFAULT NULL,
  `cantidad_material` text,
  `otros_procesos` varchar(100) DEFAULT NULL,
  `descripcion_general` text,
  `fecha_registro` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `fecha_borrado` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id_orden_pieza`),
  KEY `fk_orden_pieza_op` (`id_op`),
  KEY `fk_orden_pieza_pieza` (`id_pieza`),
  CONSTRAINT `fk_orden_pieza_op` FOREIGN KEY (`id_op`) REFERENCES `tbl_ordenproduccion` (`id_op`) ON DELETE CASCADE,
  CONSTRAINT `fk_orden_pieza_pieza` FOREIGN KEY (`id_pieza`) REFERENCES `tbl_piezas` (`id_pieza`)
) ENGINE=InnoDB AUTO_INCREMENT=16 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Volcando estructura para tabla crud_python.tbl_orden_piezas_procesos
CREATE TABLE `tbl_orden_piezas_procesos` (
  `id_orden_pieza_proceso` int NOT NULL AUTO_INCREMENT,
  `id_orden_pieza` int NOT NULL,
  `id_proceso` int NOT NULL,
  `fecha_registro` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `fecha_borrado` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id_orden_pieza_proceso`),
  KEY `fk_orden_pieza_proceso_op` (`id_orden_pieza`),
  KEY `fk_orden_pieza_proceso_proceso` (`id_proceso`),
  CONSTRAINT `fk_orden_pieza_proceso_op` FOREIGN KEY (`id_orden_pieza`) REFERENCES `tbl_orden_piezas` (`id_orden_pieza`) ON DELETE CASCADE,
  CONSTRAINT `fk_orden_pieza_proceso_proceso` FOREIGN KEY (`id_proceso`) REFERENCES `tbl_procesos` (`id_proceso`)
) ENGINE=InnoDB AUTO_INCREMENT=50 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Volcando estructura para tabla crud_python.tbl_piezas
CREATE TABLE `tbl_piezas` (
  `id_pieza` int NOT NULL AUTO_INCREMENT,
  `nombre_pieza` varchar(50) DEFAULT NULL,
  `descripcion_pieza` varchar(200) DEFAULT NULL,
  `fecha_registro` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `fecha_borrado` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id_pieza`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Volcando estructura para tabla crud_python.tbl_renders_op
CREATE TABLE `tbl_renders_op` (
  `id_render` int NOT NULL AUTO_INCREMENT,
  `id_op` int NOT NULL,
  `render_path` varchar(255) NOT NULL,
  `fecha_registro` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `fecha_borrado` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id_render`),
  KEY `fk_render_op` (`id_op`),
  CONSTRAINT `fk_render_op` FOREIGN KEY (`id_op`) REFERENCES `tbl_ordenproduccion` (`id_op`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;