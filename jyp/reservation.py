# jyp/reservation.py
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List

from jyp.utils import mmdd_to_dt, is_valid_mmdd, is_valid_time_hhmm   # 이미 있는 유틸 재사용
from jyp.templates import 요일표


@dataclass
class ReservationData:
    name: str
    day1: str                  # "MM/DD"
    day1_times: List[str]      # ["07:30", "12:30", ...]
    day2_times: List[str]
    day3_times: List[str]      # 1박2일이면 []
    teams: int                 # 팀 수
    rooms: int                 # 2 or 4
    price: str                 # "123,000" 같은 문자열


def validate(data: ReservationData, is_2n3d: bool) -> list[str]:
    """입력값 검증만 수행(메시지 문자열 리스트 반환)."""
    errors: list[str] = []

    if not is_valid_mmdd(data.day1):
        errors.append("첫 번째 날: MM/DD 형식으로 입력하세요 (예: 08/15).")

    for s in data.day1_times:
        if s and not is_valid_time_hhmm(s):
            errors.append("첫 번째 날: HH:MM 형식 확인")

    for s in data.day2_times:
        if s and not is_valid_time_hhmm(s):
            errors.append("두 번째 날: HH:MM 형식 확인")

    if is_2n3d:
        for s in data.day3_times:
            if s and not is_valid_time_hhmm(s):
                errors.append("세 번째 날: HH:MM 형식 확인")

    if data.teams <= 0:
        errors.append("팀 수: 1 이상의 정수를 입력하세요.")
    if data.rooms not in (2, 4):
        errors.append("룸 수: 2 또는 4만 선택하세요.")

    # 날짜 유효성(2월 30일 등)
    if not errors:
        try:
            mmdd_to_dt(data.day1, datetime.now().year)
        except ValueError as ve:
            errors.append(f"날짜가 올바르지 않습니다: {ve}")

    return errors


def render_text(data: ReservationData, is_2n3d: bool) -> str:
    """예약안내 최종 문자열 생성(기존 문구 유지)."""
    # 연도/요일 계산
    d1 = mmdd_to_dt(data.day1, datetime.now().year)
    d2 = d1 + timedelta(days=1)
    d3 = d1 + timedelta(days=2) if is_2n3d else None

    요일1 = 요일표[d1.strftime("%a")]
    요일2 = 요일표[d2.strftime("%a")]
    요일3 = 요일표[d3.strftime("%a")] if is_2n3d else ""

    둘째날 = d2.strftime("%m/%d")
    셋째날 = d3.strftime("%m/%d") if is_2n3d else ""

    첫날시간들   = ", ".join(t.strip() for t in data.day1_times if t.strip())
    둘째날시간들  = ", ".join(t.strip() for t in data.day2_times if t.strip())
    셋째날시간들  = ", ".join(t.strip() for t in data.day3_times if t.strip()) if is_2n3d else ""

    header_tag = "예약확정 안내"
    팀라인 = f"{data.teams}팀({data.teams*4}명)예약 확정 되었습니다."

    if is_2n3d:
        return f"""[장수CC 2박3일 {header_tag}]
예약자: {data.name}님
■{data.day1}({요일1}) {첫날시간들}
■{둘째날}({요일2}) {둘째날시간들}
■{셋째날}({요일3}) {셋째날시간들}
{팀라인}

[유의사항]
*본 예약은 확정되었으며,
*취소는 전화로만 가능하고,
자동취소는 되지 않습니다.
*2주전 취소부터는 위약발생
*티오프 최소 30분전 내장!!

[이용 요금]
*패키지(1인): {data.price}원
(그린피3일(54홀)+숙박2일+조식2회포함)
※불포함:카트피,캐디피
※팀당 4인플레이 기준

[숙박안내]
*일자: {data.day1}({요일1}), {둘째날}({요일2})
숙소: 장수스테이  {data.teams}객실
{data.rooms}룸타입(방{data.rooms},욕실2,거실1)
★ 객실내 취사 및 흡연 불가

※석식 바베큐 별도신청
 (선착순 마감)
https://www.jangsugolf.com/resort/resort_bbq

[조식안내]
*2일차 라운드전 클럽하우스
※라운드 시작이후 이용불가
※티오프 50분전부터 식사가능
※ 제공 시간은 9시까지  ※

[예약금]
*금 액: {data.teams*30}만원 (팀당30만원)
*은 행:기업은행
*계 좌:232-112996-01-015
*예금주:장수레저(주)
※입금후 확인연락바랍니다.

상기예약은 확정되었습니다.
감사합니다.

-장수골프리조트"""
    else:
        return f"""[장수CC 1박2일 {header_tag}]
예약자: {data.name}님
■{data.day1}({요일1}) {첫날시간들}
■{둘째날}({요일2}) {둘째날시간들}
{팀라인}

[유의사항]
*본 예약은 확정되었으며,
*취소는 전화로만 가능하며,
자동취소는 되지 않습니다.
*2주전 취소부터는 위약발생
*티오프 최소 30분전 내장!!

[이용 요금]
*패키지(1인): {data.price}원
(그린피2일(36홀)+숙박+조식포함)
※불포함:카트피,캐디피
※팀당 4인플레이 기준

[숙박안내]
*일자: {data.day1}({요일1})
숙소: 장수스테이  {data.teams}객실
{data.rooms}룸타입(방{data.rooms},욕실2,거실1)
★ 객실내 취사 및 흡연 불가

※석식 바베큐 별도신청
 (선착순 마감)
https://www.jangsugolf.com/resort/resort_bbq

[조식안내]
*2일차 라운드전 클럽하우스
※라운드 시작이후 이용불가
※티오프 50분전부터 식사가능
※ 제공 시간은 9시까지  ※

[예약금]
*금 액: {data.teams*30}만원 (팀당30만원)
*은 행:기업은행
*계 좌:232-112996-01-015
*예금주:장수레저(주)
※입금후 확인연락바랍니다.

상기예약은 확정되었습니다.
감사합니다.

-장수골프리조트"""
