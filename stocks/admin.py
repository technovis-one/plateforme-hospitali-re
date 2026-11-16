from django.contrib import admin

from .models import Medicament, MouvementStock, Prescription


@admin.register(Medicament)
class MedicamentAdmin(admin.ModelAdmin):
    list_display = ("nom", "categorie", "quantite_stock", "unite", "seuil_alerte", "date_peremption", "actif")
    list_filter = ("categorie", "actif")
    search_fields = ("nom",)


@admin.register(MouvementStock)
class MouvementStockAdmin(admin.ModelAdmin):
    list_display = ("cree_le", "article", "type_mouvement", "quantite", "motif", "cree_par")
    list_filter = ("type_mouvement", "cree_le")
    search_fields = ("article__nom", "motif", "cree_par__email")
    readonly_fields = ("cree_le",)


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ("consultation", "medicament", "quantite", "posologie")
    search_fields = ("medicament__nom",)
