import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandStart
from aiogram.types import FSInputFile, ReplyKeyboardMarkup, KeyboardButton
from OCR import process_pdf, read_whole_pdf
from Auth import TOKEN
from json_handler import handle_json, merge_json_files, fix_json, json_to_txt
from compare_files import extract_text_from_pdf, compare_files, write_to_csv

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Клавиатура
keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Получить json'), KeyboardButton(text='Сравнить файлы')]
    ],
    resize_keyboard=True,
    input_field_placeholder='Выберите пункт в меню'
)

# Определение состояний для FSM
class DocumentStates(StatesGroup):
    waiting_for_pdf = State()  # Для получения одного PDF файла
    waiting_for_first_file = State()  # Для получения первого файла для сравнения
    waiting_for_second_file = State()  # Для получения второго файла для сравнения

# Обработчик команды старт
@dp.message(CommandStart())
async def start_command(message: types.Message):
    logging.info(f"Received start command from {message.from_user.id}")
    await message.answer('Привет!', reply_markup=keyboard)

# Обработчик для получения JSON из PDF
@dp.message(F.text == 'Получить json')
async def button_get_json(message: types.Message, state: FSMContext):
    await state.set_state(DocumentStates.waiting_for_pdf)
    await message.answer('Пришлите файл в формате PDF')

# Обработчик для начала процесса сравнения файлов
@dp.message(F.text == 'Сравнить файлы')
async def button_compare_files(message: types.Message, state: FSMContext):
    await state.set_state(DocumentStates.waiting_for_first_file)
    await message.answer('Пришлите первый файл для сравнения')

# Обработка PDF документа для создания JSON
@dp.message(DocumentStates.waiting_for_pdf)
async def process_document(message: types.Message, state: FSMContext):
    logging.info(f"Received document from {message.from_user.id}")
    file_id = message.document.file_id
    file_info = await bot.get_file(file_id)
    destination_path = "downloaded_file.pdf"
    await bot.download_file(file_info.file_path, destination=destination_path)
    logging.info(f"File downloaded: {file_info.file_path}")
    process_pdf(destination_path)
    directory_path = 'outputs'
    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)
        handle_json(file_path, file_name=filename)
        fix_json(file_path)
    merge_json_files(directory_path, 'outputs/output.json')
    file = FSInputFile(f'outputs/output.json')
    await message.answer_document(file)
    await state.clear()
    await delete_files()

# Обработка первого файла для сравнения
@dp.message(DocumentStates.waiting_for_first_file)
async def process_first_file(message: types.Message, state: FSMContext):
    file_id = message.document.file_id
    file_info = await bot.get_file(file_id)
    destination_path1 = "first_file.pdf"
    await bot.download_file(file_info.file_path, destination=destination_path1)
    await state.update_data(first_file=destination_path1)
    await state.set_state(DocumentStates.waiting_for_second_file)
    await message.answer('Теперь пришлите второй файл для сравнения')

# Обработка второго файла для сравнения
@dp.message(DocumentStates.waiting_for_second_file)
async def process_second_file(message: types.Message, state: FSMContext):
    file_id = message.document.file_id
    file_info = await bot.get_file(file_id)
    destination_path2 = "second_file.pdf"
    await bot.download_file(file_info.file_path, destination=destination_path2)
    data = await state.get_data()
    destination_path1 = data['first_file']
    result_ocr1 = 'outputs/result_ocr1.json'
    result_ocr2 = 'outputs/result_ocr2.json'
    process_pdf(destination_path1)
    directory_path = 'outputs'
    for i,filename in enumerate(os.listdir(directory_path)):
        file_path = os.path.join(directory_path, filename)
        handle_json(file_path, file_name=filename)
        fix_json(file_path)
    merge_json_files(directory_path, 'result_ocr1.json')
    await delete_files()
    process_pdf(destination_path2)
    for i,filename in enumerate(os.listdir(directory_path)):
        file_path = os.path.join(directory_path, filename)
        handle_json(file_path, file_name=filename)
        fix_json(file_path)
    merge_json_files(directory_path, 'result_ocr2.json')
    await delete_files()
    with open('result_ocr1.json', 'r', encoding='utf-8') as file:
        extracted_text1 = file.read().strip()
    with open('result_ocr2.json', 'r', encoding='utf-8') as file:
        extracted_text2 = file.read().strip()
    # ocr_txt1 = 'result_ocr1.txt'
    # ocr_txt2 = 'result_ocr2.txt'
    # json_to_txt(result_ocr1, ocr_txt1)
    # json_to_txt(result_ocr2, ocr_txt2)
    # with open('result_ocr1.txt', 'r', encoding='utf-16') as file:
    #     extracted_text1 = file.read()
    # with open('result_ocr1.txt', 'r', encoding='utf-16') as file:
    #     extracted_text2 = file.read()
    result = compare_files(extracted_text1, extracted_text2)
    write_to_csv(result, 'outputs/output.csv')
    file = FSInputFile(f'outputs/output.csv')
    await message.answer_document(file)
    await state.clear()

async def delete_files():
    directory_path = 'outputs'
    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)
        os.remove(file_path)
    directory = "tmp"
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        try:
            # Проверяем, является ли это файлом (не директорией)
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"Не удалось удалить {file_path}. Причина: {e}")



async def main():
    logging.info("Starting polling")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())