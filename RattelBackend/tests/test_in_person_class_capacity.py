import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username='ipcuser',
        name='IPC User',
        phone='09100000010',
        password='testpass123',
    )


@pytest.fixture
def other_user(db):
    return User.objects.create_user(
        username='ipcother',
        name='IPC Other',
        phone='09100000011',
        password='testpass123',
    )


@pytest.fixture
def time_range(db):
    from in_person_class.models import TimeRange
    return TimeRange.objects.create(label='شنبه ۱۰-۱۲')


def _make_class(capacity=None, **overrides):
    from in_person_class.models import InPersonClass
    from datetime import date, timedelta

    defaults = {
        'title': 'Test Class',
        'short_description': 'desc',
        'price': 100000,
        'new_price': 0,
        'start_date': date.today(),
        'end_date': date.today() + timedelta(days=30),
        'capacity': capacity,
    }
    defaults.update(overrides)
    return InPersonClass.objects.create(**defaults)


@pytest.fixture
def unlimited_class(db, time_range):
    ipc = _make_class(capacity=None)
    ipc.available_times.add(time_range)
    return ipc


@pytest.fixture
def limited_class(db, time_range):
    ipc = _make_class(capacity=1)
    ipc.available_times.add(time_range)
    return ipc


@pytest.fixture
def registration(db, limited_class, time_range):
    from in_person_class.models import InPersonClassRegistration
    return InPersonClassRegistration.objects.create(
        in_person_class=limited_class,
        time_range=time_range,
        start_date=limited_class.start_date,
        end_date=limited_class.end_date,
        price=limited_class.price,
        new_price=limited_class.new_price,
    )


@pytest.fixture
def unlimited_registration(db, unlimited_class, time_range):
    from in_person_class.models import InPersonClassRegistration
    return InPersonClassRegistration.objects.create(
        in_person_class=unlimited_class,
        time_range=time_range,
        start_date=unlimited_class.start_date,
        end_date=unlimited_class.end_date,
        price=unlimited_class.price,
        new_price=unlimited_class.new_price,
    )


class TestCapacityProperties:

    def test_unlimited_when_capacity_none(self, unlimited_registration):
        assert unlimited_registration.is_full is False
        assert unlimited_registration.seats_remaining is None

    def test_seats_remaining_decrements(self, registration, user):
        assert registration.seats_remaining == 1
        assert registration.is_full is False

        registration.bought_by.add(user)
        assert registration.seats_remaining == 0
        assert registration.is_full is True

    def test_seats_remaining_clamps_at_zero(self, registration, user, other_user):
        registration.bought_by.add(user, other_user)
        assert registration.seats_remaining == 0
        assert registration.registered_count == 2


class TestRegisterViewCapacity:

    def test_register_rejects_full_slot(self, registration, user, other_user):
        registration.bought_by.add(user)

        client = APIClient()
        client.force_authenticate(other_user)
        response = client.post(
            reverse('in_person_class:register'),
            {
                'class_id': str(registration.in_person_class.pk),
                'time_range_id': registration.time_range.pk,
            },
        )

        assert response.status_code == 400
        assert response.data['success'] is False
        assert isinstance(response.data['message'], str)
        assert 'ظرفیت' in response.data['message']

    def test_register_allows_existing_owner_of_full_slot(self, registration, user):
        registration.bought_by.add(user)

        client = APIClient()
        client.force_authenticate(user)
        response = client.post(
            reverse('in_person_class:register'),
            {
                'class_id': str(registration.in_person_class.pk),
                'time_range_id': registration.time_range.pk,
            },
        )

        assert response.status_code == 200
        assert response.data['success'] is True

    def test_register_succeeds_when_not_full(self, limited_class, time_range, user):
        client = APIClient()
        client.force_authenticate(user)
        response = client.post(
            reverse('in_person_class:register'),
            {
                'class_id': str(limited_class.pk),
                'time_range_id': time_range.pk,
            },
        )

        assert response.status_code == 200
        assert response.data['success'] is True


class TestCartManagerCapacity:

    def test_cart_add_blocked_for_full_registration(self, registration, user, other_user, settings):
        from cart.models import CartItem

        settings.CART_ALLOWED_CONTENT_TYPES = ['in_person_class.inpersonclassregistration']
        registration.bought_by.add(user)

        cart = CartItem.for_user(other_user)
        success, message = cart.add(
            'in_person_class', 'inpersonclassregistration', registration.pk
        )

        assert success is False
        assert 'ظرفیت' in message

    def test_cart_add_allowed_when_not_full(self, registration, other_user, settings):
        from cart.models import CartItem

        settings.CART_ALLOWED_CONTENT_TYPES = ['in_person_class.inpersonclassregistration']

        cart = CartItem.for_user(other_user)
        success, message = cart.add(
            'in_person_class', 'inpersonclassregistration', registration.pk
        )

        assert success is True
        assert message == 'added'

    def test_cart_add_unaffected_for_models_without_capacity_hook(self, user, settings):
        from cart.models import CartItem
        from courses.models import Course

        settings.CART_ALLOWED_CONTENT_TYPES = ['courses.course']

        teacher = User.objects.create_user(
            username='ipcteacher',
            name='IPC Teacher',
            phone='09100000012',
            password='testpass123',
        )
        course = Course.objects.create(
            name='Capacity Regression Course',
            teacher=teacher,
            short_description='Short',
            long_description='Long',
            price=100000,
            new_price=0,
            difficulty='beginner',
            age_group='adult',
            category='naghme',
            rating=5,
        )

        cart = CartItem.for_user(user)
        success, message = cart.add('courses', 'course', course.pk)

        assert success is True
        assert message == 'added'
