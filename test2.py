from datetime import datetime, timedelta

now = datetime.now()
print(now)

one_hour = timedelta(seconds=3600)
print(now-one_hour)