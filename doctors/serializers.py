from django.db.models import Avg, Count, Q
from rest_framework import serializers
from .models import Specialty, Doctor, Schedule


class SpecialtySerializer(serializers.ModelSerializer):
    class Meta:
        model = Specialty
        fields = ('id', 'name', 'description', 'icon')


class ScheduleSerializer(serializers.ModelSerializer):
    day_display = serializers.CharField(source='get_day_of_week_display', read_only=True)

    class Meta:
        model = Schedule
        fields = ('id', 'day_of_week', 'day_display', 'start_time', 'end_time', 'slot_duration')


class DoctorListSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    specialties = SpecialtySerializer(many=True, read_only=True)
    avg_rating = serializers.SerializerMethodField()
    reviews_count = serializers.SerializerMethodField()
    photo = serializers.SerializerMethodField()

    class Meta:
        model = Doctor
        fields = (
            'id', 'full_name', 'specialties', 'experience_years',
            'photo', 'consultation_price', 'is_available',
            'avg_rating', 'reviews_count',
        )

    def get_full_name(self, obj):
        return obj.user.full_name

    def get_photo(self, obj):
        if obj.photo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.photo.url)
            return obj.photo.url
        return obj.photo_url or ''

    def get_avg_rating(self, obj):
        if hasattr(obj, '_avg_rating'):
            return round(obj._avg_rating, 1) if obj._avg_rating else 0
        return round(obj.reviews.filter(is_approved=True).aggregate(
            avg=Avg('rating'))['avg'] or 0, 1)

    def get_reviews_count(self, obj):
        if hasattr(obj, '_reviews_count'):
            return obj._reviews_count
        return obj.reviews.filter(is_approved=True).count()


class DoctorDetailSerializer(DoctorListSerializer):
    schedules = ScheduleSerializer(many=True, read_only=True)

    class Meta(DoctorListSerializer.Meta):
        fields = DoctorListSerializer.Meta.fields + (
            'education', 'bio', 'schedules',
        )


class DoctorCreateSerializer(serializers.ModelSerializer):
    specialty_ids = serializers.PrimaryKeyRelatedField(
        queryset=Specialty.objects.all(), many=True, write_only=True,
    )

    class Meta:
        model = Doctor
        fields = (
            'user', 'specialty_ids', 'experience_years', 'education',
            'bio', 'photo', 'consultation_price',
        )

    def create(self, validated_data):
        specialties = validated_data.pop('specialty_ids')
        doctor = Doctor.objects.create(**validated_data)
        doctor.specialties.set(specialties)
        return doctor
