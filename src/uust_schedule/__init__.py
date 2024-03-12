"""Ufa University of Science and Technology schedule.

Notes:
    Classroom scheduling is not implemented as there are differences in the approach to parsing html table.
    Schedule endpoints block any IP except Russian ones.

Schedule html table: https://isu.uust.ru/api/new_schedule_api
Schedule json api endpoints: https://gist.github.com/GuFFy12/c31f01713d14d722ca6197c0a5e11637
"""
from __future__ import annotations

import dataclasses
import datetime
import enum
import typing
import urllib.parse

import bs4
import dateutil.tz
import requests

# Time constants. Used to work with the time obtained from the schedule.
TZ_NAME = "Asia/Yekaterinburg"
TZ_INFO = dateutil.tz.gettz(TZ_NAME)


class SemesterTypeNotFoundError(ValueError):
    """Exception for when the semester type cannot be determined."""


class ParticipantType(enum.IntEnum):
    """Enum for participant types."""
    GROUP = 1
    TEACHER = 2
    ROOM = 3


class SemesterType(enum.IntEnum):
    """Enum for semester types.

    Attributes:
        AUTUMN: From start of first September week to December 31.
        SPRING: From December 31 to start of first September.
    """
    AUTUMN = 1
    SPRING = 2


@dataclasses.dataclass(frozen=True, slots=True)
class Event:
    """Represents schedule event dataclass with relevant information.

    Has methods for obtaining additional information such as the daily event sequence number or the teacher's full name.

    Args:
        title: Title of the schedule event.
        event_type: Type of the schedule event. Listed in EventType enum.
        participant: Participant involved in the event (e.g., student group name, teacher short name).
        location: Location where the event takes place.
        comment: Additional comments or information about the event.
        start_datetime: Localized start date and time of the event.
        end_datetime: Localized end date and time of the event.
    """
    title: str
    event_type: str
    participant: str
    location: str
    comment: str
    start_datetime: datetime.datetime
    end_datetime: datetime.datetime

    def get_daily_number(self) -> int:
        """Getting daily event sequence number.

        Returns:
            Daily event sequence number.
        """
        return [
            "08:00",
            "09:35",
            "11:35",
            "13:10",
            "15:10",
            "16:45",
            "18:20",
            "19:55",
            "21:25",
            "22:55",
        ].index(datetime.datetime.strftime(self.start_datetime, "%H:%M")) + 1


class Schedule:
    """Represents a schedule for group or teacher.

    Args:
        participant_type: A number indicating the type of participant.
        participant_id: ID of the participant (student group ID or teacher ID).
        academic_year: Academic year for the schedule.
    """

    def __init__(self, participant_type: ParticipantType | int, participant_id: int, academic_year: int):
        self.participant_type = ParticipantType(participant_type)
        self.participant_id = participant_id
        self.academic_year = academic_year

        self.start_datetime_of_academic_year = self.get_start_datetime_of_academic_year(self.academic_year)

    @staticmethod
    def get_start_datetime_of_academic_year(academic_year: int) -> datetime.datetime:
        """Gets the start datetime of the academic year.

        Args:
            academic_year: The academic year.

        Returns:
            The start datetime of the academic year.
        """
        first_september_datetime_of_academic_year = datetime.datetime(academic_year, 9, 1, tzinfo=TZ_INFO)
        return first_september_datetime_of_academic_year - datetime.timedelta(days=first_september_datetime_of_academic_year.weekday())

    @staticmethod
    def get_semester_type(reference_date: datetime.date | None = None) -> SemesterType:
        """Gets the semester type (AUTUMN or SPRING) based on the current date.

        Args:
            reference_date: The reference datetime.

        Returns:
            The SemesterType enum value.

        Raises:
             SemesterTypeNotFoundError: If code cannot determine a semester type for the given date.
        """
        if reference_date is None:
            reference_date = datetime.datetime.now(tz=TZ_INFO).date()

        start_datetime_of_academic_year = Schedule.get_start_datetime_of_academic_year(reference_date.year)
        start_datetime_of_next_academic_year = Schedule.get_start_datetime_of_academic_year(reference_date.year + 1)

        if reference_date >= start_datetime_of_academic_year.date():
            return SemesterType.AUTUMN
        if reference_date < start_datetime_of_next_academic_year.date():
            return SemesterType.SPRING

        raise SemesterTypeNotFoundError

    def get_events(
            self,
            semester_type: SemesterType | int | None = None,
            *,
            session: requests.Session | None = None,
            base_url: str = "https://isu.uust.ru/",
            request_timeout: int = 60,
    ) -> typing.Generator[Event, None, None]:
        """Fetches and parses the schedule events for the semester.

        Args:
            semester_type: The semester type.
            session: Request session.
            base_url: Url for fetch request.
            request_timeout: Timeout for the HTTP request.

        Returns:
            Schedule events generator.

        Raises:
            requests.exceptions.RequestException: If an HTTP request error occurs.

        Notes:
            Not using getting the schedule via json api because you can't specify the desired semester there.
            The algorithm is not very different when working with json api, the only advantage is that it directly gets the full name of the teacher.
        """
        if session is None:
            session = requests.session()

        semester_type = SemesterType(semester_type or self.get_semester_type())

        fetch_params = {
            "WhatShow": self.participant_type.value,
            "schedule_semestr_id": f"{str(self.academic_year)[-2:]}{semester_type}",
            "weeks": 0,
        }

        if self.participant_type == ParticipantType.GROUP:
            fetch_params["student_group_id"] = self.participant_id
        elif self.participant_type == ParticipantType.TEACHER:
            fetch_params["teacher"] = self.participant_id

        response = session.get(urllib.parse.urljoin(base_url, "api/new_schedule_api"), params=fetch_params, timeout=request_timeout)
        response.raise_for_status()
        soup = bs4.BeautifulSoup(response.text, "html.parser")

        weekday_index = 0
        for row in soup.select("tbody tr"):
            row_columns = row.findAll("td")

            if "dayheader" in row["class"]:
                weekday_index = [
                    "Понедельник",
                    "Вторник",
                    "Среда",
                    "Четверг",
                    "Пятница",
                    "Суббота",
                    "Воскресенье",
                ].index(row_columns[0].text)

            if "noinfo" in row["class"]:
                continue

            start_time, end_time = (list(map(int, time.split(":"))) for time in row_columns[1].text.split("-"))
            start_timedelta = datetime.timedelta(hours=start_time[0], minutes=start_time[1])
            end_timedelta = datetime.timedelta(hours=end_time[0], minutes=end_time[1])
            for week_number in map(int, row_columns[2].text.split()):
                week_timedelta = datetime.timedelta(weeks=week_number - 1, days=weekday_index)
                start_datetime = self.start_datetime_of_academic_year + week_timedelta + start_timedelta
                end_datetime = self.start_datetime_of_academic_year + week_timedelta + end_timedelta

                yield Event(
                    title=row_columns[3].text,
                    event_type=row_columns[4].text,
                    participant=row_columns[5].text,
                    location=row_columns[6].text,
                    comment=row_columns[7].text,
                    start_datetime=start_datetime,
                    end_datetime=end_datetime,
                )
