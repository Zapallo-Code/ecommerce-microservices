-- Script de inicialización de bases de datos para los microservicios
-- Este script se ejecuta automáticamente cuando se crea el contenedor de PostgreSQL por primera vez

-- Crear base de datos para el microservicio de Catalog
CREATE DATABASE ms_catalog;

-- Crear base de datos para el microservicio de Payments
CREATE DATABASE ms_payments;

-- Crear base de datos para el microservicio de Inventory
CREATE DATABASE ms_inventory;

-- Crear base de datos para el microservicio de Purchases
CREATE DATABASE ms_purchases;
