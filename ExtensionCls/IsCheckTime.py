
from datetime import timezone, timedelta, timedelta as td
from datetime import datetime
from dateutil.relativedelta import relativedelta
class IsCheckTime:
    def __init__(self, nameparking):
        self.NameParking = nameparking

    #Kiem tra thoi gian ke tiep xe duoc vao bai



    def is_expiry_available(self, datetime_registration, datetime_now,years=0, months=0, days=0, hours=0, minutes=0, seconds=0):
        tz_vn = timezone(timedelta(hours=7))

        # Nu datetime_registration naive  gn UTC
        if datetime_registration.tzinfo is None:
            datetime_registration = datetime_registration.replace(tzinfo=timezone.utc)

        # Chuyn datetime_registration v VN timezone
        datetime_registration = datetime_registration.astimezone(tz_vn)

        # Nu datetime_now naive  gn VN timezone
        if datetime_now.tzinfo is None:
            datetime_now = datetime_now.replace(tzinfo=tz_vn)
        else:
             datetime_now = datetime_now.astimezone(tz_vn)

        # Tnh thi gian ht hn
        delta_time = relativedelta(years=years, months=months, days=days,hours=hours, minutes=minutes, seconds=seconds)
        compare_time = (datetime_registration + delta_time) - datetime_now

        if compare_time <= td(0):
            print(f"Ht hn s dng: {-compare_time}")
        else:
            print(f"Cn hn s dng: {compare_time}")

        return compare_time
    
