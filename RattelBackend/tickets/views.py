import logging

from django.conf import settings
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from RattelBackend.mixins import GetDataMixin, ResponseBuilderMixin, FieldValidator
from .models import Ticket, Message
from .serializers import TicketListSerializer, TicketDetailSerializer, MessageSerializer

logger = logging.getLogger(__name__)

_TICKET_ALLOWED_MIMETYPES = ['image/jpeg', 'image/jpg', 'image/png']
_TICKET_ALLOWED_EXTENSIONS = ['jpg', 'jpeg', 'png']
_TICKET_MAX_ATTACHMENT_SIZE = 3 * 1024 * 1024  # 3 MB


class TicketListCreateView(APIView, GetDataMixin, ResponseBuilderMixin, FieldValidator):
    """
    List all tickets for the authenticated user or create a new one.

    Permissions:
        - IsAuthenticated: Must be logged in.

    Throttling:
        - Uses the `tickets` scope -> 200/min.

    GET:
        Returns a paginated list of the user's own tickets, newest first.

        Query Params:
            status (str): Optional — filter by ticket status.

        Returns:
            200 OK:
                - success=True
                - tickets: List of serialized tickets
                - total: Total count of matching tickets

    POST:
        Creates a new ticket with an initial message.
        Expects multipart/form-data so an optional image attachment can be included.

        Body Params:
            subject (str):     Ticket subject (required).
            body (str):        Body of the first message (required).
            category (str):    Optional — one of technical|billing|content|account|other. Default: other.
            priority (str):    Optional — one of low|medium|high|urgent. Default: medium.
            attachment (file): Optional — JPG/PNG image up to 3 MB.

        Returns:
            201 CREATED:
                - success=True
                - message: 'Ticket created.'
                - ticket: Serialized ticket detail

            400 BAD REQUEST:
                - success=False
                - error: -1  Missing/invalid subject or body
                - error: -2  Invalid category or priority value
                - error: -3  Attachment failed validation
    """

    permission_classes = (IsAuthenticated,)
    throttle_scope = 'tickets'

    valid_fields = ('subject', 'body')
    validators = {
        'max_length': 255,
        'sql': True,
        'lookup': True,
        'injection': True,
        'redis': False,
    }

    def get(self, request):
        """Return a list of the authenticated user's tickets."""
        qs = Ticket.objects.filter(user=request.user).order_by('-created_at')

        # Optional status filter
        filter_status = request.query_params.get('status')
        if filter_status:
            if filter_status not in Ticket.StatusChoices.values:
                return self.build_response(
                    status.HTTP_400_BAD_REQUEST,
                    success=False,
                    error=-1,
                    message=f'Invalid status filter. Valid values: {", ".join(Ticket.StatusChoices.values)}',
                )
            qs = qs.filter(status=filter_status)

        serializer = TicketListSerializer(qs, many=True)
        return self.build_response(
            status.HTTP_200_OK,
            success=True,
            message='Successful',
            tickets=serializer.data,
            total=qs.count(),
        )

    def post(self, request):
        """Create a new ticket with an optional initial attachment."""
        # Extract and validate required text fields
        success_extract, result = self.get_data(request, 'subject', 'body')
        if not success_extract:
            return self.build_response(
                status.HTTP_400_BAD_REQUEST,
                success=False,
                error=-1,
                message=result,
            )

        subject = result['subject']
        body = result['body']

        # Security check on text fields
        ok, err = self.validate_string_fields(
            valid_fields=self.valid_fields,
            validators=self.validators,
            subject=subject,
            body=body,
        )
        if not ok:
            return self.build_response(
                status.HTTP_400_BAD_REQUEST,
                success=False,
                error=-1,
                message=err,
            )

        # Validate optional category / priority
        category = request.data.get('category', Ticket.CategoryChoices.OTHER)
        priority = request.data.get('priority', Ticket.PriorityChoices.MEDIUM)

        if category not in Ticket.CategoryChoices.values:
            return self.build_response(
                status.HTTP_400_BAD_REQUEST,
                success=False,
                error=-2,
                message=f'Invalid category. Valid values: {", ".join(Ticket.CategoryChoices.values)}',
            )
        if priority not in Ticket.PriorityChoices.values:
            return self.build_response(
                status.HTTP_400_BAD_REQUEST,
                success=False,
                error=-2,
                message=f'Invalid priority. Valid values: {", ".join(Ticket.PriorityChoices.values)}',
            )

        # Optional attachment validation
        attachment = request.FILES.get('attachment')
        if attachment:
            file_valid, errors = self.validate_uploaded_file(
                attachment,
                max_size=_TICKET_MAX_ATTACHMENT_SIZE,
                allowed_mime_types=_TICKET_ALLOWED_MIMETYPES,
                allowed_extensions=_TICKET_ALLOWED_EXTENSIONS,
            )
            if not file_valid:
                return self.build_response(
                    status.HTTP_400_BAD_REQUEST,
                    success=False,
                    error=-3,
                    message=errors,
                )

        # Create the ticket
        ticket = Ticket.objects.create(
            user=request.user,
            subject=subject,
            category=category,
            priority=priority,
        )

        # Create the initial message
        Message.objects.create(
            ticket=ticket,
            sender=request.user,
            body=body,
            attachment=attachment,
            is_staff_reply=False,
        )

        logger.info(f'User {request.user.pk} created ticket {ticket.pk}.')

        serializer = TicketDetailSerializer(ticket, context={'request': request})
        return self.build_response(
            status.HTTP_201_CREATED,
            success=True,
            message='Ticket created.',
            ticket=serializer.data,
        )


class TicketDetailView(APIView, ResponseBuilderMixin):
    """
    Retrieve a single ticket with all its messages.

    Permissions:
        - IsAuthenticated: Must be logged in.
        - Users can only access their own tickets.

    Throttling:
        - Uses the `tickets` scope -> 200/min.

    GET:
        Returns the full ticket detail including the message thread.

        Returns:
            200 OK:
                - success=True
                - ticket: Full serialized ticket with messages

            403 FORBIDDEN:
                - success=False
                - error: -2  Ticket does not belong to the requesting user

            404 NOT FOUND:
                - success=False
                - error: -1  Ticket not found
    """

    permission_classes = (IsAuthenticated,)
    throttle_scope = 'tickets'

    def _get_ticket(self, ticket_id, user):
        """Fetch and authorise access to a ticket.

        Args:
            ticket_id: UUID primary key of the ticket.
            user: The requesting user.

        Returns:
            Tuple[Ticket | None, Response | None]: The ticket (if authorised) or an error response.
        """
        try:
            ticket = (
                Ticket.objects
                .prefetch_related('messages__sender')
                .get(pk=ticket_id)
            )
        except Ticket.DoesNotExist:
            return None, self.build_response(
                status.HTTP_404_NOT_FOUND,
                success=False,
                error=-1,
                message='Ticket not found.',
            )

        if ticket.user_id != user.pk:
            logger.warning(
                f'User {user.pk} attempted to access ticket {ticket_id} '
                f'owned by user {ticket.user_id}.'
            )
            return None, self.build_response(
                status.HTTP_403_FORBIDDEN,
                success=False,
                error=-2,
                message='You do not have permission to access this ticket.',
            )

        return ticket, None

    def get(self, request, ticket_id):
        """Retrieve a ticket and its full message thread."""
        ticket, error_response = self._get_ticket(ticket_id, request.user)
        if error_response:
            return error_response

        serializer = TicketDetailSerializer(ticket, context={'request': request})
        return self.build_response(
            status.HTTP_200_OK,
            success=True,
            message='Successful',
            ticket=serializer.data,
        )


class TicketCloseView(APIView, ResponseBuilderMixin):
    """
    Close an open ticket.

    Users can close their own tickets when the issue is resolved.
    A closed ticket cannot be submitted to — it must be reopened first.

    Permissions:
        - IsAuthenticated: Must be logged in.

    Throttling:
        - Uses the `tickets` scope -> 200/min.

    POST:
        Returns:
            200 OK:
                - success=True
                - message: 'Ticket closed.'

            400 BAD REQUEST:
                - success=False
                - error: -3  Ticket is already closed

            403 FORBIDDEN:
                - success=False
                - error: -2  Ticket does not belong to the requesting user

            404 NOT FOUND:
                - success=False
                - error: -1  Ticket not found
    """

    permission_classes = (IsAuthenticated,)
    throttle_scope = 'tickets'

    def post(self, request, ticket_id):
        """Close the specified ticket."""
        try:
            ticket = Ticket.objects.get(pk=ticket_id)
        except Ticket.DoesNotExist:
            return self.build_response(
                status.HTTP_404_NOT_FOUND,
                success=False,
                error=-1,
                message='Ticket not found.',
            )

        if ticket.user_id != request.user.pk:
            logger.warning(
                f'User {request.user.pk} attempted to close ticket {ticket_id} '
                f'owned by user {ticket.user_id}.'
            )
            return self.build_response(
                status.HTTP_403_FORBIDDEN,
                success=False,
                error=-2,
                message='You do not have permission to close this ticket.',
            )

        closed = ticket.close()
        if not closed:
            return self.build_response(
                status.HTTP_400_BAD_REQUEST,
                success=False,
                error=-3,
                message='Ticket is already closed.',
            )

        logger.info(f'User {request.user.pk} closed ticket {ticket_id}.')
        return self.build_response(
            status.HTTP_200_OK,
            success=True,
            message='Ticket closed.',
        )


class TicketReopenView(APIView, ResponseBuilderMixin):
    """
    Reopen a previously closed ticket.

    Permissions:
        - IsAuthenticated: Must be logged in.

    Throttling:
        - Uses the `tickets` scope -> 200/min.

    POST:
        Returns:
            200 OK:
                - success=True
                - message: 'Ticket reopened.'

            400 BAD REQUEST:
                - success=False
                - error: -3  Ticket is not closed

            403 FORBIDDEN:
                - success=False
                - error: -2  Ticket does not belong to the requesting user

            404 NOT FOUND:
                - success=False
                - error: -1  Ticket not found
    """

    permission_classes = (IsAuthenticated,)
    throttle_scope = 'tickets'

    def post(self, request, ticket_id):
        """Reopen a closed ticket."""
        try:
            ticket = Ticket.objects.get(pk=ticket_id)
        except Ticket.DoesNotExist:
            return self.build_response(
                status.HTTP_404_NOT_FOUND,
                success=False,
                error=-1,
                message='Ticket not found.',
            )

        if ticket.user_id != request.user.pk:
            logger.warning(
                f'User {request.user.pk} attempted to reopen ticket {ticket_id} '
                f'owned by user {ticket.user_id}.'
            )
            return self.build_response(
                status.HTTP_403_FORBIDDEN,
                success=False,
                error=-2,
                message='You do not have permission to reopen this ticket.',
            )

        reopened = ticket.reopen()
        if not reopened:
            return self.build_response(
                status.HTTP_400_BAD_REQUEST,
                success=False,
                error=-3,
                message='Ticket is not closed.',
            )

        logger.info(f'User {request.user.pk} reopened ticket {ticket_id}.')
        return self.build_response(
            status.HTTP_200_OK,
            success=True,
            message='Ticket reopened.',
        )


class TicketMessageCreateView(APIView, GetDataMixin, ResponseBuilderMixin, FieldValidator):
    """
    Send a new message (reply) to an existing ticket.

    Only the ticket owner can post messages through this endpoint.
    Messages cannot be sent to a closed ticket.

    Permissions:
        - IsAuthenticated: Must be logged in.

    Throttling:
        - Uses the `tickets` scope -> 200/min.

    POST:
        Expects multipart/form-data.

        Body Params:
            body (str):        Message text (required).
            attachment (file): Optional — JPG/PNG image up to 3 MB.

        Returns:
            201 CREATED:
                - success=True
                - message: 'Message sent.'
                - reply: Serialized message

            400 BAD REQUEST:
                - success=False
                - error: -1  Missing/invalid body
                - error: -3  Attachment failed validation
                - error: -4  Ticket is closed

            403 FORBIDDEN:
                - success=False
                - error: -2  Ticket does not belong to the requesting user

            404 NOT FOUND:
                - success=False
                - error: -1  Ticket not found
    """

    permission_classes = (IsAuthenticated,)
    throttle_scope = 'tickets'

    valid_fields = ('body',)
    validators = {
        'max_length': 5000,
        'sql': False,
        'lookup': False,
        'injection': True,
        'redis': False,
    }

    def post(self, request, ticket_id):
        """Post a reply to a ticket thread."""
        # Fetch the ticket
        try:
            ticket = Ticket.objects.get(pk=ticket_id)
        except Ticket.DoesNotExist:
            return self.build_response(
                status.HTTP_404_NOT_FOUND,
                success=False,
                error=-1,
                message='Ticket not found.',
            )

        # Authorisation check
        if ticket.user_id != request.user.pk:
            logger.warning(
                f'User {request.user.pk} attempted to reply to ticket {ticket_id} '
                f'owned by user {ticket.user_id}.'
            )
            return self.build_response(
                status.HTTP_403_FORBIDDEN,
                success=False,
                error=-2,
                message='You do not have permission to reply to this ticket.',
            )

        # Closed tickets cannot receive new messages
        if ticket.status == Ticket.StatusChoices.CLOSED:
            return self.build_response(
                status.HTTP_400_BAD_REQUEST,
                success=False,
                error=-4,
                message='Cannot send a message to a closed ticket. Reopen it first.',
            )

        # Validate body
        success_extract, result = self.get_data(request, 'body')
        if not success_extract:
            return self.build_response(
                status.HTTP_400_BAD_REQUEST,
                success=False,
                error=-1,
                message=result,
            )

        body = result['body']
        ok, err = self.validate_string_fields(
            valid_fields=self.valid_fields,
            validators=self.validators,
            body=body,
        )
        if not ok:
            return self.build_response(
                status.HTTP_400_BAD_REQUEST,
                success=False,
                error=-1,
                message=err,
            )

        # Optional attachment validation
        attachment = request.FILES.get('attachment')
        if attachment:
            file_valid, errors = self.validate_uploaded_file(
                attachment,
                max_size=_TICKET_MAX_ATTACHMENT_SIZE,
                allowed_mime_types=_TICKET_ALLOWED_MIMETYPES,
                allowed_extensions=_TICKET_ALLOWED_EXTENSIONS,
            )
            if not file_valid:
                return self.build_response(
                    status.HTTP_400_BAD_REQUEST,
                    success=False,
                    error=-3,
                    message=errors,
                )

        msg = Message.objects.create(
            ticket=ticket,
            sender=request.user,
            body=body,
            attachment=attachment,
            is_staff_reply=False,
        )

        # Move ticket back to OPEN if it was waiting for a user response
        if ticket.status == Ticket.StatusChoices.WAITING_USER:
            ticket.status = Ticket.StatusChoices.OPEN
            ticket.save(update_fields=['status', 'updated_at'])

        logger.info(
            f'User {request.user.pk} sent message {msg.pk} '
            f'to ticket {ticket_id}.'
        )

        serializer = MessageSerializer(msg, context={'request': request})
        return self.build_response(
            status.HTTP_201_CREATED,
            success=True,
            message='Message sent.',
            reply=serializer.data,
        )
