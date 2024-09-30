import pytesseract
import os
import tempfile
from PIL import Image
from flask import request, jsonify, Blueprint, current_app
from pdf2image import convert_from_path
from datetime import datetime
from blood_analysis.utils import extract_data
from kafka import KafkaProducer
import json
from bson import json_util
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity

blood_analysis = Blueprint('blood_analysis', __name__)

producer = KafkaProducer(
    bootstrap_servers='localhost:9092'
)


def extract_text_from_pdf(pdf_path):
    # Convert PDF to image
    pages = convert_from_path(pdf_path, 500,
                              poppler_path=r"C:\Users\stank\Downloads\Release-24.07.0-0\poppler-24.07.0\Library\bin")

    # Extract text from each page using Tesseract OCR
    text_data = ''
    for page in pages:
        text = pytesseract.image_to_string(page)
        text_data += text + '\n'

    # Return the text data
    return text_data


@blood_analysis.route('/analyze-report', methods=['POST'])
@jwt_required()
def upload_image():
    laboratory_reports = current_app.db.laboratory_reports

    if 'image' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file_path = request.files['image']

    if file_path.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    file_name, file_extension = os.path.splitext(file_path.filename)
    content_type = file_path.content_type
    current_app.logger.info(content_type)

    if file_extension in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff'] or content_type.startswith('image/'):
        try:
            image = Image.open(file_path)
            text_data = pytesseract.image_to_string(image)

        except Exception as e:
            return jsonify({'error': 'Error processing image', 'details': str(e)}), 500

    elif file_extension == '.pdf' or content_type == 'application/pdf':
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            temp_file.write(file_path.read())
            temp_pdf_path = temp_file.name

        try:
            text_data = extract_text_from_pdf(temp_pdf_path)
        except Exception as e:
            return jsonify({'error': 'Error processing pdf file', 'details': str(e)}), 500
        finally:
            os.remove(temp_pdf_path)
    else:
        return jsonify({'error': 'Unsupported file type'}), 400

    values_out_of_range, values_in_range = extract_data(text_data)
    current_user = get_jwt_identity()
    user_id = current_user["user_id"]
    laboratory_report = laboratory_reports.insert_one({"user_id": user_id, "datetime": datetime.now(),
                                                       "values_out_of_range": values_out_of_range,
                                                       "values_in_range": values_in_range})
    current_app.logger.info(laboratory_report.inserted_id)
    current_app.logger.info(type(values_out_of_range))
    message_to_be_sent = {
        "user_id": user_id,
        "report_id": laboratory_report.inserted_id,
        "values_out_of_range": values_out_of_range
    }
    current_app.logger.info(message_to_be_sent)
    producer.send('microservice-topic', json.dumps(message_to_be_sent, default=json_util.default).encode('utf-8'))

    return jsonify({'message': 'File uploaded successfully', 'status': 'success', 'good_values': values_in_range,
                    'bad_values': values_out_of_range}), 200
