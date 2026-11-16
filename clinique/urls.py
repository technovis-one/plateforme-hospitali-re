from django.urls import path

from . import views

app_name = "clinique"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("identite/", views.profile, name="profile"),
    path("services/", views.services, name="services"),
    path("services/<int:service_id>/modifier/", views.service_edit, name="service_edit"),
    path("services/<int:service_id>/activer/", views.service_toggle, name="service_toggle"),
    path("equipe/", views.staffing, name="staffing"),
    path("equipe/horaire/<int:schedule_id>/modifier/", views.schedule_edit, name="schedule_edit"),
    path("equipe/membre/<int:member_id>/modifier/", views.team_member_edit, name="team_member_edit"),
    path("salles/", views.rooms, name="rooms"),
    path("salles/<int:room_id>/modifier/", views.room_edit, name="room_edit"),
    path("salles/<int:room_id>/activer/", views.room_toggle, name="room_toggle"),
    path("stocks/", views.stock, name="stock"),
    path("stocks/<int:article_id>/modifier/", views.stock_article_edit, name="stock_article_edit"),
]
