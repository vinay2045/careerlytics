from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import UserRegistration
from .utils import link_student_to_placement_cell

@receiver(post_save, sender=UserRegistration)
def sync_student_on_save(sender, instance, created, **kwargs):
    """
    Signal to automatically link a student to a placement cell upon registration
    or update their data in PlacementCellStudent when UserRegistration is updated.
    """
    if instance.user_type == 'student':
        if created:
            try:
                success, msg = link_student_to_placement_cell(instance)
                if success:
                    print(f"Signal: Linked {instance.userid} to placement cell: {msg}")
                else:
                    print(f"Signal: Failed to link {instance.userid} to placement cell: {msg}")
            except Exception as e:
                print(f"Signal: Error linking student to placement cell: {e}")
        else:
            # Sync update to existing PlacementCellStudent
            from Careerlytics.models import PlacementCellStudent
            try:
                pcs = PlacementCellStudent.objects.filter(student_id=instance.student_id).first()
                if pcs:
                    pcs.marks_percentage = instance.academic_marks if instance.academic_marks is not None else 0.0
                    pcs.backlog = instance.backlog
                    pcs.year = int(instance.year) if instance.year and (isinstance(instance.year, int) or (isinstance(instance.year, str) and instance.year.isdigit())) else pcs.year
                    pcs.department = instance.branch if instance.branch else pcs.department
                    pcs.save()
                    print(f"Signal: Updated PlacementCellStudent for {instance.userid}")
            except Exception as e:
                print(f"Signal: Error syncing student update: {e}")
