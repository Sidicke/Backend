from datetime import datetime, timedelta, time, date

from django.utils import timezone

from .models import Disponibilite, RendezVous


def generer_creneaux(medecin, date_debut, date_fin):
    """
    Génère les créneaux libres d'un médecin sur une période donnée.
    Prend en compte les plages récurrentes, les exceptions et les indisponibilités.
    Retourne une liste de dict : [{'date': ..., 'heure_debut': ..., 'heure_fin': ...}, ...]
    """
    duree = medecin.duree_rdv_default
    creneaux = []

    # Récupérer toutes les disponibilités actives du médecin
    disponibilites = Disponibilite.objects.filter(medecin=medecin, is_active=True)
    recurrentes = disponibilites.filter(type='recurrent')
    exceptions = disponibilites.filter(type='exception')
    indisponibilites = disponibilites.filter(type='indisponible')

    # Récupérer les RDV déjà pris (non annulés/refusés) sur la période
    rdvs_pris = RendezVous.objects.filter(
        medecin=medecin,
        date_heure__date__gte=date_debut,
        date_heure__date__lte=date_fin,
    ).exclude(
        statut__in=['annule', 'refuse']
    )

    def est_dans_rdv(slot_debut, slot_fin):
        for rdv in rdvs_pris:
            rdv_debut = rdv.date_heure
            rdv_fin = rdv.date_heure + timedelta(minutes=rdv.duree)
            # Overlap: slot starts before rdv ends AND slot ends after rdv starts
            if slot_debut < rdv_fin and slot_fin > rdv_debut:
                return True
        return False

    # Dates d'indisponibilité (ponctuelles)
    dates_indisponibles = {}
    for indispo in indisponibilites:
        if indispo.date_specifique:
            if indispo.date_specifique not in dates_indisponibles:
                dates_indisponibles[indispo.date_specifique] = []
            dates_indisponibles[indispo.date_specifique].append(
                (indispo.heure_debut, indispo.heure_fin)
            )

    # Parcourir chaque jour de la période
    jour_courant = date_debut
    while jour_courant <= date_fin:
        # Ne pas proposer de créneaux dans le passé
        maintenant = timezone.now()
        if jour_courant < maintenant.date():
            jour_courant += timedelta(days=1)
            continue

        # 1=lundi ... 7=dimanche (isoweekday)
        jour_iso = jour_courant.isoweekday()

        # Collecter les plages pour ce jour
        plages_du_jour = []

        # Plages récurrentes
        for plage in recurrentes:
            if plage.jour_semaine == jour_iso:
                plages_du_jour.append((plage.heure_debut, plage.heure_fin))

        # Plages exceptionnelles (ajoutent des créneaux pour ce jour)
        for exc in exceptions:
            if exc.date_specifique == jour_courant:
                plages_du_jour.append((exc.heure_debut, exc.heure_fin))

        # Plages d'indisponibilité pour ce jour
        indispos_jour = dates_indisponibles.get(jour_courant, [])

        # Découper chaque plage en créneaux
        for heure_debut, heure_fin in plages_du_jour:
            debut = timezone.make_aware(datetime.combine(jour_courant, heure_debut))
            fin = timezone.make_aware(datetime.combine(jour_courant, heure_fin))

            creneau_debut = debut
            while creneau_debut + timedelta(minutes=duree) <= fin:
                creneau_fin = creneau_debut + timedelta(minutes=duree)

                # Vérifier si ce créneau est dans une plage d'indisponibilité
                est_indisponible = False
                for indispo_debut, indispo_fin in indispos_jour:
                    indispo_dt_debut = timezone.make_aware(datetime.combine(jour_courant, indispo_debut))
                    indispo_dt_fin = timezone.make_aware(datetime.combine(jour_courant, indispo_fin))
                    if creneau_debut < indispo_dt_fin and creneau_fin > indispo_dt_debut:
                        est_indisponible = True
                        break

                # Vérifier si le créneau est occupé
                est_occupe = est_dans_rdv(creneau_debut, creneau_fin)

                # Vérifier que le créneau est dans le futur
                est_futur = creneau_debut > maintenant

                if not est_indisponible and not est_occupe and est_futur:
                    creneaux.append({
                        'date': jour_courant.isoformat(),
                        'heure_debut': creneau_debut.strftime('%H:%M'),
                        'heure_fin': creneau_fin.strftime('%H:%M'),
                    })

                creneau_debut = creneau_fin

        jour_courant += timedelta(days=1)

    return creneaux

