import django.db.models.deletion
import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("comptes", "0002_alter_medecin_options_alter_patient_options_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="Clinique",
            fields=[
                ("id", models.PositiveSmallIntegerField(default=1, editable=False, primary_key=True, serialize=False)),
                ("nom", models.CharField(default="Clinique NovaHospito", max_length=180)),
                ("telephone", models.CharField(blank=True, max_length=32)),
                ("email", models.EmailField(blank=True, max_length=254)),
                ("adresse", models.CharField(blank=True, max_length=255)),
                ("ville", models.CharField(blank=True, max_length=120)),
                ("pays", models.CharField(blank=True, max_length=120)),
                ("site_web", models.URLField(blank=True)),
                ("modifie_le", models.DateTimeField(auto_now=True)),
            ],
            options={"verbose_name": "Clinique", "verbose_name_plural": "Clinique"},
        ),
        migrations.CreateModel(
            name="Service",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nom", models.CharField(max_length=120, unique=True)),
                ("specialite", models.CharField(blank=True, max_length=120)),
                ("description", models.TextField(blank=True)),
                ("actif", models.BooleanField(default=True)),
                ("cree_le", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ("nom",), "verbose_name": "Service clinique", "verbose_name_plural": "Services cliniques"},
        ),
        migrations.CreateModel(
            name="Salle",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nom", models.CharField(max_length=120)),
                ("code", models.CharField(max_length=32, unique=True)),
                ("capacite", models.PositiveSmallIntegerField(default=1, validators=[django.core.validators.MinValueValidator(1)])),
                ("equipements", models.TextField(blank=True)),
                ("active", models.BooleanField(default=True)),
                ("service", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="salles", to="clinique.service")),
            ],
            options={"ordering": ("code",), "verbose_name": "Salle", "verbose_name_plural": "Salles"},
        ),
        migrations.CreateModel(
            name="MembreEquipe",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nom", models.CharField(max_length=120)),
                ("fonction", models.CharField(max_length=120)),
                ("telephone", models.CharField(blank=True, max_length=32)),
                ("email", models.EmailField(blank=True, max_length=254)),
                ("actif", models.BooleanField(default=True)),
                ("cree_le", models.DateTimeField(auto_now_add=True)),
                ("service", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="membres_equipe", to="clinique.service")),
            ],
            options={"ordering": ("nom",), "verbose_name": "Membre de l’équipe", "verbose_name_plural": "Membres de l’équipe"},
        ),
        migrations.CreateModel(
            name="DisponibiliteMedecin",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("jour", models.PositiveSmallIntegerField(choices=[(0, "Lundi"), (1, "Mardi"), (2, "Mercredi"), (3, "Jeudi"), (4, "Vendredi"), (5, "Samedi"), (6, "Dimanche")])),
                ("heure_debut", models.TimeField()),
                ("heure_fin", models.TimeField()),
                ("actif", models.BooleanField(default=True)),
                ("medecin", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="disponibilites_clinique", to="comptes.medecin")),
                ("salle", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="disponibilites", to="clinique.salle")),
                ("service", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="disponibilites", to="clinique.service")),
            ],
            options={"ordering": ("jour", "heure_debut", "medecin__last_name"), "verbose_name": "Horaire médecin", "verbose_name_plural": "Horaires médecins"},
        ),
    ]
