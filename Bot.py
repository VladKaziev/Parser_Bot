import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from OCR import process_pdf
from Auth import TOKEN
from aiogram.types import FSInputFile, ReplyKeyboardMarkup,KeyboardButton
import os
from json_handler import handle_json
from compare_files import extract_text_from_pdf, compare_files
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

bot = Bot(token=TOKEN)
dp = Dispatcher()

keyboard = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Получить json'), KeyboardButton(text='Сравнить файлы')]],
    resize_keyboard=True,
    input_field_placeholder='Выберите пункт в меню')

@dp.message(CommandStart())
async def start_command(message: types.Message):
    logging.info(f"Received start command from {message.from_user.id}")
    await message.answer('Привет!', reply_markup=keyboard)

@dp.message(F.text == 'Получить json')
async def button_get_json(message: types.Message):
    await message.answer('Пришлите файл в формате PDF')
    await process_document(message)

@dp.message(F.text == 'Сравнить файлы')
async def button_compare_files(message: types.Message):
    await message.answer('Пришлите файлы, которые хотите сравнить')
    await compare_2_files(message)

@dp.message(F.document)
async def compare_2_files(message: types.Message):
    await message.answer('Пришлите первый файл')
    file_1 = message.document.file_id
    file_info = await bot.get_file(file_1)
    destination_path1 = "first_file.pdf"
    await bot.download_file(file_info.file_path, destination=destination_path1)
    await message.answer('Пришлите второй файл')
    file2 = message.document.file_id
    file_info = await bot.get_file(file2)
    destination_path2 = "second_file.pdf"
    await bot.download_file(file_info.file_path, destination=destination_path2)
    if 'first_file.pdf' and 'secon_file.pdf':
        extracted_text = extract_text_from_pdf("first_file.pdf")
        extracted_text2 = extract_text_from_pdf("second_file.pdf")
        print(compare_files(extracted_text,extracted_text2))
@dp.message(F.document)
async def process_document(message: types.Message):
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
        file = FSInputFile(f'outputs/{filename}')
        await message.answer_document(file)
    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)
        os.remove(file_path)

    for filename in os.listdir(directory_path):
        file = FSInputFile(f'outputs/{filename}')
        await message.answer_document(file)
    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)
        try:
            # Проверяем, является ли это файлом (не директорией)
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"Не удалось удалить {file_path}. Причина: {e}")
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