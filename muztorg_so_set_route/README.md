# При створенні сейл ордер перевіряти значення поля Метод доставки.

Якщо метод доставки = "Нова Пошта (Ми платемо)" (id 3) або "Власна доставка" (id 5) в поле Route встановлювати значення
"МТ Київ: відвантаження через ТВ".

При цьому має спрацьовувати заповнення маршруту у рядках замовлення.

muztorg_so_set_route

## CHANGELOG

### 14.0.1.0.0

[ADD] - создание модуля

### 14.0.1.1.0

[IMP] - добавил очистку маршрута при изменении склада или способа доставки, если он не задан в настройках. Иначе
случайно можно отгрузить маршрутом "Новая почта" и способом доставки "Самовывоз"
