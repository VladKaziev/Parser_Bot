import json
import pandas as pd

def handle_json(file_path, file_name):
    # Загрузка данных JSON
    with open(file_path,'r', encoding='utf-8') as file:
        data = json.load(file)

    blocks = data['result']['textAnnotation']['blocks']

    # Подготовка данных для группировки
    entries = []
    for block in blocks:
        for line in block.get('lines', []):
            vertices = line['boundingBox']['vertices']
            text = line.get('text', '')
            # Средняя точка по y для определения строк, приведение к int
            y_avg = sum(int(vertex['y']) for vertex in vertices) / len(vertices)
            # Минимальная точка по x для определения порядка в строке, приведение к int
            x_min = min(int(vertex['x']) for vertex in vertices)
            entries.append((y_avg, x_min, text))

    # Сортировка для последующей группировки
    entries.sort()

    # Группировка строк по y с учетом допуска в 10 пикселей
    tolerance = 10
    rows = []
    current_row = []

    for entry in entries:
        if not current_row or abs(current_row[-1][0] - entry[0]) <= tolerance:
            current_row.append(entry)
        else:
            # Сортировка по x и добавление в итоговую таблицу
            rows.append([text for _, _, text in sorted(current_row, key=lambda x: x[1])])
            current_row = [entry]

    # Не забыть добавить последнюю строку
    if current_row:
        rows.append([text for _, _, text in sorted(current_row, key=lambda x: x[1])])

    df = pd.DataFrame(rows)
    df.to_json(f'outputs/{file_name}', orient='records', lines=True, force_ascii=False)