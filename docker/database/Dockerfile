# ==========================
# Database Dockerfile
# ==========================
FROM mysql:9.3

# timezone 데이터 설치
RUN microdnf install -y tzdata \
    && microdnf clean all

COPY /my.cnf /etc/mysql/conf.d/custom.cnf