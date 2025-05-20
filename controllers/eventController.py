import datetime
from mongoConnection import db
from datetime import timedelta

events = db["events"]


class EventController:
    def getNextEvents(self):
        start_hour = datetime.datetime.now()
        end_hour = start_hour + datetime.timedelta(hours=3)

        filteredEvents = events.find(
            {"datetime": {"$gte": start_hour, "$lte": end_hour}, "notified": False}
        )
        return filteredEvents

    def convert_to_time(self, time_str):
        # Remove any extra spaces and lowercase the string
        time_str = time_str.strip().lower()

        # Parse the time string
        try:
            return datetime.strptime(time_str, "%I%p").time()
        except ValueError:
            return datetime.strptime(time_str, "%I:%M%p").time()

    def make_date_from_str(self, date_str):
        weekdays = {
            "monday": 0,
            "tuesday": 1,
            "wednesday": 2,
            "thursday": 3,
            "friday": 4,
            "saturday": 5,
            "sunday": 6,
        }

        if "at" in date_str:
            time = self.convert_to_time(date_str.split("at")[1].strip())
            if "today" in date_str:
                date_str = datetime.now().isoformat()
            elif "tomorrow" in date_str:
                date_str = (datetime.now() + timedelta(days=1)).isoformat()
            elif "next week" in date_str:
                date_str = (datetime.now() + timedelta(weeks=1)).isoformat()
            else:
                date = date_str.split("at")[0].strip()
                if (
                    "next" in date
                    and len(date.split(" ")) > 1
                    and date.split(" ")[1].lower() in weekdays
                ):

                    today = datetime.now()
                    current_weekday = today.weekday()

                    target_weekday = weekdays[date.split(" ")[1].lower()]
                    days_until_next = (target_weekday - current_weekday + 7) % 7

                    if days_until_next == 0:
                        days_until_next = 7

                    date_str = (
                        datetime.now() + timedelta(days=days_until_next)
                    ).isoformat()
        else:
            date = datetime.fromisoformat(date_str)
            time = date.time()
        if not date.year >= datetime.now().year:
            date = date.replace(
                year=datetime.now().year,
                hour=time.hour,
                minute=time.minute,
                second=0,
                microsecond=0,
            )

        return date
