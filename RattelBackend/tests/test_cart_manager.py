import pytest
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ImproperlyConfigured


User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username='cartuser',
        name='Cart User',
        phone='09100000001',
        password='testpass123',
    )


@pytest.fixture
def other_user(db):
    return User.objects.create_user(
        username='otheruser',
        name='Other User',
        phone='09100000002',
        password='testpass123',
    )


@pytest.fixture
def course(db):
    from courses.models import Course
    teacher = User.objects.create_user(
        username='teacher1',
        name='Teacher One',
        phone='09100000003',
        password='testpass123',
    )
    return Course.objects.create(
        name='Test Course',
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


@pytest.fixture
def another_course(db, course):
    from courses.models import Course
    return Course.objects.create(
        name='Another Course',
        teacher=course.teacher,
        short_description='Short',
        long_description='Long',
        price=200000,
        new_price=0,
        difficulty='intermediate',
        age_group='adult',
        category='hafeze',
        rating=4,
    )


@pytest.fixture
def cart(user):
    from cart.models import CartItem
    return CartItem.for_user(user)


class TestCartAdd:

    def test_add_new_item(self, cart, course, settings):
        settings.CART_ALLOWED_CONTENT_TYPES = ['courses.course']
        success, status = cart.add('courses', 'course', course.pk)
        assert success is True
        assert status == 'added'

    def test_add_stacks_existing_item(self, cart, course, settings):
        settings.CART_ALLOWED_CONTENT_TYPES = ['courses.course']
        cart.add('courses', 'course', course.pk, quantity=1)
        success, status = cart.add('courses', 'course', course.pk, quantity=2)
        assert success is True
        assert status == 'updated'

        from cart.models import CartItem
        content_type = ContentType.objects.get(app_label='courses', model='course')
        item = CartItem.objects.get(user=cart.user, content_type=content_type, object_id=course.pk)
        assert item.quantity == 3

    def test_add_disallowed_content_type(self, cart, user, settings):
        settings.CART_ALLOWED_CONTENT_TYPES = []
        success, message = cart.add('courses', 'course', 1)
        assert success is False
        assert 'not an allowed' in message

    def test_add_nonexistent_object(self, cart, settings):
        settings.CART_ALLOWED_CONTENT_TYPES = ['courses.course']
        success, message = cart.add('courses', 'course', 999999)
        assert success is False
        assert 'does not exist' in message

    def test_add_invalid_quantity(self, cart, course, settings):
        settings.CART_ALLOWED_CONTENT_TYPES = ['courses.course']
        success, message = cart.add('courses', 'course', course.pk, quantity=0)
        assert success is False
        assert 'non-zero integer' in message

    def test_add_missing_setting_raises(self, cart, course, settings):
        del settings.CART_ALLOWED_CONTENT_TYPES
        with pytest.raises(ImproperlyConfigured):
            cart.add('courses', 'course', course.pk)


class TestCartDecrease:

    def test_decrease_reduces_quantity(self, cart, course, settings):
        settings.CART_ALLOWED_CONTENT_TYPES = ['courses.course']
        cart.add('courses', 'course', course.pk, quantity=3)
        success, status = cart.add('courses', 'course', course.pk, quantity=-1)
        assert success is True
        assert status == 'updated'

        from cart.models import CartItem
        from django.contrib.contenttypes.models import ContentType
        content_type = ContentType.objects.get(app_label='courses', model='course')
        item = CartItem.objects.get(user=cart.user, content_type=content_type, object_id=str(course.pk))
        assert item.quantity == 2

    def test_decrease_to_zero_removes_item(self, cart, course, settings):
        settings.CART_ALLOWED_CONTENT_TYPES = ['courses.course']
        cart.add('courses', 'course', course.pk, quantity=1)
        success, status = cart.add('courses', 'course', course.pk, quantity=-1)
        assert success is True
        assert status == 'removed'
        assert cart.length() == 0

    def test_decrease_below_zero_removes_item(self, cart, course, settings):
        settings.CART_ALLOWED_CONTENT_TYPES = ['courses.course']
        cart.add('courses', 'course', course.pk, quantity=2)
        success, status = cart.add('courses', 'course', course.pk, quantity=-5)
        assert success is True
        assert status == 'removed'
        assert cart.length() == 0

    def test_decrease_item_not_in_cart(self, cart, course, settings):
        settings.CART_ALLOWED_CONTENT_TYPES = ['courses.course']
        success, message = cart.add('courses', 'course', course.pk, quantity=-1)
        assert success is False
        assert 'not found' in message


class TestCartRemove:

    def test_remove_existing_item(self, cart, course, settings):
        settings.CART_ALLOWED_CONTENT_TYPES = ['courses.course']
        cart.add('courses', 'course', course.pk)
        success, status = cart.remove('courses', 'course', course.pk)
        assert success is True
        assert status == 'removed'

    def test_remove_item_not_in_cart(self, cart, course, settings):
        settings.CART_ALLOWED_CONTENT_TYPES = ['courses.course']
        success, message = cart.remove('courses', 'course', course.pk)
        assert success is False
        assert 'not found' in message

    def test_remove_does_not_affect_other_users(self, cart, other_user, course, settings):
        settings.CART_ALLOWED_CONTENT_TYPES = ['courses.course']
        other_cart = __import__('cart.models', fromlist=['CartItem']).CartItem.for_user(other_user)
        other_cart.add('courses', 'course', course.pk)

        success, message = cart.remove('courses', 'course', course.pk)
        assert success is False
        assert other_cart.length() == 1


class TestCartClear:

    def test_clear_removes_all_items(self, cart, course, another_course, settings):
        settings.CART_ALLOWED_CONTENT_TYPES = ['courses.course']
        cart.add('courses', 'course', course.pk)
        cart.add('courses', 'course', another_course.pk)
        deleted = cart.clear()
        assert deleted == 2
        assert cart.length() == 0

    def test_clear_empty_cart(self, cart):
        deleted = cart.clear()
        assert deleted == 0


class TestCartLength:

    def test_length_empty(self, cart):
        assert cart.length() == 0

    def test_length_after_adds(self, cart, course, another_course, settings):
        settings.CART_ALLOWED_CONTENT_TYPES = ['courses.course']
        cart.add('courses', 'course', course.pk)
        cart.add('courses', 'course', another_course.pk)
        assert cart.length() == 2

    def test_length_counts_rows_not_quantity(self, cart, course, settings):
        settings.CART_ALLOWED_CONTENT_TYPES = ['courses.course']
        cart.add('courses', 'course', course.pk, quantity=5)
        assert cart.length() == 1


class TestCartIter:

    def test_iter_yields_cart_items_with_item(self, cart, course, settings):
        settings.CART_ALLOWED_CONTENT_TYPES = ['courses.course']
        cart.add('courses', 'course', course.pk)
        items = list(cart)
        assert len(items) == 1
        assert items[0].item == course

    def test_iter_empty_cart(self, cart):
        assert list(cart) == []
