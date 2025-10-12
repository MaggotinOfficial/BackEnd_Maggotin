from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import timedelta
from django.db.models.signals import post_save
from django.dispatch import receiver

User = get_user_model()

class nameIoT(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class IoTData(models.Model):
    """Data suhu & kelembapan yang dikirim box IoT."""
    iot = models.ForeignKey(nameIoT, related_name='data', on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    temperature = models.FloatField()
    humidity = models.FloatField()

    def __str__(self):
        return f"{self.iot.name} @ {self.timestamp:%Y-%m-%d %H:%M} → {self.temperature}°C / {self.humidity}%"

class Cycle(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    date = models.DateField()  # Tanggal siklus
    name = models.CharField(max_length=100)  # Nama siklus
    egg_photo = models.ImageField(upload_to='egg_photos/')  # Foto telur maggot
    points = models.IntegerField(default=0)
    iot = models.ForeignKey(nameIoT, on_delete=models.SET_NULL, null=True, blank=True, default=None)
    
    def __str__(self):
        return f"Siklus untuk {self.user_id} dengan {self.name} pada {self.date}"
    
class Phase(models.Model):
    PHASE_CHOICES = [
        ('egg', 'Fase Telur'),
        ('larva', 'Fase Larva'),
        ('prepupa', 'Fase Prepupa'),
        ('pupa', 'Fase Pupa'),
        ('bsf', 'Fase BSF'),
        ('harvest', 'Panen'),
    ]
    PHASE_DURATIONS = {
        'egg': 3,
        'larva': 3,
        'prepupa': 10,
        'pupa': 5,
        'bsf': 14
    }

    cycle = models.ForeignKey(Cycle, related_name='phases', on_delete=models.CASCADE)
    phase_name = models.CharField(max_length=50, choices=PHASE_CHOICES)  # Nama fase
    start_date = models.DateField()  # Tanggal mulai fase
    notes = models.TextField(null=True, blank=True)  # Catatan tambahan tentang fase
    emissions = models.FloatField(default=0)

    def calculate_emissions(self):
        """
        Hitung total emissions CO₂e dari semua waste di fase ini.
        Rumus:
            Methane emissions = total_waste (kg) × 0.851
            CO₂e = Methane emissions × 27
        """
        # SEKARANG (basis kg):
        total_waste_kg = sum(w.waste_amount for w in self.wastes.all())
        methane_emissions = total_waste_kg * 0.851
        co2e_emissions = methane_emissions * 27.0
        return round(co2e_emissions, 2)


    def __str__(self):
        return f"{self.phase_name} - {self.cycle.name}"

    def get_end_date(self):
        """Menghitung tanggal akhir fase berdasarkan durasi yang ditentukan."""
        return self.start_date + timedelta(days=self.PHASE_DURATIONS.get(self.phase_name, 0))


def check_and_notify_users_for_phase(phase):
    today = timezone.now().date()
    end_date = phase.get_end_date()
    days_remaining = (end_date - today).days

    if phase.phase_name != 'harvest':
        if days_remaining in [2, 1, 0]:
            check_box_name = phase.cycle.name
            user = phase.cycle.user

            if days_remaining == 0:
                message = f"Check {check_box_name} kamu karena seharusnya sudah memasuki fase baru. Pastikan kamu memeriksa perubahan pada siklusnya."
            else:
                message = f"Check {check_box_name} kamu karena hampir memasuki fase baru. Pastikan kamu memeriksa perubahan pada siklusnya."

            if not Notification.objects.filter(user=user.id, message=message).exists():
                Notification.objects.create(
                    user=user,
                    message=message,
                    cycle=phase.cycle,  # Menyimpan referensi ke Cycle
                    phase=phase  # Menyimpan referensi ke Phase
                )

@receiver(post_save, sender=Phase)
def create_phase_notification(sender, instance, created, **kwargs):
    """Membuat notifikasi ketika fase baru dibuat atau diubah."""
    if created or instance.phase_name in ['egg', 'larva', 'prepupa', 'pupa', 'bsf']:  # Semua fase kecuali 'harvest'
        check_and_notify_users_for_phase(instance)

# Untuk Perhitungan Emisi Larvanya
@receiver(post_save, sender=Phase)
def calculate_emissions_on_larva_end(sender, instance, created, **kwargs):
    if not created and instance.phase_name == 'larva' and instance.emissions == 0:
        today = timezone.now().date()
        if today >= instance.get_end_date():
            # Disconnect the signal temporarily to prevent recursion
            post_save.disconnect(calculate_emissions_on_larva_end, sender=Phase)
            try:
                emissions = instance.calculate_emissions()
                instance.emissions = emissions
                instance.save(update_fields=['emissions'])
            finally:
                # Reconnect the signal
                post_save.connect(calculate_emissions_on_larva_end, sender=Phase)



class Waste(models.Model):
    phase = models.ForeignKey(Phase, related_name='wastes', on_delete=models.CASCADE, default=1)  # Hubungkan ke fase
    waste_date = models.DateField(default=timezone.now)  # Tanggal default adalah hari ini
    waste_amount = models.PositiveIntegerField()  # Jumlah sampah yang diolah (Kg)
    waste_photo = models.ImageField(upload_to='waste_photos/')  # Foto sampah

    def __str__(self):
        return f"Waste {self.phase.phase_name} - {self.waste_amount} Kg"

    def display_amount_with_unit(self):
        """
        Mengembalikan jumlah sampah dengan satuan.
        """
        return f"{self.waste_amount} Kg"
    

class LarvaHarvest(models.Model):
    phase = models.ForeignKey(Phase, related_name='larva_harvests', on_delete=models.CASCADE)  # Hubungkan ke fase
    harvest_date = models.DateField(default=timezone.now)  # Tanggal default adalah hari ini
    total_harvest = models.PositiveIntegerField()  # Total panen maggot (Kgram)
    total_for_sale = models.PositiveIntegerField()  # Total yang siap jual (kgram)
    total_for_breeding = models.PositiveIntegerField()  # Total untuk lanjut bibit (kgram)
    total_kasgot = models.PositiveIntegerField()  # Total kasgot (kgram)
    harvest_photo = models.ImageField(upload_to='harvest_photos/')  # Foto hasil panen

    def __str__(self):
        return f"Panen Larva pada {self.harvest_date} - {self.phase.phase_name}"

    def save(self, *args, **kwargs):
        if self.total_harvest > 0:
            cycle = self.phase.cycle
            user = cycle.user
            cycle.points += 10
            cycle.save()
            if user:
                user.points += 10
                user.save()

        super().save(*args, **kwargs)


class EggHarvest(models.Model):
    cycle = models.ForeignKey(Cycle, related_name='egg_harvests', on_delete=models.CASCADE)
    total_egg_harvest = models.PositiveIntegerField()  # Total panen telur (gram)
    egg_photo = models.ImageField(upload_to='egg_harvest_photos/')  # Foto telur
    harvest_date = models.DateField(default=timezone.now) # Tanggal default adalah hari ini

    def __str__(self):
        return f"Panen telur {self.cycle.name} - {self.total_egg_harvest} g"

    def display_harvest_with_unit(self):
        """
        Mengembalikan total panen dengan satuan.
        """
        return f"{self.total_egg_harvest} g"
    
    def save(self, *args, **kwargs):
        if self.total_egg_harvest > 0:  
            cycle = self.cycle
            user = cycle.user
            cycle.points += 10
            cycle.save()
            if user:
                user.points += 10
                user.save()

        super().save(*args, **kwargs)

class Article(models.Model):
    phase = models.ForeignKey(Phase, related_name='articles', on_delete=models.SET_NULL, null=True, blank=True)  # Relasi ke Phase jadi opsional
    imageUrl = models.URLField()  # URL untuk gambar artikel
    title = models.CharField(max_length=300)
    description = models.TextField()
    author = models.CharField(max_length=150, null=True, blank=True)
    date_published = models.DateField(default = '2025-01-01')

    def __str__(self):
        return self.title


class Youtube(models.Model):
    phase = models.ForeignKey(Phase, related_name='videos', on_delete=models.SET_NULL, null=True, blank=True)  # Relasi ke Phase
    title = models.CharField(max_length=300)
    description = models.TextField(default="Deskripsi video")
    videoId = models.CharField(max_length=100)  # ID video YouTube unik
    channel_name = models.CharField(max_length=150, null=True, blank=True)
    date_published = models.DateField(default="2025-01-01")
    

    def __str__(self):
        return self.title
    
class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications", null=True, blank=True)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    cycle = models.ForeignKey(Cycle, on_delete=models.SET_NULL, null=True, blank=True)
    phase = models.ForeignKey(Phase, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Notification for {self.user.id if self.user else 'Unknown'}: {self.message}"

class SensorData(models.Model):
    # ganti dari:
    # phase = models.ForeignKey(Phase, related_name='sensor_data', on_delete=models.CASCADE, null=True, blank=True)
    cycle = models.ForeignKey(Cycle, related_name='sensor_data', on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    temperature = models.FloatField()
    humidity = models.FloatField()

    def __str__(self):
        return f"Cycle {self.cycle.id} @ {self.timestamp} → Temp: {self.temperature}°C, Humidity: {self.humidity}%"
