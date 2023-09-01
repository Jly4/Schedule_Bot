"""
import csv

# Для парсинга всего сайта в csv файл.
for i in range(2, 11):
    # Открываем файл calls.csv в режиме 'a' (append) для добавления данных
    with open('calls.csv', 'a', newline='') as f:
    # Создаем объект writer
        writer = csv.writer(f)
    # Записываем пустую строку
        writer.writerow([])
        writer.writerow([f'dataframe index: {i}'])
        writer.writerow([])

    # Добавляем дата фрейм в csv
    shedule[i].to_csv("shedule.csv", index=False, index_label=False, mode='a')

    # В эксель
    shedule[i].to_excel("shedule.xlsx", index=False, index_label=False)
"""