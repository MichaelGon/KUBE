import os
import logging
from datetime import datetime
from flask import Flask, request, jsonify, Response
from flask_restful import Api, Resource
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

LOG_REQUESTS_TOTAL = Counter(
    'journal_log_requests_total', 'Общее количество запросов к /log')
LOG_SUCCESS = Counter('journal_log_success', 'Успешные операции логирования')
LOG_FAILURE = Counter('journal_log_failure', 'Неудачные операции логирования')
REQUEST_TIME = Histogram('journal_request_duration_seconds', 'Время обработки запроса')

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
    @REQUEST_TIME.time()
    def post(self):
        LOG_REQUESTS_TOTAL.inc()
        data = request.get_json()
        entry = data.get('message', '')
        journal.info(f"Получена запись: {entry}")

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open('/application/journal/app.log', 'a') as journal_file:
            journal_file.write(f"[{timestamp}] {entry}\n")

        LOG_SUCCESS.inc()
        return {"result": "запись добавлена", "time": timestamp}


class JournalViewResource(Resource):
    def get(self):
        journal.info("Запрос содержимого журнала")
        try:
            with open('/application/journal/app.log', 'r') as journal_file:
                content = journal_file.read()
            return content
        except Exception as e:
            LOG_FAILURE.inc()
            journal.error(f"Ошибка чтения журнала: {e}")
            return {"error": str(e)}, 500
        

class MetricResource(Resource):
    def get(self):
        journal.info("Запрос метрик")
        return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


api.add_resource(HomeResource, '/')
api.add_resource(HealthResource, '/status')
api.add_resource(JournalEntryResource, '/log')
api.add_resource(JournalViewResource, '/logs')
api.add_resource(MetricResource, '/metrics')

if __name__ == '__main__':
    server.run(host='0.0.0.0', port=SERVICE_PORT)
