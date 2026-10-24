def calculate_cost(quantity, price):
    """Вычисляет полную стоимость заказа."""
    return round(quantity * price, 2)


def determine_cost_category(cost):
    """Определяет категорию стоимости заказа."""
    if cost < 1000:
        return "Малый"
    elif cost < 5000:
        return "Средний"
    return "Крупный"


def parse_line(line):
    """Разбивает строку на поля и удаляет лишние пробелы по краям."""
    return [part.strip() for part in line.strip().split(";")]


def validate_record(parts, line_num, existing_ids):
    """Проверяет корректность полей записи и возвращает словарь заказа или текст ошибки."""
    if len(parts) != 6:
        return None, f"Строка {line_num}: неверное количество полей ({len(parts)} вместо 6)."

    order_id_str, name, category, qty_str, price_str, status_raw = parts

    try:
        order_id = int(order_id_str)
    except ValueError:
        return None, f"Строка {line_num}: номер заказа не является целым числом."

    if order_id <= 0:
        return None, f"Строка {line_num}: номер заказа должен быть положительным."

    if order_id in existing_ids:
        return None, f"Строка {line_num}: повторяющийся номер заказа {order_id}."

    if not name:
        return None, f"Строка {line_num}: имя покупателя не может быть пустым."

    if not category:
        return None, f"Строка {line_num}: категория товара не может быть пустой."

    try:
        qty = int(qty_str)
    except ValueError:
        return None, f"Строка {line_num}: количество не является целым числом."

    if qty <= 0:
        return None, f"Строка {line_num}: количество должно быть положительным."

    try:
        price = float(price_str)
    except ValueError:
        return None, f"Строка {line_num}: цена не является числом."

    if price <= 0:
        return None, f"Строка {line_num}: цена должна быть положительным числом."

    valid_statuses = {"новый", "в обработке", "выполнен", "отменён"}
    status = status_raw.lower()
    if status not in valid_statuses:
        return None, f"Строка {line_num}: неизвестный статус «{status_raw}»."

    cost = calculate_cost(qty, price)
    cost_category = determine_cost_category(cost)

    order = {
        "id": order_id,
        "name": name,
        "category": category,
        "quantity": qty,
        "price": price,
        "status": status,
        "cost": cost,
        "cost_category": cost_category,
    }
    return order, None


def load_orders(filename):
    """Читает заказы из файла и возвращает список корректных заказов и список ошибок."""
    orders = []
    errors = []
    existing_ids = set()

    try:
        with open(filename, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                if not line.strip():
                    continue
                parts = parse_line(line)
                order, error = validate_record(parts, line_num, existing_ids)
                if order is not None:
                    orders.append(order)
                    existing_ids.add(order["id"])
                else:
                    errors.append(error)
    except FileNotFoundError:
        print(f"Ошибка: входной файл «{filename}» не найден.")
    except OSError as e:
        print(f"Ошибка при чтении файла «{filename}»: {e}")

    return orders, errors


def sort_by_cost_desc(orders):
    """Сортирует заказы по убыванию стоимости, а при равенстве — по возрастанию номера."""
    return sorted(orders, key=lambda x: (-x["cost"], x["id"]))


def sort_by_category_and_name(orders):
    """Сортирует заказы по категории и по имени покупателя в алфавитном порядке."""
    return sorted(orders, key=lambda x: (x["category"].lower(), x["name"].lower()))


def filter_by_status(orders, status):
    """Возвращает список заказов с указанным статусом."""
    target = status.strip().lower()
    return [o for o in orders if o["status"] == target]


def filter_by_category(orders, category):
    """Возвращает список заказов указанной категории."""
    target = category.strip().lower()
    return [o for o in orders if o["category"].lower() == target]


def search_by_name(orders, name_part):
    """Ищет заказы по части имени покупателя без учёта регистра."""
    target = name_part.strip().lower()
    if not target:
        return []
    return [o for o in orders if target in o["name"].lower()]


def get_large_orders(orders):
    """Возвращает крупные заказы со стоимостью не меньше 5000."""
    return [o for o in orders if o["cost"] >= 5000]


def get_unique_categories(orders):
    """Возвращает отсортированный по алфавиту список уникальных категорий."""
    categories = {o["category"] for o in orders}
    return sorted(categories)


def calc_category_stats(orders):
    """Рассчитывает статистику по каждой категории товаров."""
    stats = {}
    for cat in get_unique_categories(orders):
        stats[cat] = {
            "count": 0,
            "qty": 0,
            "total_cost": 0.0,
            "completed_cost": 0.0,
            "avg_cost": 0.0,
        }

    for o in orders:
        cat = o["category"]
        stats[cat]["count"] += 1
        stats[cat]["qty"] += o["quantity"]
        stats[cat]["total_cost"] = round(stats[cat]["total_cost"] + o["cost"], 2)
        if o["status"] == "выполнен":
            stats[cat]["completed_cost"] = round(stats[cat]["completed_cost"] + o["cost"], 2)

    for cat in stats:
        stats[cat]["avg_cost"] = round(stats[cat]["total_cost"] / stats[cat]["count"], 2)

    return stats


def calc_status_stats(orders):
    """Подсчитывает количество заказов для каждого допустимого статуса."""
    valid_statuses = ["новый", "в обработке", "выполнен", "отменён"]
    stats = {st: 0 for st in valid_statuses}
    for o in orders:
        if o["status"] in stats:
            stats[o["status"]] += 1
    return stats


def calc_general_stats(orders):
    """Вычисляет общие показатели по всем заказам."""
    if not orders:
        return None

    total_orders = len(orders)
    completed = [o for o in orders if o["status"] == "выполнен"]
    cancelled = [o for o in orders if o["status"] == "отменён"]

    total_cost = round(sum(o["cost"] for o in orders), 2)
    revenue = round(sum(o["cost"] for o in completed), 2)
    avg_cost = round(total_cost / total_orders, 2)
    max_order = max(orders, key=lambda x: x["cost"])

    best_customers = []
    max_spent = 0.0
    if completed:
        customer_totals = {}
        for o in completed:
            customer_totals[o["name"]] = round(customer_totals.get(o["name"], 0.0) + o["cost"], 2)
        max_spent = max(customer_totals.values())
        best_customers = [name for name, spent in customer_totals.items() if spent == max_spent]

    return {
        "total_orders": total_orders,
        "completed_count": len(completed),
        "cancelled_count": len(cancelled),
        "total_cost": total_cost,
        "revenue": revenue,
        "avg_cost": avg_cost,
        "max_order": max_order,
        "best_customers": best_customers,
        "best_customer_sum": max_spent,
    }


def format_order_line(order):
    """Форматирует одну запись заказа для табличного вывода."""
    return (
        f"{order['id']:<6} | {order['name']:<18} | {order['category']:<13} | "
        f"{order['quantity']:<5} | {order['price']:<9.2f} | {order['cost']:<10.2f} | "
        f"{order['status']:<12} | {order['cost_category']}"
    )


def print_orders(orders):
    """Выводит таблицу заказов в консоль."""
    if not orders:
        print("Заказы не найдены.")
        return

    header = (
        f"{'Номер':<6} | {'Покупатель':<18} | {'Категория':<13} | "
        f"{'Кол.':<5} | {'Цена':<9} | {'Стоимость':<10} | "
        f"{'Статус':<12} | {'Категория ст.'}"
    )
    print(header)
    print("-" * len(header))
    for o in orders:
        print(format_order_line(o))


def print_statistics(orders):
    """Выводит в консоль общие показатели и статистику по категориям и статусам."""
    if not orders:
        print("Нет корректных записей для расчёта статистики.")
        return

    general = calc_general_stats(orders)
    print("\n--- Общие показатели ---")
    print(f"Общее количество заказов: {general['total_orders']}")
    print(f"Количество выполненных заказов: {general['completed_count']}")
    print(f"Количество отменённых заказов: {general['cancelled_count']}")
    print(f"Общая стоимость всех заказов: {general['total_cost']:.2f}")
    print(f"Выручка по выполненным заказам: {general['revenue']:.2f}")
    print(f"Средняя стоимость заказа: {general['avg_cost']:.2f}")
    max_o = general["max_order"]
    print(f"Самый дорогой заказ: №{max_o['id']} ({max_o['name']}, {max_o['cost']:.2f})")
    if general["best_customers"]:
        names = ", ".join(general["best_customers"])
        print(f"Покупатель с наибольшей суммой выполненных заказов: {names} ({general['best_customer_sum']:.2f})")
    else:
        print("Выручка равна 0.00, определить лучшего покупателя невозможно (нет выполненных заказов).")

    print("\n--- Уникальные категории ---")
    print(", ".join(get_unique_categories(orders)))

    print("\n--- Статистика по категориям товаров ---")
    cat_stats = calc_category_stats(orders)
    for cat, st in cat_stats.items():
        print(
            f"{cat}: заказов — {st['count']}, единиц товара — {st['qty']}, "
            f"общая стоимость — {st['total_cost']:.2f}, стоимость выполненных — {st['completed_cost']:.2f}, "
            f"средняя стоимость — {st['avg_cost']:.2f}"
        )

    print("\n--- Статистика по статусам ---")
    status_stats = calc_status_stats(orders)
    for status, count in status_stats.items():
        print(f"{status}: {count}")


def build_report(orders, errors):
    """Формирует текст итогового отчёта по всем разделам."""
    lines = []
    lines.append("ОТЧЁТ ПО АНАЛИЗУ ЗАКАЗОВ МАГАЗИНА")
    lines.append("=" * 40)
    lines.append(f"1. Количество корректных записей: {len(orders)}")
    lines.append(f"2. Количество некорректных записей: {len(errors)}")

    lines.append("\n3. Перечень уникальных категорий:")
    unique_cats = get_unique_categories(orders)
    if unique_cats:
        for cat in unique_cats:
            lines.append(f"   - {cat}")
    else:
        lines.append("   Категории отсутствуют.")

    lines.append("\n4. Заказы по убыванию стоимости:")
    sorted_orders = sort_by_cost_desc(orders)
    if sorted_orders:
        for o in sorted_orders:
            lines.append("   " + format_order_line(o))
    else:
        lines.append("   Нет корректных заказов.")

    lines.append("\n5. Перечень крупных заказов (от 5000):")
    large_orders = get_large_orders(orders)
    if large_orders:
        for o in large_orders:
            lines.append("   " + format_order_line(o))
    else:
        lines.append("   Крупные заказы отсутствуют.")

    lines.append("\n6. Общие показатели:")
    general = calc_general_stats(orders)
    if general:
        lines.append(f"   - Общее количество заказов: {general['total_orders']}")
        lines.append(f"   - Количество выполненных заказов: {general['completed_count']}")
        lines.append(f"   - Количество отменённых заказов: {general['cancelled_count']}")
        lines.append(f"   - Общая стоимость всех заказов: {general['total_cost']:.2f}")
        lines.append(f"   - Выручка по выполненным заказам: {general['revenue']:.2f}")
        lines.append(f"   - Средняя стоимость заказа: {general['avg_cost']:.2f}")
        max_o = general["max_order"]
        lines.append(f"   - Самый дорогой заказ: №{max_o['id']} ({max_o['name']}, {max_o['cost']:.2f})")
        if general["best_customers"]:
            names = ", ".join(general["best_customers"])
            lines.append(
                f"   - Покупатель с наибольшей суммой выполненных заказов: {names} ({general['best_customer_sum']:.2f})"
            )
        else:
            lines.append("   - Выручка равна нулю, определить лучшего покупателя невозможно.")
    else:
        lines.append("   Невозможно вычислить показатели для пустого списка заказов.")

    lines.append("\n7. Статистика по категориям:")
    cat_stats = calc_category_stats(orders)
    if cat_stats:
        for cat, st in cat_stats.items():
            lines.append(
                f"   - {cat}: заказов — {st['count']}, единиц — {st['qty']}, "
                f"общая стоимость — {st['total_cost']:.2f}, стоимость выполненных — {st['completed_cost']:.2f}, "
                f"средняя стоимость — {st['avg_cost']:.2f}"
            )
    else:
        lines.append("   Нет данных по категориям.")

    lines.append("\n8. Статистика по статусам:")
    status_stats = calc_status_stats(orders)
    for st, count in status_stats.items():
        lines.append(f"   - {st}: {count}")

    lines.append("\n9. Список ошибок входных данных:")
    if errors:
        for err in errors:
            lines.append(f"   - {err}")
    else:
        lines.append("   Ошибок во входных данных не обнаружено.")

    return "\n".join(lines) + "\n"


def save_report(orders, errors, filename="orders_report.txt"):
    """Сохраняет сформированный отчёт в текстовый файл."""
    report_text = build_report(orders, errors)
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(report_text)
        return True
    except OSError as e:
        print(f"Ошибка при сохранении отчёта: {e}")
        return False


def run_tests():
    """Выполняет автоматические проверки основных функций программы."""
    assert calculate_cost(2, 750.50) == 1501.00
    assert determine_cost_category(500) == "Малый"
    assert determine_cost_category(999.99) == "Малый"
    assert determine_cost_category(1000.00) == "Средний"
    assert determine_cost_category(4999.99) == "Средний"
    assert determine_cost_category(5000.00) == "Крупный"

    sample_orders = [
        {"id": 10, "name": "Иванов Иван", "category": "Книги", "quantity": 1, "price": 500.0, "cost": 500.0, "status": "выполнен", "cost_category": "Малый"},
        {"id": 5, "name": "Петрова Анна", "category": "Электроника", "quantity": 1, "price": 6000.0, "cost": 6000.0, "status": "отменён", "cost_category": "Крупный"},
        {"id": 2, "name": "Алексеев Пётр", "category": "Книги", "quantity": 2, "price": 3000.0, "cost": 6000.0, "status": "выполнен", "cost_category": "Крупный"},
    ]

    assert len(filter_by_status(sample_orders, "  ВЫПОЛНЕН ")) == 2
    assert len(filter_by_category(sample_orders, "книги")) == 2
    assert search_by_name(sample_orders, "анна")[0]["id"] == 5

    by_cost = sort_by_cost_desc(sample_orders)
    assert [o["id"] for o in by_cost] == [2, 5, 10]
    assert [o["id"] for o in sample_orders] == [10, 5, 2]

    by_cat = sort_by_category_and_name(sample_orders)
    assert [o["id"] for o in by_cat] == [2, 10, 5]

    stats = calc_general_stats(sample_orders)
    assert stats["revenue"] == 6500.00


def handle_menu(orders, errors):
    """Обрабатывает команды пользовательского меню в консоли."""
    while True:
        print("\nМеню:")
        print("1. Показать все заказы")
        print("2. Показать заказы по убыванию стоимости")
        print("3. Показать заказы по категориям")
        print("4. Найти заказы по статусу")
        print("5. Найти заказы по категории")
        print("6. Найти заказы покупателя")
        print("7. Показать крупные заказы")
        print("8. Показать статистику")
        print("9. Сохранить отчёт")
        print("0. Завершить программу")

        choice = input("Выберите пункт меню: ").strip()

        if choice == "1":
            print_orders(orders)
        elif choice == "2":
            print_orders(sort_by_cost_desc(orders))
        elif choice == "3":
            print_orders(sort_by_category_and_name(orders))
        elif choice == "4":
            status = input("Введите статус: ")
            res = filter_by_status(orders, status)
            if res:
                print_orders(res)
            else:
                print(f"Заказы со статусом «{status.strip()}» не найдены.")
        elif choice == "5":
            category = input("Введите категорию товара: ")
            res = filter_by_category(orders, category)
            if res:
                print_orders(res)
            else:
                print(f"Заказы в категории «{category.strip()}» не найдены.")
        elif choice == "6":
            name_part = input("Введите имя или часть имени покупателя: ")
            res = search_by_name(orders, name_part)
            if res:
                print_orders(res)
            else:
                print(f"Заказы покупателя «{name_part.strip()}» не найдены.")
        elif choice == "7":
            print_orders(get_large_orders(orders))
        elif choice == "8":
            print_statistics(orders)
        elif choice == "9":
            if save_report(orders, errors, "orders_report.txt"):
                print("Отчёт сохранён в файл orders_report.txt.")
        elif choice == "0":
            print("Работа программы завершена.")
            break
        else:
            print("Неизвестный пункт меню. Пожалуйста, введите число от 0 до 9.")


def main():
    """Точка входа в программу."""
    run_tests()
    orders, errors = load_orders("orders.txt")
    if errors:
        print(f"Загружено заказов: {len(orders)}. Пропущено некорректных строк: {len(errors)}.")
    handle_menu(orders, errors)


if __name__ == "__main__":
    main()
