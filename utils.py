import zipfile
import io

def save_to_zip(text_dict):
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for page, text in text_dict.items():
            zip_file.writestr(f'page_{page}.txt', text)
    return zip_buffer.getvalue()