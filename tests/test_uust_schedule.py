import datetime

from requests_mock.mocker import Mocker
from uust_schedule import TZ_INFO, Event, Schedule, SemesterType


def test_get_start_datetime_of_academic_year() -> None:
    assert datetime.datetime(2023, 8, 28, tzinfo=TZ_INFO) == Schedule.get_start_datetime_of_academic_year(2023)


def test_get_semester_type() -> None:
    assert Schedule.get_semester_type(datetime.date(2023, 8, 28)) == SemesterType.AUTUMN
    assert Schedule.get_semester_type(datetime.date(2024, 8, 25)) == SemesterType.SPRING


def test_get_schedule_events(requests_mock: Mocker) -> None:
    requests_mock.get("https://isu.uust.ru/api/new_schedule_api", text="""<html>
<body>
<table>
<tbody>
<tr class="dayheader"><td>Понедельник</td><td>08:00-09:20</td><td>1</td><td>name0</td><td>event_type0</td><td>fio0</td><td>location0</td><td>comment0</td></tr>
<tr class="noinfo dayheader"><td>Вторник</td></tr>
<tr class="noinfo dayheader"><td>Среда</td></tr>
<tr class="noinfo dayheader"><td>Четверг</td></tr>
<tr class="noinfo dayheader"><td>Пятница</td></tr>
<tr class="noinfo dayheader"><td>Суббота</td></tr>
<tr class="extra"><td></td><td>22:55-23:00</td><td>52</td><td>name1</td><td>event_type1</td><td>fio1</td><td>location1</td><td>comment1</td></tr>
</tbody>
</table>
</body>
</html>""")

    schedule = Schedule(1, 2575, 2023)
    schedule_events = list(schedule.get_events())

    assert Event(
        title="name0",
        event_type="event_type0",
        participant="fio0",
        location="location0",
        comment="comment0",
        start_datetime=datetime.datetime(2023, 8, 28, 8, tzinfo=TZ_INFO),
        end_datetime=datetime.datetime(2023, 8, 28, 9, 20, tzinfo=TZ_INFO),
    ) == schedule_events[0]

    assert Event(
        title="name1",
        event_type="event_type1",
        participant="fio1",
        location="location1",
        comment="comment1",
        start_datetime=datetime.datetime(2024, 8, 24, 22, 55, tzinfo=TZ_INFO),
        end_datetime=datetime.datetime(2024, 8, 24, 23, tzinfo=TZ_INFO),
    ) == schedule_events[1]


def test_get_daily_index() -> None:
    assert Event(
        title="name0",
        event_type="event_type0",
        participant="fio0",
        location="location0",
        comment="comment0",
        start_datetime=datetime.datetime(2023, 8, 28, 8, tzinfo=TZ_INFO),
        end_datetime=datetime.datetime(2023, 8, 28, 9, 20, tzinfo=TZ_INFO),
    ).get_daily_number() == 1
