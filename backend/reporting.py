"""Exact base aggregation, ratios derived only after summing."""
from fastapi import APIRouter, Depends, Query, Request
from .auth import current_session
from .domain import access, client_metrics, date_range

COUNTS = ('impressions', 'clicks', 'leads', 'sales')
CHANNELS = ('Google Ads', 'Meta Ads', 'TikTok Ads', 'Other')


def cents(amount):
    whole, fraction = amount.split('.')
    return int(whole) * 100 + int(fraction)


def money(value):
    return f'{value // 100}.{value % 100:02d}'


def aggregate(rows):
    total = {key: sum(row[key] for row in rows) for key in COUNTS}
    spend = sum(cents(row['spend']) for row in rows)
    revenue = sum(cents(row['revenue']) for row in rows)
    return {**total, 'spend': money(spend), 'revenue': money(revenue),
            'ctr': total['clicks'] / total['impressions'] * 100 if total['impressions'] else None,
            'cpc': spend / 100 / total['clicks'] if total['clicks'] else None,
            'cpl': spend / 100 / total['leads'] if total['leads'] else None,
            'roas': revenue / spend if spend else None}


def router():
    api = APIRouter()

    @api.get('/api/clients/{clientId}/report', operation_id='getReport')
    def get_report(clientId: str, request: Request, start: str = Query(alias='from'),
                   end: str = Query(alias='to'), auth=Depends(current_session)):
        repo = request.app.state.repo
        with repo.lock:
            client = access(repo, auth[0], clientId)
            date_range(start, end)
            rows = client_metrics(repo, clientId, start, end)
            campaigns = {c['id']: c for c in repo.all('campaigns') if c['clientId'] == clientId}
            dates = sorted({r['date'] for r in rows})
            return {'clientId': clientId, 'currency': client['currency'], 'from': start, 'to': end,
                    'totals': aggregate(rows),
                    'daily': [{'date': day, 'totals': aggregate([r for r in rows if r['date'] == day])} for day in dates],
                    'channels': [{'channel': channel, 'totals': aggregate(channel_rows)} for channel in CHANNELS
                                 if (channel_rows := [r for r in rows if campaigns[r['campaignId']]['channel'] == channel])]}
    return api
