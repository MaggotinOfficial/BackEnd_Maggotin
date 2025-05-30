from rest_framework import serializers
from .models import *

class CycleSerializer(serializers.ModelSerializer):
    phases = serializers.PrimaryKeyRelatedField(many=True, read_only=True)  # Menambahkan relasi reverse

    class Meta:
        model = Cycle
        fields = ['id', 'date', 'name', 'egg_photo', 'phases', 'user', 'points'] 
        read_only_fields = ['user'] 
    

class PhaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Phase
        fields = ['id', 'cycle', 'phase_name', 'start_date', 'notes', 'articles', 'videos']


class WasteSerializer(serializers.ModelSerializer):
    waste_amount_with_unit = serializers.SerializerMethodField()  # Field tambahan

    class Meta:
        model = Waste
        fields = ['id', 'phase', 'waste_date', 'waste_amount', 'waste_amount_with_unit', 'waste_photo']

    def get_waste_amount_with_unit(self, obj):
        """
        Mengembalikan jumlah sampah dengan satuan gram.
        """
        return f"{obj.waste_amount} g"


class LarvaHarvestSerializer(serializers.ModelSerializer):
    class Meta:
        model = LarvaHarvest
        fields = [
            'id', 'phase', 'harvest_date', 'total_harvest',
            'total_for_sale', 'total_for_breeding', 'total_kasgot', 'harvest_photo'
        ]


class EggHarvestSerializer(serializers.ModelSerializer):
    total_egg_harvest_with_unit = serializers.SerializerMethodField()  # Field tambahan
    # harvest_date_formatted = serializers.DateField(format="%Y-%m-%d")

    class Meta:
        model = EggHarvest
        fields = ['cycle', 'total_egg_harvest', 'total_egg_harvest_with_unit', 'egg_photo', 'harvest_date']

    def get_total_egg_harvest_with_unit(self, obj):
        """
        Mengembalikan total panen telur dengan satuan gram.
        """
        return f"{obj.total_egg_harvest} g"


class ArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = ['id', 'phase', 'imageUrl', 'title', 'description', 'author', 'date_published']


class YoutubeSerializer(serializers.ModelSerializer):
    youtube_url = serializers.SerializerMethodField()

    class Meta:
        model = Youtube
        fields = ['id', 'phase', 'title', 'description' , 'videoId', 'youtube_url', 'channel_name', 'date_published']

    def get_youtube_url(self, obj):
        return f"https://www.youtube.com/watch?v={obj.videoId}"
    

class NotificationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Notification
        fields = ['id', 'user', 'message', 'is_read', 'created_at', 'cycle', 'phase']
        read_only_fields = ['user', 'created_at'] 