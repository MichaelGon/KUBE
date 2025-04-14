import os
import logging
from datetime import datetime
from flask import Flask, request, jsonify
from flask_restful import Api, Resource

server = Flask(__name__)
api = Api(server)

LOG_SEVERITY = os.environ.get('LOG_SEVERITY', 'INFO')
SERVICE_PORT = int(os.environ.get('SERVICE_PORT', 5000))
GREETING = os.environ.get('GREETING', 'Welcome to the custom app')

logging.basicConfig(
    level=getattr(logging, LOG_SEVERITY),
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/application/journal/app.log')
    ]
)
journal = logging.getLogger('journal_service')


class HomeResource(Resource):
    def get(self):
        journal.info("Запрос к корневому маршруту")
        return GREETING


class HealthResource(Resource):
    def get(self):
        journal.info("Проверка работоспособности")
        return {"status": "ok"}


class JournalEntryResource(Resource):
    def post(self):
        data = request.get_json()
        entry = data.get('message', '')
        journal.info(f"Получена запись: {entry}")

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open('/application/journal/app.log', 'a') as journal_file:
            journal_file.write(f"[{timestamp}] {entry}\n")

        return {"result": "запись добавлена", "time": timestamp}


class JournalViewResource(Resource):
    def get(self):
        journal.info("Запрос содержимого журнала")
        try:
            with open('/application/journal/app.log', 'r') as journal_file:
                content = journal_file.read()
            return content
        except Exception as e:
            journal.error(f"Ошибка чтения журнала: {e}")
            return {"error": str(e)}, 500


api.add_resource(HomeResource, '/')
api.add_resource(HealthResource, '/status')
api.add_resource(JournalEntryResource, '/log')
api.add_resource(JournalViewResource, '/logs')

if __name__ == '__main__':
    server.run(host='0.0.0.0', port=SERVICE_PORT)
