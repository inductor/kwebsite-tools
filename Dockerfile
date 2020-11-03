FROM python:3.8-alpine
ENV GITHUB_API_TOKEN=your_damn_token
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . .
ENTRYPOINT ["python", "l10n-release.py"]
CMD ["-h"]
