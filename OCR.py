import base64
import requests
import json
import logging
from Auth import IAM, FOLDER_ID
import PyPDF2
import time
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def encode_file(file):
    try:
        with open(f'{file}', 'rb') as f:
            file_content = f.read()
            return base64.b64encode(file_content)
    except:
        print("File reading error :( ")
        return None

def recognize_one_page(encoded_file):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {IAM}",
        "x-folder-id": FOLDER_ID,
        "x-data-logging-enabled": "true"
    }

    data = {
        "mimeType": "application/pdf",
        "languageCodes": ["*"],
        "model": "table",
        "content": encoded_file
    }

    url = "https://ocr.api.cloud.yandex.net/ocr/v1/recognizeText"

    result = requests.post(url, headers=headers, json=data)

    if result.status_code != 200:
        print("Daemon return code {}".format(result.status_code))
        print(result.content)
        return None
    else:
        return json.loads(result.content)

def process_pdf(file_path):
    with open(file_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        num_pages = len(pdf_reader.pages)
        for page_num in range(num_pages):

            pdf_writer = PyPDF2.PdfWriter()
            pdf_writer.add_page(pdf_reader.pages[page_num])

            temp_pdf_path = f'tmp/temporary_page_{page_num + 1}.pdf'
            with open(temp_pdf_path, 'wb') as temp_pdf_file:
                pdf_writer.write(temp_pdf_file)


            encoded_page = encode_file(temp_pdf_path).decode("utf-8")
            recognition_result = recognize_one_page(encoded_page)

            if recognition_result:
                output_filename = f'outputs/output_page_{page_num + 1}.json'
                with open(output_filename, 'w') as output_file:
                    json.dump(recognition_result, output_file)
                logging.info(f"Результат OCR сохранён в {output_filename}")

def recognize_file(encoded_file):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {IAM}",
        "x-folder-id": FOLDER_ID,
        "x-data-logging-enabled": "true"
    }

    data = {
        "mimeType": "application/pdf",
        "languageCodes": ["*"],
        "model": "page",
        "content": encoded_file
    }

    url = "https://ocr.api.cloud.yandex.net/ocr/v1/recognizeTextAsync"

    result = requests.post(url, headers=headers, json=data)

    if result.status_code != 200:
        print("Daemon return code {}".format(result.status_code))
        print(result.content)
        return None
    else:
        return json.loads(result.content)


def get_recognition(recognition_id):
    time.sleep(30)
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {IAM}",
        "x-folder-id": "b1gvg8hv0tcuji248evj",
        "x-data-logging-enabled": "true",
    }

    url = f"https://ocr.api.cloud.yandex.net/ocr/v1/getRecognition?operationId={recognition_id}"

    response = requests.get(url, headers=headers)

    return response.content

def read_whole_pdf(pdf_path, filename):
    encoded_file = encode_file(pdf_path).decode("utf-8")
    recognition = recognize_file(encoded_file)
    id = recognition['id']
    print((id))
    result = get_recognition(id)
    print(result)
    with open(f'{filename}', 'wb') as f:
        f.write(result)

