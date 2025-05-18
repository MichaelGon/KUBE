#!/bin/bash

echo "Проверка подключения к кластеру Kubernetes..."
if ! kubectl cluster-info &> /dev/null; then
    echo "Не удалось подключиться к кластеру. Убедитесь, что кластер запущен."
    exit 1
fi

echo "Установка Istio"
istioctl install --set profile=demo -y

echo "Сборка образа приложения..."
docker build -t journal-service:latest .

echo "Загрузка образа в Minikube..."
minikube image load journal-service:latest

echo "Включаем injection Istio"
kubectl label namespace journal-system istio-injection=enabled --overwrite

echo "Установка Prometheus"
kubectl apply -f kubernetes/prometheus.yaml

echo "Создание конфигурации приложения..."
kubectl apply -f k8s/configuration.yaml

echo "Развертывание тестового пода..."
kubectl apply -f k8s/test-pod.yaml
echo "Ожидание готовности тестового пода..."
kubectl wait --for=condition=Ready pod/journal-test-pod --timeout=60s

echo "Проверка функциональности API..."
kubectl exec journal-test-pod -- curl -s http://localhost:5000/status

echo "Развертывание основного приложения..."
kubectl apply -f k8s/journal-deployment.yaml
echo "Ожидание готовности развертывания..."
kubectl wait --for=condition=Available deployment/journal-deployment --timeout=90s

echo "Создание сервиса для балансировки нагрузки..."
kubectl apply -f k8s/journal-service.yaml

echo "Настройка хранилища для архивирования..."
kubectl apply -f k8s/storage-volume.yaml
kubectl apply -f k8s/storage-claim.yaml

echo "Развертывание сборщика журналов на всех узлах..."
kubectl apply -f k8s/collector-daemonset.yaml

echo "Настройка задания для периодического архивирования..."
kubectl apply -f k8s/archiver-cronjob.yaml

echo "Применение Istio"
kubectl apply -f kubernetes/gateway.yaml
kubectl apply -f kubernetes/virtual-service.yaml
kubectl apply -f kubernetes/destination-rule.yaml

echo ""
echo "Развертывание успешно завершено!"
echo "Для доступа к приложению выполните команду:"
echo "kubectl port-forward -n istio-system svc/istio-ingressgateway 8080:80"
echo "Затем откройте http://localhost:8080 в браузере"
echo "Для проверки метрик приложения:"
echo "curl http://localhost:8080/metrics"
echo "Для доступа к Prometheus выполните:"
echo "kubectl port-forward -n journal-system svc/prometheus 9000:9000"
echo "Затем откройте в браузере http://localhost:9000"
echo "Метрики приложения в Prometheus:"
echo "journal_log_requests_total"
echo "Метрики Istio:"
echo "istio_requests_total"
