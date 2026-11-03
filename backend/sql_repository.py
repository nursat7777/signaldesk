"""Per-row relational repository with request-scoped transactions, never JSON snapshots."""
from datetime import date, datetime, timezone
from threading import local
import secrets
from sqlalchemy import delete, inspect, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from .core import ApiError, now, token_hash
from .database import make_engine
from .models import AssignmentModel, CampaignModel, ClientModel, MetricModel, OAuthTransactionModel, SessionModel, UserModel
from .reporting import cents, money

MODELS = {'users': UserModel, 'clients': ClientModel, 'campaigns': CampaignModel, 'metrics': MetricModel}

class Transaction:
    def __init__(self, repo): self.repo = repo
    def __enter__(self):
        state=self.repo._local
        if getattr(state,'depth',0)==0:
            state.session=Session(self.repo.engine)
        state.depth=getattr(state,'depth',0)+1
        return self
    def __exit__(self, kind, value, trace):
        state=self.repo._local
        state.depth-=1
        if state.depth:
            return False
        try:
            if kind:
                state.session.rollback()
            else:
                state.session.commit()
        except IntegrityError as exc:
            state.session.rollback()
            raise ApiError(409,'conflict','Concurrent or constraint conflict') from exc
        finally:
            state.session.close()
            del state.session
        return False

class SQLRepository:
    storage='sqlite'
    def __init__(self,url):
        self.engine=make_engine(url)
        self.storage=self.engine.dialect.name
        self._local=local()
        self.lock=Transaction(self)
        tables=set(inspect(self.engine).get_table_names())
        if not {'alembic_version','users','clients','campaigns','daily_metrics','sessions','oauth_transactions','assignments'}<=tables:
            self.engine.dispose()
            raise RuntimeError('Database schema missing: run python -m alembic upgrade head before starting')
    @property
    def db(self):
        return self._local.session
    def _flush(self):
        try:self.db.flush()
        except IntegrityError as exc:
            # Outer transaction rollback preserves prior rows, including failed role/assignment changes.
            raise ApiError(409,'conflict','Concurrent or constraint conflict') from exc
    def _serialize(self, collection, row):
        if row is None:return None
        if collection=='users':
            return dict(id=row.id,email=row.email,name=row.name,role=row.role,enabled=row.enabled,clientId=row.client_id,
                        clientIds=sorted(a.client_id for a in row.assignments),googleSub=row.google_sub)
        if collection=='clients':return dict(id=row.id,name=row.name,currency=row.currency,archived=row.archived)
        if collection=='campaigns':return dict(id=row.id,clientId=row.client_id,name=row.name,channel=row.channel,archived=row.archived)
        return dict(id=row.id,campaignId=row.campaign_id,date=row.date.isoformat(),spend=money(row.spend_minor),
                    revenue=money(row.revenue_minor),impressions=row.impressions,clicks=row.clicks,leads=row.leads,sales=row.sales,version=row.version)
    def get(self,collection,key):return self._serialize(collection,self.db.get(MODELS[collection],key))
    def all(self,collection):return [self._serialize(collection,row) for row in self.db.scalars(select(MODELS[collection]).order_by(MODELS[collection].id)).all()]
    def _values(self,collection,data):
        mapped={}
        for key,value in data.items():
            if key=='clientIds':continue
            key={'clientId':'client_id','googleSub':'google_sub','campaignId':'campaign_id','spend':'spend_minor','revenue':'revenue_minor'}.get(key,key)
            if key in ('spend_minor','revenue_minor'):value=cents(value)
            if key=='date':value=date.fromisoformat(value)
            mapped[key]=value
        return mapped
    def insert(self,collection,row):
        model=MODELS[collection](**self._values(collection,row));self.db.add(model);self._flush()
        if collection=='users':self._assignments(model,row.get('clientIds',[]))
        return self._serialize(collection,model)
    def _assignments(self,user,ids):
        user.assignments=[AssignmentModel(client_id=client_id) for client_id in ids]
        self._flush()
    def update(self,collection,key,changes):
        row=self.db.get(MODELS[collection],key)
        for field,value in self._values(collection,changes).items():setattr(row,field,value)
        if collection=='users' and 'clientIds' in changes:self._assignments(row,changes['clientIds'])
        self._flush()
        return self._serialize(collection,row)
    def bootstrap(self,email):
        if not email:return
        with self.lock:
            if not self.db.scalar(select(UserModel).where(UserModel.email==email)):
                self.insert('users',dict(id=secrets.token_urlsafe(16),email=email,name='Administrator',role='admin',enabled=True,clientId=None,clientIds=[],googleSub=None))
    def create_session(self,user_id,lifetime):
        # Internal helper supports normal authenticated callback and isolated test factories.
        with self.lock:
            token,csrf=secrets.token_urlsafe(32),secrets.token_urlsafe(32)
            self.db.add(SessionModel(token_hash=token_hash(token),user_id=user_id,csrf=csrf,expires=now()+lifetime))
            self._flush()
            return token,csrf
    def session_get(self,digest):
        row=self.db.get(SessionModel,digest)
        return None if row is None else dict(userId=row.user_id,csrf=row.csrf,expires=row.expires)
    def session_delete(self,digest):self.db.execute(delete(SessionModel).where(SessionModel.token_hash==digest))
    def oauth_begin(self,digest,nonce,expires):
        self.db.execute(delete(OAuthTransactionModel).where(OAuthTransactionModel.expires<=now()))
        self.db.add(OAuthTransactionModel(state_hash=digest,nonce=nonce,expires=expires));self._flush()
    def oauth_consume(self,digest):
        # DELETE ... RETURNING is portable to supported modern DBs and atomically consumes one state.
        row=self.db.execute(delete(OAuthTransactionModel).where(OAuthTransactionModel.state_hash==digest).returning(OAuthTransactionModel.nonce,OAuthTransactionModel.expires)).first()
        return None if row is None else dict(nonce=row.nonce,expires=row.expires)
    def save_metric(self,campaign_id,day,values,expected_version):
        condition=(MetricModel.campaign_id==campaign_id,MetricModel.date==date.fromisoformat(day))
        if expected_version is None:
            # Database unique campaign/date covers simultaneous creates across workers.
            return self.insert('metrics',dict(id=secrets.token_urlsafe(16),campaignId=campaign_id,date=day,**values,version=1))
        statement=update(MetricModel).where(*condition,MetricModel.version==expected_version).values(
            **self._values('metrics',values),version=expected_version+1,updated_at=datetime.now(timezone.utc).replace(tzinfo=None))
        result=self.db.execute(statement)
        if result.rowcount!=1:raise ApiError(409,'conflict')
        self.db.expire_all()
        row=self.db.scalar(select(MetricModel).where(*condition))
        return self._serialize('metrics',row)
