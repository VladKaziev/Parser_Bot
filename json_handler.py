import json
import pandas as pd
import logging
import os
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
def handle_json(file_path, file_name):
    # Загрузка данных JSON
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read().strip()
            if not content:
                print(f"Файл {file_name} пуст.")
                return
            data = json.loads(content)
            if 'result' not in data or 'textAnnotation' not in data['result'] or 'blocks' not in data['result']['textAnnotation']:
                print(f"Некорректная структура данных в файле {file_name}.")
                return
            blocks = data['result']['textAnnotation']['blocks']
            logging.info(f"JSON handled: {file_name}")
    except json.JSONDecodeError as e:
        print(f"Ошибка при разборе JSON в файле {file_name}: {e}")
        return
    except FileNotFoundError:
        print(f"Файл {file_name} не найден.")
        return
    except Exception as e:
        print(f"Произошла ошибка при обработке файла {file_name}: {e}")
        return

    # Подготовка данных для группировки
    entries = []
    for block in blocks:
        for line in block.get('lines', []):
            vertices = line['boundingBox']['vertices']
            text = line.get('text', '')
            try:
                y_avg = sum(int(vertex.get('y', 0)) for vertex in vertices) / len(vertices)
                x_min = min(int(vertex.get('x', 0)) for vertex in vertices)
                entries.append((y_avg, x_min, text))
            except ValueError as e:
                print(f"Ошибка в данных вершин: {e}")

    # Сортировка для последующей группировки
    entries.sort()

    # Группировка строк по y с учетом допуска в 10 пикселей
    tolerance = 50
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

def merge_json_files(directory, file_name):
    all_data = []  # Список для хранения данных из всех файлов
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read().strip()
                if len(content) > 4:  # Проверяем, что содержимое файла длиннее 4 символов
                    data = json.loads(content)
                    all_data.append(data)
                else:
                    print(f"Файл {filename} пропущен, так как содержит мало информации.")
        except json.JSONDecodeError as e:
            print(f"Ошибка при разборе JSON в файле {filename}: {e}")
        except Exception as e:
            print(f"Произошла ошибка при обработке файла {filename}: {e}")

    # Сохранение всех собранных данных в один файл
    if all_data:
        output_path = f'{file_name}'
        with open(output_path, 'w', encoding='utf-8') as file:
            json.dump(all_data, file, ensure_ascii=False, indent=4)
        logging.info(f"Данные успешно объединены и сохранены в {output_path}")
    else:
        print("Не найдено файлов, подходящих для объединения.")

def fix_json(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = "[" + file.read().replace("}\n{", "},\n{") + "]"
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(data)
    except Exception as e:
        print(f"Ошибка при исправлении JSON в файле {file_path}: {e}")

def json_to_txt(file_path, filename):
    with open(f'{file_path}', 'rb') as f:
        for line in f:
            with open(f'{filename}', 'a', encoding="utf-16") as fa:
                fa.write(json.loads(line)['result']['textAnnotation']['fullText'])