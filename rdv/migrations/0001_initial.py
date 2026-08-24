
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('comptes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='RendezVous',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('heure', models.TimeField()),
                ('statut', models.CharField(choices=[('attente', 'En attente'), ('confirme', 'ConfirmÃ©'), ('annule', 'AnnulÃ©'), ('termine', 'TerminÃ©')], default='attente', max_length=10)),
                ('type', models.CharField(choices=[('presentiel', 'PrÃ©sentiel'), ('teleconsultation', 'TÃ©lÃ©consultation')], default='presentiel', max_length=20)),
                ('medecin', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rendezvous', to='comptes.medecin')),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rendezvous', to='comptes.patient')),
            ],
        ),
    ]
