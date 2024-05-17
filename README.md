# Веб-приложение для планирования загрузки производственных мощностей

## Описание
![Django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white)
![HTMX](https://img.shields.io/badge/HTMX-FF69B4?style=for-the-badge&logo=htmx&logoColor=white)
![Alpine.js](https://img.shields.io/badge/Alpine.js-8BC0D0?style=for-the-badge&logo=alpine.js&logoColor=white)
![Bootstrap](https://img.shields.io/badge/Bootstrap-563D7C?style=for-the-badge&logo=bootstrap&logoColor=white)

![img.png](readme_logos.png)

## Основные функции

Реализован ролевой доступ на рабочих и администраторов

### Функционал для рабочих:
![worker.gif](worker.gif)
_(подождите пока загрузится gif)_
- Заполнение и сдача формы с отчетом об изготовленных за смену деталях

### Функционал для администраторов:
![admin.gif](admin.gif)
_(подождите пока загрузится gif)_
- Просмотр сводной таблицы-плана <br>
  Слева заказы: количество деталей на изготовление и текущий прогресс изготовления вычисленный по отчетам <br>
  Справа таблица смена/станок с соответствующими отчетами или планами в каждой ячейке
- Удобный drag-n-drop интерфейс для планирования - перетаскивание детали из списка заказов в ячейку таблицы автоматически создает соответствующий план
- CRUD отчетов от имени любого сотрудника
- CRUD заказов
- CRUD станков
- CRUD деталей
- CRUD пользователей

## Запуск

1. Склонируйте репозиторий
2. Установите зависимости
```bash
pip install -r requirements.txt
```
3. Примените миграции
```bash
python manage.py migrate
```
4. Запустите команду demo_setup для создания демонстрационных данных
```bash
python manage.py demo_setup
```
5. Запустите сервер
```bash
python manage.py runserver
```

