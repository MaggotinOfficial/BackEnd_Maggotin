from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from .models import Article, Cycle, LarvaHarvest, Waste, EggHarvest, Phase, Youtube, Notification    
from .serializers import CycleSerializer, LarvaHarvestSerializer, WasteSerializer, EggHarvestSerializer,PhaseSerializer, ArticleSerializer, YoutubeSerializer, NotificationSerializer

User = get_user_model()

class CycleViewSet(viewsets.ModelViewSet):
    queryset = Cycle.objects.all()
    serializer_class = CycleSerializer
    # permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        """Pastikan user dari request otomatis terhubung ke Cycle yang dibuat."""
        serializer.save(user=self.request.user)  

    @action(detail=True, methods=['post'])
    def add_egg_harvest(self, request, pk=None):
        """Tambahkan Egg Harvest ke Cycle tertentu."""
        cycle = self.get_object()
        serializer = EggHarvestSerializer(data=request.data)
        if serializer.is_valid():
            egg_harvest = serializer.save(cycle=cycle)
            if egg_harvest.total_egg_harvest > 0:
                user = request.user
                """Nambah point untuk user dan box kalau ada yang dipanen"""
                user.save()
                cycle.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

class PhaseViewSet(viewsets.ModelViewSet):
    queryset = Phase.objects.all()
    serializer_class = PhaseSerializer

    @action(detail=True, methods=['post'])
    def add_waste(self, request, pk=None):
        """Tambahkan Waste ke Cycle tertentu."""
        phase = self.get_object()
        serializer = WasteSerializer(data=request.data)
        if serializer.is_valid():
            waste_instance = serializer.save(phase=phase)

            cycle = phase.cycle  # Ambil cycle dari phase
            print(f"[DEBUG] Sebelum Update - Cycle ID: {cycle.id}, Total Waste: {cycle.total_waste}")

            # Update total waste hanya di cycle
            cycle.total_waste += waste_instance.waste_amount
            cycle.save()

            print(f"[DEBUG] Setelah Update - Cycle ID: {cycle.id}, Total Waste: {cycle.total_waste}")

            return Response(serializer.data, status=201)
        
        return Response(serializer.errors, status=400)

    @action(detail=True, methods=['post'])
    def add_larva_harvest(self, request, pk=None):
        phase = self.get_object()

        # Pastikan fase adalah "larva" atau "panen"
        if phase.phase_name != 'larva':
            return Response({"error": "Panen larva hanya bisa dilakukan pada fase larva."}, status=400)

        serializer = LarvaHarvestSerializer(data=request.data)

        if serializer.is_valid():
            larva_harvest = serializer.save(phase=phase)
            if larva_harvest.total_harvest > 0:
                cycle = phase.cycle  # Ambil cycle dari phase

                print(f"[DEBUG] Sebelum Update - Cycle ID: {cycle.id}, Total Harvest: {cycle.total_harvest}, Points: {cycle.points}")

                # Update total harvest hanya di cycle
                cycle.total_harvest += larva_harvest.total_harvest
                cycle.save()

                print(f"[DEBUG] Setelah Update - Cycle ID: {cycle.id}, Total Harvest: {cycle.total_harvest}, Points: {cycle.points}")

                return Response({
                    "message": "Larva Harvest added successfully",
                    "total_harvest": cycle.total_harvest,
                    "points": cycle.points
                }, status=201)
        print(f"[DEBUG] Serializer Errors: {serializer.errors}")
        return Response(serializer.errors, status=400)

class WasteViewSet(viewsets.ModelViewSet):
    queryset = Waste.objects.all()
    serializer_class = WasteSerializer

    def create(self, request, *args, **kwargs):
        """Tambahkan waste dan update total waste di user serta phase."""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            waste = serializer.save()  # Simpan waste

            # Dapatkan phase dari waste
            phase = waste.phase
            user = phase.cycle.user  # User diambil dari cycle yang memiliki phase

            print(f"[DEBUG] Sebelum Update - User: {user.email}, Total Waste: {user.total_waste}")

            # Update total waste user
            user.total_waste += waste.waste_amount
            user.save()

            print(f"[DEBUG] Setelah Update - User: {user.email}, Total Waste: {user.total_waste}")

            return Response(serializer.data, status=201)
        
        return Response(serializer.errors, status=400)

class EggHarvestViewSet(viewsets.ModelViewSet):
    queryset = EggHarvest.objects.all()
    serializer_class = EggHarvestSerializer

class LarvaHarvestViewSet(viewsets.ModelViewSet):
    queryset = LarvaHarvest.objects.all()
    serializer_class = LarvaHarvestSerializer

    def create(self, request, *args, **kwargs):
        """Tambahkan larva harvest dan update total harvest di user."""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            larva_harvest = serializer.save()  # Simpan data harvest

            # Dapatkan phase dari larva_harvest
            phase = larva_harvest.phase
            user = phase.cycle.user  # User diambil dari cycle yang memiliki phase

            print(f"[DEBUG] Sebelum Update - User: {user.email}, Total Harvest: {user.total_harvest}, Points: {user.points}")

            # Update total harvest
            user.total_harvest += larva_harvest.total_harvest
            user.save()

            print(f"[DEBUG] Setelah Update - User: {user.email}, Total Harvest: {user.total_harvest}, Points: {user.points}")

            return Response({
                "message": "Larva Harvest added successfully",
                "total_harvest": user.total_harvest,
                "points": user.points
            }, status=201)

        return Response(serializer.errors, status=400)


class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer

class YoutubeViewSet(viewsets.ModelViewSet):
    queryset = Youtube.objects.all()
    serializer_class = YoutubeSerializer

class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    queryset = Notification.objects.all()
    permission_classes = [IsAuthenticated]  

    def get_queryset(self):
        """Mengembalikan notifikasi hanya untuk pengguna yang sedang login."""
        user = self.request.user
        if user.is_authenticated:
            return Notification.objects.filter(user=user).order_by('-created_at')
        return Notification.objects.none()


    @action(detail=True, methods=['patch'])
    def mark_as_read(self, request, pk=None):
        print(f'Menerima PATCH untuk ID: {pk}')
        print(f'Data request: {request.data}')
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({'status': 'Notification marked as read'})
    
    def list(self, request, *args, **kwargs):
        """Menampilkan daftar notifikasi untuk semua pengguna."""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        print(serializer.data)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        """Membuat notifikasi baru jika user terautentikasi."""
        if not request.user.is_authenticated:
            return Response(
                {"detail": "Anda harus login untuk membuat notifikasi."},
                status=401
            )

        data = request.data.copy()
        data['user'] = request.user.id  # Set user ke ID pengguna yang sedang login

        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)