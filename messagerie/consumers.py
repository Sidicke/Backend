"""Consumer WebSocket pour la messagerie temps réel."""

import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer


class ChatConsumer(AsyncWebsocketConsumer):
    """Consumer pour le chat temps réel d'une consultation."""

    async def connect(self):
        self.consultation_id = self.scope['url_route']['kwargs']['consultation_id']
        self.room_group_name = f'chat_{self.consultation_id}'

        user = self.scope.get('user')
        if not user or user.is_anonymous:
            await self.close()
            return

        # Vérifier que l'utilisateur est participant de la consultation et qu'elle n'est pas clôturée
        participant_status = await self.check_participant(user, self.consultation_id)
        if not participant_status['is_participant'] or participant_status['is_cloture']:
            await self.close()
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        contenu = data.get('contenu', '').strip()
        if not contenu:
            return

        user = self.scope['user']
        msg = await self.save_message(user, self.consultation_id, contenu)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'id': msg['id'],
                'consultation': msg['consultation'],
                'expediteur': msg['expediteur'],
                'expediteur_nom': msg['expediteur_nom'],
                'destinataire': msg['destinataire'],
                'destinataire_nom': msg['destinataire_nom'],
                'contenu': msg['contenu'],
                'date_envoi': msg['date_envoi'],
                'lu': False,
                'piece_jointe': None,
            }
        )

    async def chat_message(self, event):
        event_copy = dict(event)
        event_copy.pop('type', None)
        await self.send(text_data=json.dumps(event_copy))

    @database_sync_to_async
    def check_participant(self, user, consultation_id):
        from rendezvous.models import Consultation
        try:
            consultation = Consultation.objects.select_related(
                'rendez_vous__patient__user', 'rendez_vous__medecin__user'
            ).get(pk=consultation_id)
            rdv = consultation.rendez_vous
            return {
                'is_participant': user.pk in (rdv.patient.user_id, rdv.medecin.user_id),
                'is_cloture': consultation.est_cloture
            }
        except Consultation.DoesNotExist:
            return {'is_participant': False, 'is_cloture': False}

    @database_sync_to_async
    def save_message(self, user, consultation_id, contenu):
        from rendezvous.models import Consultation
        from .models import Message
        from notifications.utils import create_notification

        consultation = Consultation.objects.select_related(
            'rendez_vous__patient__user', 'rendez_vous__medecin__user'
        ).get(pk=consultation_id)
        
        if consultation.est_cloture:
            raise Exception("La consultation est clôturée. Envoi de message impossible.")

        rdv = consultation.rendez_vous

        if user.pk == rdv.patient.user_id:
            destinataire = rdv.medecin.user
        else:
            destinataire = rdv.patient.user

        message = Message.objects.create(
            consultation=consultation,
            expediteur=user,
            destinataire=destinataire,
            contenu=contenu,
        )

        create_notification(
            user=destinataire,
            type='nouveau_message',
            message=f"Nouveau message de {user.get_full_name()}.",
            lien=f"/api/messages/?consultation={consultation_id}",
        )

        return {
            'id': message.id,
            'consultation': consultation_id,
            'expediteur': user.pk,
            'expediteur_nom': user.get_full_name(),
            'destinataire': destinataire.pk,
            'destinataire_nom': destinataire.get_full_name(),
            'contenu': contenu,
            'date_envoi': message.date_envoi.isoformat(),
        }
