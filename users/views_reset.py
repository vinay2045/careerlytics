
def reset_password(request):
    if request.method == 'POST':
        step = request.POST.get('step')
        
        if step == '1':
            userid = request.POST.get('userid', '').strip()
            email = request.POST.get('email', '').strip()
            
            # Find user by User ID or Student ID, AND matching Email
            user = UserRegistration.objects.filter(
                (Q(userid=userid) | Q(student_id=userid)) & Q(email=email)
            ).first()
            
            if user:
                # User found, move to step 2
                return render(request, 'resetpassword.html', {'step': 2, 'user_pk': user.pk})
            else:
                messages.error(request, "User not found with provided ID and Email.")
                return render(request, 'resetpassword.html', {'step': 1})
                
        elif step == '2':
            user_pk = request.POST.get('user_pk')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            
            if new_password != confirm_password:
                messages.error(request, "Passwords do not match.")
                return render(request, 'resetpassword.html', {'step': 2, 'user_pk': user_pk})
            
            try:
                user = UserRegistration.objects.get(pk=user_pk)
                
                # Update UserRegistration password
                user.password = new_password
                user.save()
                
                # Update subtype model password to keep in sync
                if user.user_type == 'student':
                    student = Student.objects.filter(userid=user.userid).first()
                    if student:
                        student.password = new_password
                        student.save()
                elif user.user_type == 'non_student':
                    non_student = NonStudent.objects.filter(userid=user.userid).first()
                    if non_student:
                        non_student.password = new_password
                        non_student.save()
                        
                messages.success(request, "Password reset successfully! Please login with your new password.")
                return redirect('users:user_login')
            except UserRegistration.DoesNotExist:
                messages.error(request, "User not found.")
                return redirect('users:reset_password')
                
    # GET request
    return render(request, 'resetpassword.html', {'step': 1})
