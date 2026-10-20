from django.urls import path
from . import views

app_name = 'library'

urlpatterns = [
    # Reader & catalog
    path('', views.catalog_view, name='catalog'),
    path('book/<int:book_id>/', views.book_detail_view, name='book_detail'),
    path('book/<int:book_id>/reserve/', views.reserve_book_view, name='reserve_book'),
    path('book/<int:book_id>/recommend/', views.recommend_book_view, name='recommend_book'),
    path('reservation/<int:reservation_id>/cancel/', views.cancel_reservation_view, name='cancel_reservation'),
    path('my-books/', views.my_books_view, name='my_books'),

    # Librarian operations
    path('librarian/', views.librarian_cabinet_view, name='librarian_cabinet'),
    path('librarian/export-excel/', views.export_library_excel, name='export_excel'),
    path('librarian/import-catalog/', views.import_catalog_view, name='import_catalog'),
]

