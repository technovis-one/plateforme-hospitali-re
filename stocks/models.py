from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F
from django.utils import timezone


class Medicament(models.Model):
    TYPE_MEDICAMENT = "medicament"
    TYPE_CONSOMMABLE = "consommable"
    TYPE_MATERIEL = "materiel"
    TYPE_CHOICES = (
        (TYPE_MEDICAMENT, "Médicament"),
        (TYPE_CONSOMMABLE, "Consommable médical"),
        (TYPE_MATERIEL, "Matériel"),
    )

    nom = models.CharField(max_length=150)
    quantite_stock = models.PositiveIntegerField(default=0)
    seuil_alerte = models.PositiveIntegerField(default=10)
    date_peremption = models.DateField(null=True, blank=True)
    categorie = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_MEDICAMENT)
    unite = models.CharField(max_length=32, default="unité")
    actif = models.BooleanField(default=True)
    cree_le = models.DateTimeField(auto_now_add=True)
    modifie_le = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("nom",)
        verbose_name = "Article de stock"
        verbose_name_plural = "Articles de stock"
        constraints = [
            models.CheckConstraint(condition=models.Q(quantite_stock__gte=0), name="stock_quantite_non_negative"),
            models.CheckConstraint(condition=models.Q(seuil_alerte__gte=0), name="stock_seuil_non_negative"),
        ]

    @property
    def est_en_alerte(self):
        return self.quantite_stock <= self.seuil_alerte

    @property
    def est_perime(self):
        return self.date_peremption is not None and self.date_peremption < timezone.localdate()

    def __str__(self):
        return self.nom


class Prescription(models.Model):
    consultation = models.ForeignKey('dossier.Consultation', on_delete=models.CASCADE)
    medicament = models.ForeignKey(Medicament, on_delete=models.CASCADE)
    quantite = models.PositiveIntegerField(default=1)
    posologie = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.medicament} x{self.quantite} ({self.consultation})"


class MouvementStock(models.Model):
    ENTREE = "entree"
    SORTIE = "sortie"
    TYPE_CHOICES = ((ENTREE, "Entrée"), (SORTIE, "Sortie"))

    article = models.ForeignKey(Medicament, on_delete=models.PROTECT, related_name="mouvements")
    type_mouvement = models.CharField(max_length=10, choices=TYPE_CHOICES)
    quantite = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    motif = models.CharField(max_length=180)
    cree_par = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="mouvements_stock")
    cree_le = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-cree_le", "-pk")
        verbose_name = "Mouvement de stock"
        verbose_name_plural = "Mouvements de stock"
        constraints = [
            models.CheckConstraint(condition=models.Q(quantite__gt=0), name="stock_mouvement_quantite_positive"),
        ]

    def __str__(self):
        return f"{self.get_type_mouvement_display()} {self.quantite} {self.article.unite} — {self.article}"
