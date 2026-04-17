from django.db import migrations, models

def populate_code_court(apps, schema_editor):
    Hopital = apps.get_model('hopitaux', 'Hopital')
    for hopital in Hopital.objects.all():
        if not hopital.code_court:
            # Générer un code unique temporaire basé sur l'ID
            hopital.code_court = f"HOSP{hopital.id}"
            hopital.save()

class Migration(migrations.Migration):

    dependencies = [
        ('hopitaux', '0005_hopital_code_court'),
    ]

    operations = [
        migrations.RunPython(populate_code_court),
        migrations.AlterField(
            model_name='hopital',
            name='code_court',
            field=models.CharField(blank=True, help_text="Code court unique (ex: CHUC, HZPN). Utilisé dans les codes d'accès aux résultats.", max_length=10, unique=True, verbose_name='code court'),
        ),
    ]
