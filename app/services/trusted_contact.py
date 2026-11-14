"""믿는 사람 연락 기록 (T-40 — F-23 ③).

아이가 홈(Y3)의 연락 버튼으로 전화·문자 앱을 열면 보호자 리포트(G3)에 보일 연락 알림을 남긴다.
알림 항목은 발생 시각과 채널(`call`·`sms`)뿐이다 — 연락처 이름·번호·원문은 넣지 않는다(최소 정보, F-41 ③).
외부 즉시 전달(이메일 등)은 PRD Open Question 9 보류로 하지 않는다.
"""

from collections.abc import Callable
from datetime import datetime
from typing import Literal, Protocol
from uuid import UUID

ContactChannel = Literal["call", "sms"]


class TrustedContactNoticeRepository(Protocol):
    def add_trusted_contact_notice(self, child_id: UUID, channel: ContactChannel, occurred_at: datetime) -> None: ...


class TrustedContactEventService:
    def __init__(self, repository: TrustedContactNoticeRepository, *, clock: Callable[[], datetime]) -> None:
        self._repository = repository
        self._clock = clock

    def record(self, child_id: UUID, channel: ContactChannel) -> None:
        self._repository.add_trusted_contact_notice(child_id, channel, self._clock())
