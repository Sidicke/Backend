from rest_framework import generics, serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend

from accounts.permissions import IsAdminHopital
from rendezvous.models import RendezVous, Consultation
from resultats.models import DemandeAnalyse

# ──────────────────────────────────────────────
# Sérialiseurs spécifiques pour la supervision
# ──────────────────────────────────────────────

class SPPatientSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    nom_complet = serializers.SerializerMethodField()
    telephone = serializers.CharField(source='user.telephone', required=False, allow_null=True)
    
    def get_nom_complet(self, obj):
        return obj.user.get_full_name()

class SPMedecinSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    nom_complet = serializers.SerializerMethodField()
    
    def get_nom_complet(self, obj):
        return f"Dr. {obj.user.last_name} {obj.user.first_name}".strip()

class SPRendezVousSerializer(serializers.ModelSerializer):
    patient = SPPatientSerializer()
    medecin = SPMedecinSerializer()
    
    class Meta:
        model = RendezVous
        fields = ['id', 'patient', 'medecin', 'date_heure', 'duree', 'statut', 'motif', 'cree_le']

class SPConsultationSerializer(serializers.ModelSerializer):
    rendez_vous = SPRendezVousSerializer()
    
    class Meta:
        model = Consultation
        fields = ['rendez_vous', 'compte_rendu', 'diagnostic', 'prescription', 'date_consultation', 'est_cloture', 'date_cloture']

class SPDemandeAnalyseSerializer(serializers.ModelSerializer):
    patient = SPPatientSerializer(read_only=True)
    laborantin_nom = serializers.SerializerMethodField()
    
    class Meta:
        model = DemandeAnalyse
        fields = ['id', 'patient', 'patient_nom', 'patient_prenom', 'type_analyse', 'statut', 'date_inscription', 'date_cloture', 'laborantin_nom']
        
    def get_laborantin_nom(self, obj):
        if obj.laborantin:
            return obj.laborantin.get_full_name()
        return None

# ──────────────────────────────────────────────
# Vues de Supervision
# ──────────────────────────────────────────────

class SupervisionPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

class AdminHopitalDashboardGlobalView(APIView):
    """
    Statistiques globales pour le dashboard admin de l'hôpital.
    /api/hopitaux/supervision/dashboard/
    """
    permission_classes = [IsAdminHopital]

    def get(self, request):
        hopital_id = request.user.hopital_id
        
        # RDV Stats
        rdvs = RendezVous.objects.filter(medecin__user__hopital_id=hopital_id)
        rdv_total = rdvs.count()
        rdv_attente = rdvs.filter(statut='en_attente').count()
        rdv_confirme = rdvs.filter(statut='confirme').count()
        rdv_termine = rdvs.filter(statut='termine').count()
        rdv_annule = rdvs.filter(statut__in=['annule', 'refuse']).count()
        
        # Consultations Stats
        consultations = Consultation.objects.filter(rendez_vous__medecin__user__hopital_id=hopital_id)
        consultation_total = consultations.count()
        consultation_cloture = consultations.filter(est_cloture=True).count()
        consultation_en_cours = consultations.filter(est_cloture=False).count()
        
        # Labo Stats
        analyses = DemandeAnalyse.objects.filter(hopital_id=hopital_id)
        analyse_total = analyses.count()
        analyse_en_cours = analyses.filter(statut='en_cours').count()
        analyse_cloture = analyses.filter(statut='cloture').count()
        
        return Response({
            "rendezvous": {
                "total": rdv_total,
                "en_attente": rdv_attente,
                "confirmes": rdv_confirme,
                "termines": rdv_termine,
                "annules_refuses": rdv_annule
            },
            "consultations": {
                "total": consultation_total,
                "cloturees": consultation_cloture,
                "en_cours": consultation_en_cours
            },
            "laboratoire": {
                "total_demandes": analyse_total,
                "en_cours": analyse_en_cours,
                "terminees": analyse_cloture
            }
        })


class AdminHopitalRendezVousListView(generics.ListAPIView):
    """
    Supervision des RDV de l'hôpital.
    /api/hopitaux/supervision/rendezvous/
    """
    serializer_class = SPRendezVousSerializer
    permission_classes = [IsAdminHopital]
    pagination_class = SupervisionPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['statut']
    
    def get_queryset(self):
        hopital_id = self.request.user.hopital_id
        return RendezVous.objects.filter(
            medecin__user__hopital_id=hopital_id
        ).select_related('patient__user', 'medecin__user').order_by('-date_heure')


class AdminHopitalConsultationListView(generics.ListAPIView):
    """
    Supervision des consultations avec détail du rendu.
    /api/hopitaux/supervision/consultations/
    """
    serializer_class = SPConsultationSerializer
    permission_classes = [IsAdminHopital]
    pagination_class = SupervisionPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['est_cloture']
    
    def get_queryset(self):
        hopital_id = self.request.user.hopital_id
        return Consultation.objects.filter(
            rendez_vous__medecin__user__hopital_id=hopital_id
        ).select_related('rendez_vous__patient__user', 'rendez_vous__medecin__user').order_by('-date_consultation')


class AdminHopitalLaboratoireListView(generics.ListAPIView):
    """
    Supervision du pôle laboratoire.
    /api/hopitaux/supervision/laboratoire/
    """
    serializer_class = SPDemandeAnalyseSerializer
    permission_classes = [IsAdminHopital]
    pagination_class = SupervisionPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['statut']
    
    def get_queryset(self):
        hopital_id = self.request.user.hopital_id
        return DemandeAnalyse.objects.filter(
            hopital_id=hopital_id
        ).select_related('patient__user', 'laborantin').order_by('-date_inscription')


class AdminHopitalPatientParcoursView(APIView):
    """
    Supervision unifiée : l'histoire complète d'un patient dans cet hôpital.
    /api/hopitaux/supervision/patient/<int:patient_id>/parcours/
    """
    permission_classes = [IsAdminHopital]

    def get(self, request, patient_id):
        from accounts.models import Patient
        hopital_id = request.user.hopital_id
        
        # Vérification si le patient existe
        try:
            patient = Patient.objects.get(id=patient_id)
        except Patient.DoesNotExist:
            return Response({"error": "Patient introuvable"}, status=404)
        
        # Obtenir les RDV
        rdvs = RendezVous.objects.filter(
            patient_id=patient_id, 
            medecin__user__hopital_id=hopital_id
        ).select_related('medecin__user', 'consultation', 'pre_enregistrement').order_by('date_heure')
        
        parcours = []
        
        for rdv in rdvs:
            item = {
                "type": "rendez_vous",
                "id": rdv.id,
                "date": rdv.date_heure,
                "statut": rdv.statut,
                "medecin": f"Dr. {rdv.medecin.user.last_name}",
            }
            parcours.append(item)
            
            # Si le patient a soumis un préenregistrement
            if hasattr(rdv, 'pre_enregistrement'):
                parcours.append({
                    "type": "pre_enregistrement",
                    "id": rdv.pre_enregistrement.rendez_vous_id,
                    "date": rdv.pre_enregistrement.soumis_le,
                    "symptomes": rdv.pre_enregistrement.symptomes_principaux,
                    "lie_au_rdv": rdv.id
                })
                
            # Si le RDV a mené à une consultation
            if hasattr(rdv, 'consultation'):
                parcours.append({
                    "type": "consultation",
                    "id": rdv.consultation.rendez_vous_id,
                    "date": rdv.consultation.date_consultation,
                    "diagnostic": rdv.consultation.diagnostic,
                    "prescription_presente": bool(rdv.consultation.prescription),
                    "est_cloture": rdv.consultation.est_cloture,
                    "lie_au_rdv": rdv.id
                })
                
        # Ajouter les analyses labo pour ce patient dans cet hôpital
        analyses = DemandeAnalyse.objects.filter(
            patient_id=patient_id, hopital_id=hopital_id
        ).select_related('resultat').order_by('date_inscription')
        
        for ana in analyses:
            parcours.append({
                "type": "demande_analyse",
                "id": ana.id,
                "date": ana.date_inscription,
                "type_analyse": ana.type_analyse,
                "statut": ana.statut
            })
            if hasattr(ana, 'resultat') and ana.resultat:
                parcours.append({
                    "type": "resultat_labo",
                    "id": ana.resultat.id,
                    "date": ana.resultat.date_depot,
                    "titre": ana.resultat.titre,
                    "code_acces": ana.resultat.code_acces,
                    "lie_a_analyse": ana.id
                })
                
        # Trier l'historique complet par date pour créer la chronologie
        parcours_chronologique = sorted(parcours, key=lambda x: x['date'])
        
        return Response({
            "patient": {
                "id": patient.id,
                "nom_complet": patient.user.get_full_name(),
                "email": patient.user.email
            },
            "hopital_id": hopital_id,
            "chronologie": parcours_chronologique
        })
