"""Independent fresh database migration and relational constraint checks."""
from datetime import date
import pytest
from alembic import command
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.autogenerate import compare_metadata
from sqlalchemy import inspect,select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from backend.database import make_engine
from backend.models import Base,ClientModel,UserModel,CampaignModel,MetricModel,AssignmentModel
@pytest.fixture
def migrated(tmp_path,monkeypatch):
 url='sqlite:///'+str(tmp_path/'qa-migrations.sqlite3');monkeypatch.setenv('DATABASE_URL',url)
 config=Config('alembic.ini');command.upgrade(config,'head');command.upgrade(config,'head')
 engine=make_engine(url)
 yield engine
 engine.dispose()
def seed(engine):
 with Session(engine) as s:
  client=ClientModel(id='c1',name='QA',currency='USD');s.add(client);s.flush()
  s.add_all([UserModel(id='u1',name='QA',email='qa@example.com',role='marketer',client_id=None),CampaignModel(id='p1',name='QA search',channel='Google Ads',client_id='c1')]);s.commit()
def metric(**changes):
 data=dict(id='m1',campaign_id='p1',date=date(2026,1,2),spend_minor=1025,revenue_minor=3075,impressions=100,clicks=10,leads=2,sales=1,version=1);data.update(changes);return MetricModel(**data)
def test_fresh_repeat_migration_and_model_parity(migrated):
 names=set(inspect(migrated).get_table_names());assert names=={'alembic_version','clients','users','campaigns','assignments','daily_metrics','sessions','oauth_transactions'}
 with migrated.connect() as conn:assert compare_metadata(MigrationContext.configure(conn),Base.metadata)==[]
 cols={c['name']:str(c['type']) for c in inspect(migrated).get_columns('daily_metrics')}
 assert cols['spend_minor']=='BIGINT' and cols['revenue_minor']=='BIGINT'

def test_orm_relationships_minor_units_and_assignment_unique(migrated):
 seed(migrated)
 with Session(migrated) as s:
  s.add_all([metric(),AssignmentModel(user_id='u1',client_id='c1')]);s.commit()
 with Session(migrated) as s:
  p=s.get(CampaignModel,'p1');assert p.client.currency=='USD' and p.metrics[0].spend_minor==1025
  assert p.metrics[0].created_at and p.metrics[0].updated_at
  assert s.get(UserModel,'u1').assignments[0].client.name=='QA'
  s.add(AssignmentModel(user_id='u1',client_id='c1'))
  with pytest.raises(IntegrityError):s.commit()
  s.rollback();assert len(s.scalars(select(AssignmentModel)).all())==1

@pytest.mark.parametrize('change',[{'campaign_id':'missing'},{'spend_minor':-1},{'clicks':-1},{'version':0}])
def test_metric_fk_and_check_constraints(migrated,change):
 seed(migrated)
 with Session(migrated) as s:
  s.add(metric(**change))
  with pytest.raises(IntegrityError):s.commit()
  s.rollback();assert s.scalars(select(MetricModel)).all()==[]

def test_metric_date_uniqueness_and_user_role_association(migrated):
 seed(migrated)
 with Session(migrated) as s:
  s.add(metric());s.commit();s.add(metric(id='m2'))
  with pytest.raises(IntegrityError):s.commit()
  s.rollback();assert len(s.scalars(select(MetricModel)).all())==1
  s.add(UserModel(id='u2',name='Bad viewer',email='bad@example.com',role='client',client_id=None))
  with pytest.raises(IntegrityError):s.commit()
  s.rollback();assert s.get(UserModel,'u2') is None

def test_downgrade_then_reupgrade(tmp_path,monkeypatch):
 url='sqlite:///'+str(tmp_path/'qa-roundtrip.sqlite3');monkeypatch.setenv('DATABASE_URL',url);config=Config('alembic.ini')
 command.upgrade(config,'head');command.downgrade(config,'base')
 engine=make_engine(url)
 assert set(inspect(engine).get_table_names())=={'alembic_version'}
 engine.dispose();command.upgrade(config,'head');engine=make_engine(url)
 assert 'daily_metrics' in inspect(engine).get_table_names()
 engine.dispose()
