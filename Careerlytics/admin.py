from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import PlacementCell, PlacementCellStudent, Placement, PlacementActivity

@admin.register(PlacementCell)
class PlacementCellAdmin(admin.ModelAdmin):
    list_display = ['placement_cell_id', 'institution_name', 'email', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['placement_cell_id', 'institution_name', 'email']
    readonly_fields = ['created_at', 'updated_at']
    list_per_page = 20
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('placement_cell_id', 'institution_name', 'email', 'phone')
        }),
        ('Additional Details', {
            'fields': ('address', 'website', 'logo', 'is_active')
        }),
        ('User Account', {
            'fields': ('user',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(PlacementCellStudent)
class PlacementCellStudentAdmin(admin.ModelAdmin):
    list_display = ['student_id', 'name', 'email', 'department', 'year', 'marks_percentage', 'is_placed']
    list_filter = ['is_placed', 'department', 'year', 'placement_cell']
    search_fields = ['student_id', 'name', 'email']
    readonly_fields = ['created_at', 'updated_at']
    list_per_page = 20
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('placement_cell', 'student_id', 'name', 'email', 'phone')
        }),
        ('Academic Details', {
            'fields': ('department', 'year', 'marks_percentage', 'skills', 'resume')
        }),
        ('Placement Status', {
            'fields': ('is_placed', 'company_placed', 'package_offered')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Placement)
class PlacementAdmin(admin.ModelAdmin):
    list_display = ['student', 'company_name', 'job_role', 'package_offered', 'location', 'placement_date', 'is_verified']
    list_filter = ['is_verified', 'placement_date', 'placement_cell']
    search_fields = ['student__name', 'company_name', 'job_role']
    readonly_fields = ['created_at', 'updated_at']
    list_per_page = 20
    
    fieldsets = (
        ('Placement Details', {
            'fields': ('placement_cell', 'student', 'company_name', 'job_role', 'location')
        }),
        ('Offer Details', {
            'fields': ('package_offered', 'placement_date', 'offer_letter', 'is_verified')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(PlacementActivity)
class PlacementActivityAdmin(admin.ModelAdmin):
    list_display = ['title', 'activity_type', 'placement_cell', 'date', 'time', 'current_participants', 'max_participants']
    list_filter = ['activity_type', 'date', 'is_active', 'placement_cell']
    search_fields = ['title', 'description', 'location']
    readonly_fields = ['created_at', 'updated_at']
    list_per_page = 20
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('placement_cell', 'activity_type', 'title', 'description')
        }),
        ('Schedule', {
            'fields': ('date', 'time', 'location')
        }),
        ('Participants', {
            'fields': ('target_audience', 'max_participants', 'current_participants')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
