from django.contrib import admin
from .models import Cycle, Phase, Waste, LarvaHarvest, EggHarvest, Article, Youtube, Notification


class PhaseInline(admin.TabularInline):
    model = Phase
    extra = 1  # Tambahkan satu form kosong untuk input fase baru
    fields = ['phase_name', 'start_date', 'notes']

@admin.register(Cycle)
class CycleAdmin(admin.ModelAdmin):
    list_display = ['name', 'date', 'egg_photo', 'points']  # Kolom yang tampil di daftar Cycle
    search_fields = ['name']  # Fitur pencarian berdasarkan nama siklus
    list_filter = ['date']  # Fitur filter berdasarkan tanggal
    inlines = [PhaseInline]

class WasteInline(admin.TabularInline):
    model = Waste
    extra = 1  # Tambahkan satu form kosong untuk input data sampah
    fields = ['waste_date', 'waste_amount', 'waste_photo']  # Field yang ditampilkan

@admin.register(Phase)
class PhaseAdmin(admin.ModelAdmin):
    list_display = ['phase_name', 'cycle', 'start_date']  # Kolom di daftar Phase
    search_fields = ['cycle__name', 'phase_name']  # Pencarian berdasarkan nama siklus atau fase
    list_filter = ['phase_name', 'start_date']
    inlines = [WasteInline]

class WasteAdmin(admin.ModelAdmin):
    list_display = ('phase', 'display_amount_with_unit', 'waste_photo')  # Gunakan 'phase' sebagai referensi
    search_fields = ('phase__phase_name', 'waste_amount')  # Sesuaikan dengan model Phase
    list_filter = ('phase',)  # Filter berdasarkan Phase

    def display_amount_with_unit(self, obj):
        # Menampilkan Jumlah Sampah pake Satuan gram
        return f"{obj.waste_amount} g"

    display_amount_with_unit.short_description = "Jumlah Sampah (g)"  # Label kolom di admin

admin.site.register(Waste, WasteAdmin)


class EggHarvestAdmin(admin.ModelAdmin):
    list_display = ('cycle', 'display_harvest_with_unit', 'egg_photo')  # Tampilkan jumlah dengan satuan
    search_fields = ('cycle__name', 'total_egg_harvest')  
    list_filter = ('cycle',)  

    def display_harvest_with_unit(self, obj):
        """
        Metode untuk menampilkan jumlah panen dengan satuan.
        """
        return f"{obj.total_egg_harvest} g"

    display_harvest_with_unit.short_description = "Panen Telur (g)"  # Label kolom di admin

admin.site.register(EggHarvest, EggHarvestAdmin)

@admin.register(LarvaHarvest)
class LarvaHarvestAdmin(admin.ModelAdmin):
    list_display = ['phase', 'harvest_date', 'total_harvest', 'total_for_sale', 'total_for_breeding', 'total_kasgot', 'harvest_photo']
    search_fields = ['phase__phase_name', 'harvest_date']
    list_filter = ['phase', 'harvest_date']

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'date_published', 'phase']
    search_fields = ['title', 'author']
    list_filter = ['date_published', 'phase']


@admin.register(Youtube)
class YoutubeAdmin(admin.ModelAdmin):
    list_display = ['title', 'channel_name', 'date_published', 'videoId', 'phase']
    search_fields = ['title', 'channel_name', 'videoId']
    list_filter = ['date_published', 'phase']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'message', 'is_read', 'created_at', 'cycle', 'phase']
    search_fields = ['user', 'message']
    list_filter = ['is_read', 'created_at']