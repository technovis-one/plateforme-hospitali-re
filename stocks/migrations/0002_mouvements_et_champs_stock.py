import django.core.validators
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


def snapshot_existing_stock(apps, schema_editor):
    Medicament = apps.get_model("stocks", "Medicament")
    MouvementStock = apps.get_model("stocks", "MouvementStock")
    for article in Medicament.objects.using(schema_editor.connection.alias).filter(quantite_stock__gt=0).iterator():
        MouvementStock.objects.using(schema_editor.connection.alias).create(
            article_id=article.pk,
            type_mouvement="entree",
            quantite=article.quantite_stock,
            motif="Solde initial avant mise en place du journal",
        )


class Migration(migrations.Migration):
    dependencies = [
        ("stocks", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name="medicament",
            name="date_peremption",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="medicament",
            name="categorie",
            field=models.CharField(choices=[("medicament", "Médicament"), ("consommable", "Consommable médical"), ("materiel", "Matériel")], default="medicament", max_length=20),
        ),
        migrations.AddField(
            model_name="medicament",
            name="unite",
            field=models.CharField(default="unité", max_length=32),
        ),
        migrations.AddField(
            model_name="medicament",
            name="actif",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="medicament",
            name="cree_le",
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="medicament",
            name="modifie_le",
            field=models.DateTimeField(auto_now=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.CreateModel(
            name="MouvementStock",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("type_mouvement", models.CharField(choices=[("entree", "Entrée"), ("sortie", "Sortie")], max_length=10)),
                ("quantite", models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1)])),
                ("motif", models.CharField(max_length=180)),
                ("cree_le", models.DateTimeField(auto_now_add=True)),
                ("article", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="mouvements", to="stocks.medicament")),
                ("cree_par", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="mouvements_stock", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ("-cree_le", "-pk"), "verbose_name": "Mouvement de stock", "verbose_name_plural": "Mouvements de stock"},
        ),
        migrations.RunPython(snapshot_existing_stock, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name="medicament",
            constraint=models.CheckConstraint(condition=models.Q(("quantite_stock__gte", 0)), name="stock_quantite_non_negative"),
        ),
        migrations.AddConstraint(
            model_name="medicament",
            constraint=models.CheckConstraint(condition=models.Q(("seuil_alerte__gte", 0)), name="stock_seuil_non_negative"),
        ),
        migrations.AddConstraint(
            model_name="mouvementstock",
            constraint=models.CheckConstraint(condition=models.Q(("quantite__gt", 0)), name="stock_mouvement_quantite_positive"),
        ),
        migrations.AlterModelOptions(
            name="medicament",
            options={"ordering": ("nom",), "verbose_name": "Article de stock", "verbose_name_plural": "Articles de stock"},
        ),
    ]
