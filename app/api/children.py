from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel, ConfigDict, StringConstraints

from app.api.dependencies import require_guardian_id
from app.services.children import ChildrenService

router = APIRouter()

GradeValue = Literal["E6", "M1", "M2", "M3", "H1", "H2", "H3"]
NicknameValue = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=20),
]
ConsentVersionValue = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=20),
]
PinValue = Annotated[
    str,
    StringConstraints(min_length=4, max_length=4, pattern=r"^[0-9]{4}$"),
]


class ChildRegistrationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    consent_agreed: bool
    consent_version: ConsentVersionValue
    nickname: NicknameValue
    grade: GradeValue
    pin: PinValue


class ChildRegistrationResponse(BaseModel):
    child_id: UUID
    nickname: str
    grade: GradeValue
    link_code: str


class ChildSummaryResponse(BaseModel):
    child_id: UUID
    nickname: str
    grade: GradeValue


class ChildListResponse(BaseModel):
    children: list[ChildSummaryResponse]


@router.post(
    "/children",
    status_code=status.HTTP_201_CREATED,
    response_model=ChildRegistrationResponse,
)
def register_child(
    payload: ChildRegistrationRequest,
    request: Request,
    guardian_id: UUID = Depends(require_guardian_id),
) -> ChildRegistrationResponse:
    service: ChildrenService = request.app.state.children_service
    child = service.register_child(
        guardian_id=guardian_id,
        consent_agreed=payload.consent_agreed,
        consent_version=payload.consent_version,
        nickname=payload.nickname,
        grade=payload.grade,
        pin=payload.pin,
    )
    return ChildRegistrationResponse(
        child_id=child.child_id,
        nickname=child.nickname,
        grade=child.grade,
        link_code=child.link_code,
    )


@router.get("/children", response_model=ChildListResponse)
def list_children(
    request: Request,
    guardian_id: UUID = Depends(require_guardian_id),
) -> ChildListResponse:
    service: ChildrenService = request.app.state.children_service
    children = service.list_children(guardian_id)
    return ChildListResponse(
        children=[
            ChildSummaryResponse(
                child_id=child.child_id,
                nickname=child.nickname,
                grade=child.grade,
            )
            for child in children
        ]
    )