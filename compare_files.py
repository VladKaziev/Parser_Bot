import requests
from Auth import model,key
import PyPDF2

def extract_text_from_pdf(pdf_path):
    text = ''
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        num_pages = len(pdf_reader.pages)
        for page_num in range(num_pages):
            page = pdf_reader.pages[page_num]
            text += page.extract_text()
    return text


def compare_files(extracted_text, extracted_text2):
    prompt = {
        "modelUri": model,
        "completionOptions": {
            "stream": False,
            "temperature": 0.1,
            "maxTokens": "200000"
        },
        "messages": [
            {
                "role": "system",
                "text": "Ты ассистент, способный помочь в обработке технической документации."
            },
            {
                "role": "user",
                "text": "Привет, ассистент! Мне нужна твоя помощь, в извлечении технических характеристик из текста двух документов. После этого нужно сравнить технические характеристики в них и написать отличия."
            },
            {
                "role": "assistant",
                "text": "Привет! Из какого текста и какую именно информацию мне стоит достать?"
            },
            {
                "role": "user",
                "text": f"Информацией являются все технические характеристики в тексте первого документа: {extracted_text}, и в тексте второго: {extracted_text2}.Верни только отличия технических характеристик в этих документах в формате таблицы. Обязательно, кроме таблицы никакой информации не выводи."
            }
        ]
    }

    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Api-Key {key}"
    }

    response = requests.post(url, headers=headers, json=prompt)
    result = response.text[66:-152]
    return result