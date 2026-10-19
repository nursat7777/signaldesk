"""Domain REST operations. Repository reads/writes stay behind a replaceable boundary."""
from datetime import date, datetime
from zoneinfo import ZoneInfo
import secrets
from fastapi import APIRouter, Depends, Query, Request, Response
from .auth import current_session, mutation_session, require_admin
from .core import ApiError, public_user
from .schemas import Assignments, CampaignCreate, CampaignPatch, ClientCreate, ClientPatch, MetricWrite, UserCreate, UserPatch


def parse_day(value):
    try:
        parsed = date.fromisoformat(value)
        if parsed.isoformat() != value:
            raise ValueError()
        return parsed
    except ValueError:
        raise ApiError(422, 'invalidDate')


def date_range(start, end):
    parse_day(start)
    parse_day(end)
    if start > end:
        raise ApiError(422, 'dateRange')


def entity(repo, collection, key):
    row = repo.get(collection, key)
    if row is None:
        raise ApiError(404, 'notFound')
    return row


def access(repo, user, client_id, write=False):
    # Resolve current account and grants inside the write/read transaction too.
    user = entity(repo, 'users', user['id'])
    if not user['enabled']:
        raise ApiError(403, 'forbidden')
    if user['role'] == 'client' and (write or user['clientId'] != client_id):
        raise ApiError(403, 'forbidden')
    if user['role'] == 'marketer' and client_id not in user['clientIds']:
        raise ApiError(403, 'forbidden')
    return entity(repo, 'clients', client_id)


def client_metrics(repo, client_id, start=None, end=None):
    ids = {p['id'] for p in repo.all('campaigns') if p['clientId'] == client_id}
    return sorted([m for m in repo.all('metrics') if m['campaignId'] in ids and
                   (start is None or start <= m['date'] <= end)], key=lambda m: (m['date'], m['campaignId']))


def router():
    api = APIRouter()

    @api.get('/api/clients', operation_id='listClients')
    def list_clients(request: Request, auth=Depends(current_session)):
        repo = request.app.state.repo
        with repo.lock:
            user = entity(repo, 'users', auth[0]['id'])
            if not user['enabled']:
                raise ApiError(403, 'forbidden')
            return [c for c in repo.all('clients') if user['role'] == 'admin' or
                    user['role'] == 'marketer' and c['id'] in user['clientIds'] or
                    user['role'] == 'client' and c['id'] == user['clientId']]

    @api.post('/api/clients', status_code=201, operation_id='createClient')
    def create_client(data: ClientCreate, request: Request, auth=Depends(mutation_session)):
        repo = request.app.state.repo
        with repo.lock:
            require_admin(entity(repo, 'users', auth[0]['id']))
            return repo.insert('clients', dict(id=secrets.token_urlsafe(16), name=data.name.strip(), currency=data.currency, archived=False))

    @api.patch('/api/clients/{clientId}', operation_id='updateClient')
    def update_client(clientId: str, data: ClientPatch, request: Request, auth=Depends(mutation_session)):
        repo = request.app.state.repo
        with repo.lock:
            require_admin(entity(repo, 'users', auth[0]['id']))
            client = entity(repo, 'clients', clientId)
            changes = data.model_dump(exclude_unset=True)
            if 'currency' in changes and changes['currency'] != client['currency'] and client_metrics(repo, clientId):
                raise ApiError(409, 'currencyLocked')
            if 'name' in changes:
                changes['name'] = changes['name'].strip()
            return repo.update('clients', clientId, changes)

    @api.get('/api/clients/{clientId}/campaigns', operation_id='listCampaigns')
    def list_campaigns(clientId: str, request: Request, auth=Depends(current_session)):
        repo = request.app.state.repo
        with repo.lock:
            access(repo, auth[0], clientId)
            return [c for c in repo.all('campaigns') if c['clientId'] == clientId]

    @api.post('/api/clients/{clientId}/campaigns', status_code=201, operation_id='createCampaign')
    def create_campaign(clientId: str, data: CampaignCreate, request: Request, auth=Depends(mutation_session)):
        repo = request.app.state.repo
        with repo.lock:
            client = access(repo, auth[0], clientId, True)
            if client['archived']:
                raise ApiError(409, 'archived')
            return repo.insert('campaigns', dict(id=secrets.token_urlsafe(16), clientId=clientId, name=data.name.strip(), channel=data.channel, archived=False))

    @api.patch('/api/campaigns/{campaignId}', operation_id='updateCampaign')
    def update_campaign(campaignId: str, data: CampaignPatch, request: Request, auth=Depends(mutation_session)):
        repo = request.app.state.repo
        with repo.lock:
            campaign = entity(repo, 'campaigns', campaignId)
            client = access(repo, auth[0], campaign['clientId'], True)
            if client['archived']:
                raise ApiError(409, 'archived')
            changes = data.model_dump(exclude_unset=True)
            if 'name' in changes:
                changes['name'] = changes['name'].strip()
            return repo.update('campaigns', campaignId, changes)

    @api.get('/api/clients/{clientId}/metrics', operation_id='listMetrics')
    def list_metrics(clientId: str, request: Request, start: str = Query(alias='from'), end: str = Query(alias='to'), auth=Depends(current_session)):
        repo = request.app.state.repo
        with repo.lock:
            access(repo, auth[0], clientId)
            date_range(start, end)
            return client_metrics(repo, clientId, start, end)

    @api.put('/api/campaigns/{campaignId}/metrics/{date}', operation_id='saveMetric')
    def save_metric(campaignId: str, date: str, data: MetricWrite, request: Request, auth=Depends(mutation_session)):
        repo = request.app.state.repo
        with repo.lock:
            campaign = entity(repo, 'campaigns', campaignId)
            client = access(repo, auth[0], campaign['clientId'], True)
            if client['archived'] or campaign['archived']:
                raise ApiError(409, 'archived')
            if parse_day(date) > datetime.now(ZoneInfo('Asia/Almaty')).date():
                raise ApiError(422, 'futureDate')
            return repo.save_metric(campaignId, date, data.model_dump(exclude={'version'}), data.version)

    @api.get('/api/users', operation_id='listUsers')
    def list_users(request: Request, auth=Depends(current_session)):
        repo = request.app.state.repo
        with repo.lock:
            require_admin(entity(repo, 'users', auth[0]['id']))
            return [public_user(u) for u in repo.all('users')]

    @api.post('/api/users', status_code=201, operation_id='createUser')
    def create_user(data: UserCreate, request: Request, auth=Depends(mutation_session)):
        repo = request.app.state.repo
        with repo.lock:
            require_admin(entity(repo, 'users', auth[0]['id']))
            if any(u['email'] == data.email for u in repo.all('users')):
                raise ApiError(409, 'duplicateEmail')
            if data.role == 'client' and (not data.clientId or not repo.get('clients', data.clientId)):
                raise ApiError(422, 'required')
            user = repo.insert('users', dict(id=secrets.token_urlsafe(16), name=data.name.strip(), email=data.email,
                role=data.role, clientId=data.clientId if data.role == 'client' else None, clientIds=[], enabled=True, googleSub=None))
            return public_user(user)

    @api.patch('/api/users/{userId}', operation_id='updateUser')
    def update_user(userId: str, data: UserPatch, request: Request, auth=Depends(mutation_session)):
        repo = request.app.state.repo
        with repo.lock:
            require_admin(entity(repo, 'users', auth[0]['id']))
            if userId == auth[0]['id']:
                raise ApiError(409, 'selfDisable')
            old = entity(repo, 'users', userId)
            changes = data.model_dump(exclude_unset=True)
            merged = {**old, **changes}
            if merged['role'] == 'client':
                if not merged['clientId'] or not repo.get('clients', merged['clientId']):
                    raise ApiError(422, 'required')
            else:
                changes['clientId'] = None
            if merged['role'] != old['role']:
                changes['clientIds'] = []
            return public_user(repo.update('users', userId, changes))

    @api.put('/api/users/{userId}/assignments', status_code=204, operation_id='setAssignments')
    def assignments(userId: str, data: Assignments, request: Request, auth=Depends(mutation_session)):
        repo = request.app.state.repo
        with repo.lock:
            require_admin(entity(repo, 'users', auth[0]['id']))
            user = entity(repo, 'users', userId)
            if user['role'] != 'marketer' or any(not repo.get('clients', c) for c in data.clientIds):
                raise ApiError(422, 'invalidAssignment')
            repo.update('users', userId, {'clientIds': data.clientIds})
        return Response(status_code=204)
    return api
