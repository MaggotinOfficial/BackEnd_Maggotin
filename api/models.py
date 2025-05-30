from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import timedelta
from django.db.models.signals import post_save
from django.dispatch import receiver

User = get_user_model()

class Cycle(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    date = models.DateField()  # Tanggal siklus
    name = models.CharField(max_length=100)  # Nama siklus
    egg_photo = models.ImageField(upload_to='egg_photos/')  # Foto telur maggot
    points = models.IntegerField(default=0)

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

class Waste(models.Model):
    phase = models.ForeignKey(Phase, related_name='wastes', on_delete=models.CASCADE, default=1)  # Hubungkan ke fase
    waste_date = models.DateField(default=timezone.now)  # Tanggal default adalah hari ini
    waste_amount = models.PositiveIntegerField()  # Jumlah sampah yang diolah (gram)
    waste_photo = models.ImageField(upload_to='waste_photos/')  # Foto sampah

    def __str__(self):
        return f"Waste {self.phase.phase_name} - {self.waste_amount} g"

    def display_amount_with_unit(self):
        """
        Mengembalikan jumlah sampah dengan satuan.
        """
        return f"{self.waste_amount} g"
    

class LarvaHarvest(models.Model):
    phase = models.ForeignKey(Phase, related_name='larva_harvests', on_delete=models.CASCADE)  # Hubungkan ke fase
    harvest_date = models.DateField(default=timezone.now)  # Tanggal default adalah hari ini
    total_harvest = models.PositiveIntegerField()  # Total panen maggot (gram)
    total_for_sale = models.PositiveIntegerField()  # Total yang siap jual (gram)
    total_for_breeding = models.PositiveIntegerField()  # Total untuk lanjut bibit (gram)
    total_kasgot = models.PositiveIntegerField()  # Total kasgot (gram)
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
