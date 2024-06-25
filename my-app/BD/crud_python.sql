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

-- Volcando estructura para tabla crud_python.tbl_empleados
CREATE TABLE `tbl_empleados` (
  `documento` int NOT NULL,
  `id_empleado` int NOT NULL AUTO_INCREMENT,
  `nombre_empleado` varchar(50) DEFAULT NULL,
  `apellido_empleado` varchar(50) DEFAULT NULL,
  `tipo_empleado` int DEFAULT NULL,
  `telefono_empleado` varchar(50) DEFAULT NULL,
  `email_empleado` varchar(50) DEFAULT NULL,
  `cargo` varchar(50) DEFAULT NULL,
  `foto_empleado` mediumtext,
  `fecha_registro` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_empleado`)
) ENGINE=InnoDB AUTO_INCREMENT=84 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

;
CREATE TABLE `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name_surname` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `email_user` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `pass_user` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `created_user` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Creando tabla Actividades
CREATE TABLE `tbl_actividades` (
  `id_actividad` int NOT NULL AUTO_INCREMENT,
  `codigo_actividad` varchar(50) NOT NULL,
  `nombre_actividad` varchar(50) DEFAULT NULL,
  `descripcion_actividad` varchar(200) DEFAULT NULL,
  `fecha_registro` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_actividad`),
  UNIQUE KEY `codigo_actividad_UNIQUE` (`codigo_actividad`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


;
CREATE TABLE `tbl_clientes` (
  `id_cliente` int NOT NULL AUTO_INCREMENT,
  `tipo_documento` varchar(50) DEFAULT NULL,
  `documento` int NOT NULL,
  `nombre_cliente` varchar(50) DEFAULT NULL,
  `telefono_cliente` varchar(50) DEFAULT NULL,
  `email_cliente` varchar(50) DEFAULT NULL,
  `foto_cliente` mediumtext,
  `fecha_registro` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_cliente`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


;
CREATE TABLE `tbl_jornadas` (
  `id_jornada` int NOT NULL AUTO_INCREMENT,
  `id_empleado` int NOT NULL,
  `nombre_empleado` varchar(50) DEFAULT NULL,
  `novedad_jornada_programada` varchar(200) DEFAULT NULL,
  `novedad_jornada` varchar(50) DEFAULT NULL,
  `fecha_hora_llegada_programada` timestamp NOT NULL,
  `fecha_hora_salida_programada` timestamp NOT NULL,
  `fecha_hora_llegada` timestamp NOT NULL,
  `fecha_hora_salida` timestamp NOT NULL,
  `fecha_registro` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `usuario_registro` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id_jornada`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

;
CREATE TABLE `tbl_operaciones` (
  `id_operacion` int NOT NULL AUTO_INCREMENT,
  `id_empleado` int NOT NULL,
  `nombre_empleado` varchar(50) DEFAULT NULL,
  `proceso` varchar(50) DEFAULT NULL,
  `actividad` varchar(50) DEFAULT NULL,
  `codigo_op` int DEFAULT NULL,
  `cantidad` int DEFAULT NULL,
  `novedad` mediumtext,
  `fecha_hora_inicio` timestamp NOT NULL,
  `fecha_hora_fin` timestamp NOT NULL,
  `fecha_registro` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `usuario_registro` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id_operacion`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


;
CREATE TABLE `tbl_ordenproduccion` (
  `id_op` int NOT NULL AUTO_INCREMENT,
  `codigo_op` int NOT NULL,
  `nombre_cliente` varchar(50) DEFAULT NULL,
  `producto` varchar(200) DEFAULT NULL,
  `estado` varchar(50) DEFAULT NULL,
  `cantidad` int DEFAULT NULL,
  `odi` varchar(50) DEFAULT NULL,
  `empleado` varchar(50) DEFAULT NULL,
  `fecha_registro` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `usuario_registro` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id_op`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

;
CREATE TABLE `tbl_procesos` (
  `id_proceso` int NOT NULL AUTO_INCREMENT,
  `codigo_proceso` varchar(50) NOT NULL,
  `nombre_proceso` varchar(50) DEFAULT NULL,
  `descripcion_proceso` varchar(200) DEFAULT NULL,
  `fecha_registro` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_proceso`),
  UNIQUE KEY `codigo_proceso_UNIQUE` (`codigo_proceso`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;





CREATE TABLE `tbl_tipo_documento` (
  `id_tipo_documento` int NOT NULL AUTO_INCREMENT,
  `td_abreviacion` varchar(45) NOT NULL,
  `tipo_documento` varchar(45) NOT NULL,
  `fecha_registro` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_tipo_documento`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4;


INSERT INTO evolution_plastic.tbl_tipo_empleado (tipo_empleado)
VALUES ("Directo"), ("Temporal");


CREATE TABLE `tbl_tipo_empleado` (
  `id_tipo_empleado` int NOT NULL AUTO_INCREMENT,
  `tipo_empleado` varchar(45) NOT NULL,
  `fecha_registro` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_tipo_empleado`)
) ENGINE=InnoDB AUTO_INCREMENT=0 DEFAULT CHARSET=utf8mb4;

INSERT INTO evolution_plastic.tbl_tipo_documento (td_abreviacion, tipo_documento)
VALUES ("NIT", "Número de Identificación Tributaria"), ("CC", "Cedula de ciudadanía");