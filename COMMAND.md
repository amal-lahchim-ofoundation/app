## Commands

### Run app with reload
```
hypercorn app:app --bind 0.0.0.0:5000 --reload

```

### Run celery workers in background
```
celery -A app3.celery_app worker --loglevel=info
```