README: Weather-Based Order System
Суть: Сервис создает заказы на товары (зонт, очки, куртка) в зависимости от погоды из внешнего API.  
Стек: Python, БД (SQLite/Postgres), Mock-фреймворки.  
Unit-тесты: Проверка логики suggest_product и моков без реальной БД/API . 
Integration-тесты: Работа с реальной тестовой БД (создание юзера + заказ) . 
API Mocking: Тест поведения при таймаутах и кривых данных от погоды.
Final Test: Полный флоу «БД + Mock API» (запись и верификация) .  
Бизнес-логика: Rain → Umbrella, Sunny → Sunglasses, Snow → Jacket . 
БД-схема: Таблицы User (id, name, city) и Order (id, user_id, product) . 
Цель: Покрыть систему тестами на 100% и обеспечить отказоустойчивость. 
