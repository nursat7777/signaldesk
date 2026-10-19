from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictInt, StrictStr, field_validator, model_validator

Role = Literal['admin', 'marketer', 'client']
Currency = Literal['KZT', 'USD', 'EUR']
Channel = Literal['Google Ads', 'Meta Ads', 'TikTok Ads', 'Other']
Name = Annotated[StrictStr, Field(min_length=1, max_length=200, pattern=r'.*\S.*')]
Money = Annotated[StrictStr, Field(pattern=r'^(0|[1-9][0-9]{0,11})\.[0-9]{2}$', max_length=15)]
Count = Annotated[StrictInt, Field(ge=0, le=2147483647)]

class Input(BaseModel):
    model_config = ConfigDict(extra='forbid')

class Patch(Input):
    @model_validator(mode='after')
    def nonempty(self):
        if not self.model_fields_set:
            raise ValueError('empty patch')
        # Omitted differs from explicitly null. Null only allowed for client association.
        if any(getattr(self, k) is None and k != 'clientId' for k in self.model_fields_set):
            raise ValueError('null field')
        return self

class ClientCreate(Input):
    name: Name
    currency: Currency

class ClientPatch(Patch):
    name: Name | None = None
    currency: Currency | None = None
    archived: StrictBool | None = None

class CampaignCreate(Input):
    name: Name
    channel: Channel

class CampaignPatch(Patch):
    name: Name | None = None
    archived: StrictBool | None = None

class UserCreate(Input):
    name: Name
    email: StrictStr
    role: Role
    clientId: StrictStr | None

    @field_validator('email')
    @classmethod
    def email_valid(cls, value):
        import re
        if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', value):
            raise ValueError('invalid email')
        return value.lower()

class UserPatch(Patch):
    enabled: StrictBool | None = None
    role: Role | None = None
    clientId: StrictStr | None = None

class Assignments(Input):
    clientIds: list[Annotated[StrictStr, Field(min_length=1)]]

    @field_validator('clientIds')
    @classmethod
    def unique_ids(cls, value):
        if len(value) != len(set(value)):
            raise ValueError('duplicate assignment')
        return value

class MetricWrite(Input):
    spend: Money
    impressions: Count
    clicks: Count
    leads: Count
    sales: Count
    revenue: Money
    version: Annotated[StrictInt, Field(ge=1)] | None = None

    @model_validator(mode='after')
    def present_version(self):
        if 'version' in self.model_fields_set and self.version is None:
            raise ValueError('null version')
        return self
