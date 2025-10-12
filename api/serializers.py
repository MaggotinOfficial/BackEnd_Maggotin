from rest_framework import serializers
from .models import *

class IoTDataSerializer(serializers.ModelSerializer):
    iot_name = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = IoTData
        fields = ['id', 'iot', 'iot_name', 'timestamp', 'temperature', 'humidity']
        read_only_fields = ['timestamp']

    def create(self, validated_data):
        # Jika user kirim iot_name, cari atau buat nameIoT
        iot_name = validated_data.pop('iot_name', None)
        if iot_name:
            iot_obj, _ = nameIoT.objects.get_or_create(name=iot_name)
            validated_data['iot'] = iot_obj
        return super().create(validated_data)


class nameIoTSerializer(serializers.ModelSerializer):
    data = IoTDataSerializer(many=True, read_only=True)

    class Meta:
        model = nameIoT
        fields = ['id', 'name', 'description', 'data']

class CycleSerializer(serializers.ModelSerializer):
    phases = serializers.PrimaryKeyRelatedField(many=True, read_only=True)  # Menambahkan relasi reverse
    iot_data = serializers.SerializerMethodField()

    class Meta:
        model = Cycle
        fields = ['id', 'date', 'name', 'egg_photo', 'phases', 'user', 'points', 'iot', 'iot_data'] 
        read_only_fields = ['user'] 

    def get_iot_data(self, obj):
        # hanya tampilkan data IoT kalau fase LARVA sedang aktif
        larva_exists = obj.phases.filter(phase_name='larva').exists()
        if larva_exists and obj.iot:
            latest_data = obj.iot.data.order_by('-timestamp')[:5]  # ambil 5 data terakhir
            return IoTDataSerializer(latest_data, many=True).data
        return None
    

class PhaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Phase
        fields = ['id', 'cycle', 'phase_name', 'start_date', 'notes', 'articles', 'videos', 'emissions']


class WasteSerializer(serializers.ModelSerializer):
    waste_amount_with_unit = serializers.SerializerMethodField()  # Field tambahan

    class Meta:
        model = Waste
        fields = ['id', 'phase', 'waste_date', 'waste_amount', 'waste_amount_with_unit', 'waste_photo']

    def get_waste_amount_with_unit(self, obj):
        """
        Mengembalikan jumlah sampah dengan satuan gram.
        """
        return f"{obj.waste_amount} kg"
        return f"{obj.waste_amount} kg"


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


class SensorDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = SensorData
        fields = ['id', 'cycle', 'timestamp', 'temperature', 'humidity']



class PhaseEmissionsSerializer(serializers.ModelSerializer):
    articles = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    videos = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    total_waste_gram = serializers.SerializerMethodField()  # Total waste dalam gram
    total_waste_kg = serializers.SerializerMethodField()    # Total waste dalam kg

    class Meta:
        model = Phase
        fields = [
            'id', 'cycle', 'phase_name', 'start_date', 'notes', 
            'articles', 'videos', 'emissions',
            'total_waste_gram', 'total_waste_kg'  # Tambahkan field baru
        ]

    # def get_total_waste_gram(self, obj):
    #     """Hitung total waste dalam gram."""
    #     return sum(w.waste_amount for w in obj.wastes.all()) * 1000

    def get_total_waste_kg(self, obj):
        return round(sum(w.waste_amount for w in obj.wastes.all()), 2)