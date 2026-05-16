from typing import AnyStr
from .otp import OTP
from RattelBackend.mixins import GetDataMixin, ResponseBuilderMixin
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
import logging


logger = logging.getLogger(__name__)


def start_otp_session_with_sms(
        indicator: str,
        phone: str,
        error_code_start: int | AnyStr,
        **otp_options
) -> Response:
    """
    Starts an OTP session with SMS notification.
    
    Args:
        indicator: The indicator to start the OTP session with. Will be the same on the Verification endpoint.
        phone: The phone number to send the OTP token to.
        error_code_start: Used for error code of each response
        **otp_options: Options you want to pass to the OTP -> encrypted, override, kwargs
        
    Returns:
        restframework.responses.Response: A Response object containing the final result of session.
    """
    
    # Validating error_code_start
    if not isinstance(error_code_start, int):
        raise TypeError(f'Invalid error code start type: {type(error_code_start)}: {error_code_start}')
    
    # Initializing SMS service
    sms = settings.SMS_HANDLER(settings.SMS_PROVIDER, **settings.SMS_SETTINGS)
    
    if not isinstance(indicator, str):
        logger.warning(f'Invalid indicator was passed: {indicator=}')
        return ResponseBuilderMixin.build_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,  # indicator is built by server
            success=False,
            error=error_code_start,
            message='Internal server error. Could not generate an indicator.'
        )
    
    # Initializing OTP
    otp = OTP(indicator)
    
    # Generating a true random token based on the OTP settings
    token = otp.generate_otp_token()
    
    # Tries to start an OTP session with the generated session
    started = otp.start(token=token, **otp_options)
    
    # Failed to start the OTP session because there is another active session
    if not started:
        logger.warning(f'An active OTP session with the same indicator: {indicator} already exists.')
        return ResponseBuilderMixin.build_response(
            status.HTTP_409_CONFLICT,
            success=False,
            error=error_code_start - 1,
            message='An active verification request with this username already exists.'
        )
    
    # If OTP session is started successfully we can now send the token to user
    sent = sms.send(phone, f'Your verification code: {token}')
    
    # Failed to send the token to user. OTP session will be canceled.
    if not sent:
        logger.error('Failed to send verification code. Canceling the OTP session.')
        otp.cancel()
        return ResponseBuilderMixin.build_response(
            status.HTTP_502_BAD_GATEWAY,
            success=False,
            error=error_code_start - 2,
            message='Failed to send verification code'
        )
    
    # Successfully started OTP session and verification sms is sent.
    return ResponseBuilderMixin.build_response(
        status.HTTP_200_OK,
        success=True,
        indicator=indicator,
        message='Verification code sent.'
    )
    