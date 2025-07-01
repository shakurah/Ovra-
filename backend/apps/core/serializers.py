from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _
from .models import User


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""
    
    password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    confirm_password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )
    
    class Meta:
        model = User
        fields = (
            'email', 'full_name', 'password', 'confirm_password',
            'phone_number', 'profession', 'company_name', 'preferred_language'
        )
        extra_kwargs = {
            'email': {'required': True},
            'full_name': {'required': True},
        }
    
    def validate(self, attrs):
        """Validate password confirmation."""
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({
                'confirm_password': _('Password confirmation does not match.')
            })
        return attrs
    
    def validate_email(self, value):
        """Validate email uniqueness."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                _('A user with this email address already exists.')
            )
        return value
    
    def create(self, validated_data):
        """Create a new user."""
        # Remove confirm_password from validated_data
        validated_data.pop('confirm_password', None)
        
        # Create user with encrypted password
        user = User.objects.create_user(**validated_data)
        return user


class UserLoginSerializer(serializers.Serializer):
    """Serializer for user login."""
    
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        required=True,
        style={'input_type': 'password'}
    )
    
    def validate(self, attrs):
        """Validate user credentials."""
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            user = authenticate(
                request=self.context.get('request'),
                username=email,
                password=password
            )
            
            if not user:
                raise serializers.ValidationError(
                    _('Invalid email or password.'),
                    code='authorization'
                )
            
            if not user.is_active:
                raise serializers.ValidationError(
                    _('User account is disabled.'),
                    code='authorization'
                )
            
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError(
                _('Must include email and password.'),
                code='authorization'
            )


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile information."""
    
    display_name = serializers.ReadOnlyField()
    trial_queries_remaining = serializers.ReadOnlyField()
    has_trial_queries_remaining = serializers.ReadOnlyField()
    
    class Meta:
        model = User
        fields = (
            'id', 'email', 'full_name', 'display_name', 'profile_picture',
            'phone_number', 'profession', 'company_name', 'preferred_language',
            'subscription_type', 'trial_queries_used', 'trial_queries_limit',
            'trial_queries_remaining', 'has_trial_queries_remaining',
            'is_verified', 'created_at', 'last_login'
        )
        read_only_fields = (
            'id', 'email', 'subscription_type', 'trial_queries_used',
            'trial_queries_limit', 'is_verified', 'created_at', 'last_login'
        )


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile."""
    
    class Meta:
        model = User
        fields = (
            'full_name', 'profile_picture', 'phone_number', 
            'profession', 'company_name', 'preferred_language'
        )
    
    def validate_profile_picture(self, value):
        """Validate profile picture file."""
        if value:
            # Check file size (max 5MB)
            if value.size > 5 * 1024 * 1024:
                raise serializers.ValidationError(
                    _('Profile picture must be smaller than 5MB.')
                )
            
            # Check file type
            allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
            if value.content_type not in allowed_types:
                raise serializers.ValidationError(
                    _('Profile picture must be a JPEG, PNG, GIF, or WebP image.')
                )
        
        return value


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing user password."""
    
    old_password = serializers.CharField(
        required=True,
        style={'input_type': 'password'}
    )
    new_password = serializers.CharField(
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    confirm_new_password = serializers.CharField(
        required=True,
        style={'input_type': 'password'}
    )
    
    def validate_old_password(self, value):
        """Validate old password."""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError(
                _('Old password is incorrect.')
            )
        return value
    
    def validate(self, attrs):
        """Validate new password confirmation."""
        if attrs['new_password'] != attrs['confirm_new_password']:
            raise serializers.ValidationError({
                'confirm_new_password': _('New password confirmation does not match.')
            })
        return attrs
    
    def save(self, **kwargs):
        """Save the new password."""
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user
