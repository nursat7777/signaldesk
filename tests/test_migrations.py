from datetime import date
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
import pytest
from backend.database import make_engine
from backend.models import AssignmentModel, CampaignModel, ClientModel, MetricModel, UserModel, SessionModel

@pytest.fixture
def engine(tmp_path,monkeypatch):
    url='sqlite:///'+str(tmp_path/'migrate.sqlite3')
    monkeypatch.setenv('DATABASE_URL',url)
    command.upgrade(Config('alembic.ini'),'head')
    command.upgrade(Config('alembic.ini'),'head')
    engine=make_engine(url)
    yield engine
    engine.dispose()

def seed(session):
    client=ClientModel(id='c1',name='Coffee',currency='KZT',archived=False)
    user=UserModel(id='u1',name='Marketer',email='mark@example.com',role='marketer',enabled=True)
    session.add_all([client,user]);session.flush()
    campaign=CampaignModel(id='p1',client_id='c1',name='Search',channel='Google Ads',archived=False)
    session.add(campaign);session.flush()
    return campaign

def metric(key='m1'):
    return MetricModel(id=key,campaign_id='p1',date=date(2026,1,1),spend_minor=10,revenue_minor=30,impressions=1,clicks=5,leads=0,sales=7,version=1)

def test_fresh_repeat_migration_and_relations(engine):
    assert set(inspect(engine).get_table_names())=={'alembic_version','clients','users','assignments','campaigns','daily_metrics','sessions','oauth_transactions'}
    with Session(engine) as session:
        seed(session)
        session.add_all([AssignmentModel(user_id='u1',client_id='c1'),metric(),SessionModel(token_hash='hash',user_id='u1',csrf='csrf',expires=9999999999)])
        session.commit()
        user=session.get(UserModel,'u1')
        assert user.assignments[0].client.name=='Coffee' and user.sessions[0].csrf=='csrf'
        row=session.get(MetricModel,'m1')
        assert row.campaign.client.currency=='KZT' and row.spend_minor==10
        assert row.created_at is not None

@pytest.mark.parametrize('case',['daily_unique','assignment_unique','foreign_key','negative','role_client'])
def test_constraints_and_rollback(engine,case):
    with Session(engine) as session:
        seed(session);session.add(metric());session.add(AssignmentModel(user_id='u1',client_id='c1'));session.commit()
        if case=='daily_unique':session.add(metric('m2'))
        if case=='assignment_unique':session.add(AssignmentModel(user_id='u1',client_id='c1'))
        if case=='foreign_key':session.add(CampaignModel(id='bad',client_id='absent',name='Bad',channel='Other',archived=False))
        if case=='negative':session.get(MetricModel,'m1').spend_minor=-1
        if case=='role_client':session.get(UserModel,'u1').role='client'
        with pytest.raises(IntegrityError):session.commit()
        session.rollback()
        assert session.get(MetricModel,'m1').spend_minor==10
