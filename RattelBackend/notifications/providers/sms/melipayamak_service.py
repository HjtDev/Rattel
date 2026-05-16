from django.conf import settings

from notifications.providers.sms.melipayamak.sms import Rest, Soap, RestAsync, SoapAsync
from notifications.providers.sms.melipayamak import Api
from notifications.providers.base import BaseSMSProvider
from django.core.cache import cache
from notifications.tasks.melipayamak import send_sms_task, send_sms_with_template_task
import logging, os


logger = logging.getLogger(__name__)

class MelipayamakProvider(BaseSMSProvider):
    REQUIRES_API_KEY = False
    
    def __init__(
            self,
            api_key: str = None,
            username: str = 'test',
            password: str = '1234',
            sender: str = None,
            use_soap: bool = False,
            use_async: bool = False,
            use_celery: bool = False,
            admin: str = None,
            cache_prefix: str = 'melipayamak'
    ):
        """
            Initializes Melipayamak provider using its official module.
         
            If you use_celery=True:
            - SMS sending is delegated to a Celery worker (fire-and-forget).
            - The provider will NOT store last message data in cache.
            - Delivery status and recID are NOT available synchronously.
            - You must retrieve message information using:
                self.sms.get_messages(2, 0, 1, self.sender) ==> Retrieves the last sent message in provider's inbox
            Use Celery ONLY for background sending where immediate results are not required.
        """
        super().__init__(api_key)
        
        # Basic sanitization
        if not username.strip():
            raise ValueError('username cannot be empty')
            
        if not password.strip():
            raise ValueError('password cannot be empty')
        
        if not isinstance(use_soap, bool):
            raise ValueError('use_soap must be a boolean')
        
        if not isinstance(use_async, bool):
            raise ValueError('use_async must be a boolean')
        
        # Will be required later in getting list of senders
        self.username = username
        self.password = password
        
        # Setting the main configuration based on the melipayamak docs
        self.method = 'soap' if use_soap else 'rest'
        self.type = 'async' if use_async else 'sync'
        
        if self.type == 'async' and use_celery:
            raise ValueError('Celery does not support async type.')
        self.use_celery = use_celery
        
        self.api: Api = Api(self.username, self.password)
        
        self.sms: Rest | RestAsync | Soap | SoapAsync = self.api.sms(_method=self.method, _type=self.type)
        
        # To prevent creating a new one each time we want to get the list of numbers with SOAP
        self.fallback_rest_client: Rest = self.api.sms(_method='rest', _type=self.type)
        
        self._credit = None
        
        # We can set a celery task to check the credit if admin is set and warning is enabled to check the credit and warn the admin before it's to late
        if admin:
            self.admin = admin
            
            # Making sure the admin phone number is valid
            if not self.PHONE_REGEX.match(self.admin):
                raise ValueError('Invalid phone number.')
            
        self.warn_on_low_credit = settings.SMS_API_WARN_ON_LOW_CREDIT
        
        # Should set the admin phone number if the warning is enabled
        if self.warn_on_low_credit and not admin:
            raise ValueError('You have to set an admin phone number to get warnings.')
        
        # Due to limitation of melipayamk API we have to manually set the sender if we want to use soap
        if sender is None and self.method == 'soap':
            raise ValueError('In order to use the Soap method you must specify a valid sender.')
        
        # Receives all the available senders and choose a sender(either the sender that was passed or the first one in the list)
        self.senders_list = self.get_list_of_senders()
        self.sender = self.get_usable_sender(sender)
        
        # Sanitizing the cache_prefix
        if not isinstance(cache_prefix, str):
            raise ValueError('cache_prefix must be a string')
        self.cache_prefix = cache_prefix
        self._cache_key_data = f'{cache_prefix}_last_data'
        self._cache_key_warn = f'{cache_prefix}_warn'
        
    @property
    def credit(self):
        """
            Get the number remaining messages we can send. Lazy fetched on creation
        """
        if self._credit is None:
            return self.refresh_credit()
        return self._credit
    
    def refresh_credit(self) -> int:
        """
            Retrieves the credit from melipayamak API.
            
            Returns:
                The number of messages we can send
        """
        res = self.sms.get_credit()
        
        # In soap the credit is returned directly
        if self.method == 'soap':
            self._credit = int(res)
            return self._credit
        
        if res.get('RetStatus', 0) != 1 or res.get('StrRetStatus') != 'Ok':
            logger.error('Failed to fetch credit endpoint.')
            return 0
        
        # Retrieves the credit value and tries to sanitize it.
        result = res.get('Value', None)
        credit = self._get_credit_value(result)
        
        # If credit was negative that means there is an error in the credentials
        if credit == -110:
            raise ValueError('Use your api_key for password.')
        elif credit == -109:
            raise Exception('Add your IP to whitelist.')
        elif credit == -108:
            raise PermissionError('Your IP has been blacklisted.')
        else:
            # If there is no error then the credit is valid and can be saved
            self._credit = credit
            return self._credit
    
    async def get_credit_async(self) -> int:
        """
            Retrieves the credit from melipayamak API with async.
            
            Returns:
                The number of messages we can send
        """
        res = await self.sms.get_credit()
        if res.get('RetStatus', 0) != 1 or res.get('StrRetStatus') != 'Ok':
            logger.error('Failed to fetch credit endpoint.')
            return 0
        
        result = res.get('Value', None)
        credit = self._get_credit_value(result)
        
        if credit == -110:
            raise ValueError('Use your api_key for password.')
        elif credit == -109:
            raise Exception('Add your IP to whitelist.')
        elif credit == -108:
            raise PermissionError('Your IP has been blacklisted.')
        else:
            return credit
        
    def _get_credit_value(self, credit: int | float | str) -> int:
        """
            Converts the credit value to an int that represents the number of messages we can send.
            
            Args:
                credit (int | float | str): The credit value to convert.
                
            Returns:
                Sanitized credit value
        """
        if isinstance(credit, str):
            try:
                # If the credit value was float string
                credit = int(float(credit))
                return credit
            except ValueError:
                logger.error(f'Failed to convert credit to a usable number ==> Credit: {credit}')
                return 0
        elif isinstance(credit, float):
            # If credit was a float we could directly convert it to int
            return int(credit)
        elif isinstance(credit, int):
            # If the API sanitized it we can use it directly
            return credit
        else:
            # Probably internet issues
            logger.error(f'Failed to get credit value: {credit}')
            return 0
    
    def get_list_of_senders(self) -> list[str]:
        """
            Fetches the list of sender numbers that is active on the account and stores them in a list.
            
            Returns:
                The list of sender numbers
        """
        if self.method == 'rest':
            # If the method is REST we can directly call the get_numbers
            res = self.sms.get_numbers()
        else:
            # If the method is soap we don't have access to get_numbers
            # Temporary uses a rest API endpoint to get the numbers list.
            logger.warning('Getting the list of sender numbers is not supported in SOAP method.')
            logger.warning('Temporary fallback to REST method')
            res = self.fallback_rest_client.get_numbers()
        
        # Tries to check if all the required data is present
        status = res.get('MyBase', None)
        if not status:
            logger.error('Failed to fetch the list of senders.')
            return []
        if status.get('StrRetStatus') != 'Ok' or status.get('RetStatus') != 1:
            logger.error('Failed to get the list of senders.')
            return []
        
        # Extracts all the senders numbers
        senders = [sender.get('Number') for sender in res.get('Data', [dict()]) if sender.get('Number')]
        return senders
    
    async def get_list_of_senders_async(self) -> list[str]:
        """
            Fetches the list of sender numbers that is active on the account and stores them in a list.
            
            Returns:
                The list of sender numbers
        """
        if self.method == 'rest':
            res = await self.sms.get_numbers()
        else:
            res = await self.fallback_rest_client.get_numbers()
        
        status = res.get('MyBase', None)
        if not status:
            logger.error('Failed to fetch the list of senders.')
            return []
        if status.get('StrRetStatus') != 'Ok' or status.get('RetStatus') != 1:
            logger.error('Failed to get the list of senders.')
            return []
        
        senders = [sender.get('Number') for sender in res.get('Data', [dict()]) if sender.get('Number')]
        return senders
        
    def get_usable_sender(self, sender: str | None):
        """
            Tries to find the sender in the senders_list and if it didn't find a matching number it will fall back to the first number in senders_list.
            
            Args:
                sender (str | None): The sender number
                
            Returns:
                A valid sender number
        """
        if len(self.senders_list) == 0:
            raise ValueError('Your account has no sender. Reach out to your SMS service provider.')
        
        # If sender number is found the list we can use it
        if sender and sender in self.senders_list:
            logger.warning(f'Using sender: {sender}')
            return sender
        
        # Sender number was not in the list so we fall back to the default sender
        elif len(self.senders_list) >= 1:
            logger.warning(f'Using default sender: {self.senders_list[0]}')
            return self.senders_list[0]
        
        # There is no sender available
        else:
            raise ValueError('No valid sender found.')
        
    def _update_cache(
            self,
            last_sender: str | None = None,
            last_target: str | None = None,
            last_message: str | None = None,
            last_message_id: str | None = None,
    ) -> None:
        """
            Stores the essential data of the last sent message that can be used across all the instances
            
            Args:
                last_sender (str | None): The sender number that was used to send the last message.
                last_target (str | None): The last phone number that received a message.
                last_message (str | None): The last message that was sent.
                last_message_id (str | None): The last message recID.
                
            Returns:
                None
        """
        last_data = cache.get(self._cache_key_data, dict())
        
        if last_sender:
            last_data['last_sender'] = last_sender
        if last_target:
            last_data['last_target'] = last_target
        if last_message:
            last_data['last_message'] = last_message
        if last_message_id:
            last_data['last_message_id'] = last_message_id
            
        cache.set(self._cache_key_data, last_data)
        
    def get_last_message(self) -> dict[str, str] | None:
        """
            Loads the last message data from the cache
            
            Returns:
                Returns the last message data if it exists(if not returns None)
        """
        last_data = cache.get(self._cache_key_data, dict())
        if last_data:
            return last_data
        logger.warning('No last SMS data found.')
        return None
    
    def _delivery_status(self, delivery_status: str):
        """
            Outputs an error for every code. Only for is_delivered endpoint
            
            Args:
                delivery_status (str): The status of the delivery that was received from is_delivered.
                
            Returns:
                True if the message is delivered successfully False otherwise.
        """
        logger.info(f'Checking delivery status for {delivery_status}')
        match int(delivery_status):
            case -1:
                logger.warning('Message was not sent.')
            case -2:
                logger.error('Too many targets for one call')
            case -3:
                logger.error('Invalid username/password.')
            case -10:
                logger.warning('Could not receive logs for this message.')
            case 0:
                logger.info('Sent to Mokhaberat.')
                return True
            case 1:
                logger.info('Reached the target phone.')
                return True
            case 2:
                logger.info('Has not reached the target phone yet.')
            case 3:
                logger.error('Provider has an issue in sending this message.')
            case 5:
                logger.error('Unknow error.')
            case 8:
                logger.info('Reached Mokhaberat.')
                return True
            case 16:
                logger.warning('Has not reached to Mokhaberat.')
            case 35:
                logger.warning('Target phone was blacklisted.')
            case 100:
                logger.error('Something went wrong.')
            case 200:
                logger.info('Message was sent successfully.')
                return True
            case 300:
                logger.warning('The message was censored.')
            case 400:
                logger.info('Message in queue')
            case 500:
                logger.error('Message was rejected.')
        return False
        
    def is_delivered(self, rec_id: str = None) -> bool:
        """
            Checks if the last sent message was delivered successfully.
            Can also check other messages delivery status if rec_id was passed
            
            Args:
                rec_id (str): The recID of the message you want to check its delivery status.
                
            Returns:
                True if the message was delivered successfully False otherwise.
        """
        
        message_id = rec_id
        
        # rec_id was not passed
        # Tries to check for the rec_id of the last sent message
        if not message_id:
            last_data = self.get_last_message()
            if not last_data:
                # No last message
                logger.error('Could not find any message id to check. Please pass a rec_id.')
                return False
            message_id = last_data.get('last_message_id', None)
            
        # There was no last message and rec_id was not passed too.
        if not message_id:
            logger.error('Could not find any message id to check. Please pass a rec_id.')
            return False
            
        res = self.sms.is_delivered(message_id)
        
        # Tries to extract the message delivery code
        delivery_status = res
        if self.method == 'rest' and isinstance(res, dict) and res.get('Value', False):
            delivery_status = res.get('Value')
            
        # Passes the delivery code to _delivery_status to convert it to a boolean status.
        # Also logs any error or issue
        return self._delivery_status(delivery_status)
    
    async def is_delivered_async(self, rec_id: str = None) -> bool:
        """
            Checks if the last sent message was delivered successfully.
            Can also check other messages delivery status if rec_id was passed
            
            Args:
                rec_id (str): The recID of the message you want to check its delivery status.
                
            Returns:
                True if the message was delivered successfully False otherwise.
        """
        message_id = rec_id
        if not message_id:
            last_data = self.get_last_message()
            if not last_data:
                logger.error('Could not find any message id to check. Please pass a rec_id.')
                return False
            message_id = last_data.get('last_message_id', None)
        
        if not message_id:
            logger.error('Could not find any message id to check. Please pass a rec_id.')
            return False
        
        res = await self.sms.is_delivered(message_id)
        if isinstance(res, dict) and res.get('Value', False):
            delivery_status = res.get('Value')
            return self._delivery_status(delivery_status)
        else:
            logger.error(f'There is a problem with API. {res}')
            return False
        
    def _send_status(self, value: str) -> bool:
        """
            Outputs an error for every code. Only for send endpoint
            
            Args:
                value (str): The status of the message that was sent from sms.send.
                
            Returns:
                True if value was a valid recID False otherwise.
        """
        match int(value):
            case -110:
                raise ValueError('You have to use api_key instead of password')
            case -109:
                logger.error('You have to configure whitelist IPs in your providers dashboard')
            case -108:
                logger.error('You have been blacklisted. Contact your provider')
            case 0:
                raise PermissionError('username/password is wrong.')
            case 2:
                logger.error('Insufficient credit')
            case 3:
                logger.error('You have hit the quota for today.')
            case 4:
                logger.error('data is too big to be sent')
            case 6:
                logger.error('The provider is updating their system')
            case 7:
                logger.error('The message contains censored words.')
            case 10:
                logger.error('Your account has been deactivated.')
            case 11:
                logger.error('Your target phone number is blacklisted.')
            case 12:
                logger.error('Incomplete authentication.')
            case 14:
                logger.error('The message contains link.')
            case 16:
                logger.error('Could not find the target phone number.')
            case 17:
                logger.error('Empty messages are not allowed.')
            case 18:
                logger.error('Target phone number is invalid.')
            case 35:
                logger.error('If you are using REST method it means the target phone number is blacklisted.')
            case _:
                # If the value is longer than 14 character then it means it's a valid recID
                if len(value) >= 15:
                    return True
                else:
                    # Unknow error_value
                    logger.error('Something went wrong.')
                    return False
        
        return False
        
        
    def send(self, to: str, message: str, is_flash: bool = False):
        """
            Sends an SMS with normal sms.send with validation
            
            Args:
                to (str): The recipient phone number.
                message (str): The message to send.
                is_flash (bool, optional): Whether the message is flash.
                
            Returns:
                True if the message was sent successfully False otherwise.
        """
        
        # Validates the recipient phone number
        if not self.validate_contacts(to):
            raise ValueError(f'Invalid phone number: {to}')
        
        # Only non-empty messages can be sent
        if not message.strip():
            raise ValueError('Message cannot be empty')
        
        # is_flush is optional but if passed it should be boolean
        if not isinstance(is_flash, bool):
            raise ValueError('is_flash must be a boolean')
        
        # Fetches the sms.send endpoint.
        if self.use_celery:
            send_sms_task.delay(to, self.sender, message, is_flash, username=self.username, password=self.password, _method=self.method, _type=self.type)
            return True  # Queued but not sent. At least not yet
        res = self.sms.send(to, self.sender, message, is_flash)
        
        # Tries to check if the message was sent successfully
        value = res
        if self.method == 'rest' and isinstance(res, dict) and res.get('RetStatus', 0) and res.get('StrRetStatus', None) == 'Ok':
            value = res.get('Value', '11')
        
        # Passes the message status value to validate it.
        status = self._send_status(value)
        if status:  # Message was sent successfully
            # Updates the last sent message
            self._update_cache(self.sender, to, message, value)
            return True
        else:
            # The endpoint output has been changed and the logic requires an update
            logger.error('There was a problem sending this message.')
            return False
    
    async def send_async(self, to: str, message: str, is_flash: bool = False):
        """
            Sends an SMS with normal sms.send with validation
            
            Args:
                to (str): The recipient phone number.
                message (str): The message to send.
                is_flash (bool, optional): Whether the message is flash.
                
            Returns:
                True if the message was sent successfully False otherwise.
        """
        if not to.strip() or not self.validate_contacts(to):
            raise ValueError(f'Invalid phone number: {to}')
        
        if not message.strip():
            raise ValueError('Message cannot be empty')
        
        if not isinstance(is_flash, bool):
            raise ValueError('is_flash must be a boolean')
        
        res = await self.sms.send(to, self.sender, message, is_flash)
        
        value = res
        if self.method == 'rest' and isinstance(res, dict) and res.get('RetStatus', 0) and res.get('StrRetStatus', None) == 'Ok':
            value = res.get('Value', '11')
        
        # Passes the message status value to validate it.
        status = self._send_status(value)
        if status:  # Message was sent successfully
            # Updates the last sent message
            self._update_cache(self.sender, to, message, value)
            return True
        else:
            # The endpoint output has been changed and the logic requires an update
            logger.error('There was a problem sending this message.')
            return False
        
    def _send_with_template_status(self, value: str) -> bool:
        """
            Outputs an error for every code. Only for send_by_base_number endpoint
            
            Args:
                value (str): The status of the message that was sent from sms.send_by_base_number.
                
            Returns:
                True if value was a valid recID False otherwise.
        """
        match int(value):
            case -111:
                logger.error('Invalid caller IP.')
            case -110:
                logger.error('Use your api_key instead of password.')
            case -109:
                logger.error('Your IP is blacklisted.')
            case -10:
                logger.error('You can not send a link')
            case -7:
                logger.error('There is a problem with the sender number. Contact your provider.')
            case -6:
                logger.error('Internal provider error. Contact your provider.')
            case -5:
                logger.error('The given arguments do not match the template.')
            case -4:
                logger.error('body_id is not marked by provider or it does not exist.')
            case -3:
                logger.error('Internal provider error. Contact your provider.')
            case -2:
                logger.error('You can not send message to more than one phone number per call.')
            case -1:
                logger.error('Sending by template is disabled by your provider. Please contact your provider.')
            case 0:
                raise PermissionError('username/password is wrong.')
            case 2:
                logger.error('Insufficient credit')
            case 6:
                logger.error('The provider is updating their system')
            case 7:
                logger.error('The message contains censored words.')
            case 10:
                logger.error('The target phone is deactivated.')
            case 11:
                logger.error('The target phone number is blacklisted.')
            case 12:
                logger.error('Incomplete authentication.')
            case 16:
                logger.error('Could not find the target phone number.')
            case 17:
                logger.error('Empty messages are not allowed.')
            case 18:
                logger.error('Target phone number is invalid.')
            case 19:
                logger.error('You can not send message with template at this time.')
            case 35:
                logger.error('If you are using REST method it means the target phone number is blacklisted.')
            case _:
                if len(value) >= 15:
                    return True
                else:
                    logger.error('Something went wrong.')
                
        return False
        
    def send_with_template(self, body_id: int, to: str, *args):
        """
            Arranges the arguments and sends them with body_id to the endpoint.
            Message will be built and delivered to the recipient phone number by provider.
            
            Args:
                body_id (int): Message template ID.
                to (str): The recipient phone number.
                *args: Arguments passed to the template. Should have ordered the same way they are specified in the provider dashboard.
            
            Returns:
                True if the message was sent successfully False otherwise.
        """
        if not to.strip() or not self.validate_contacts(to):
            raise ValueError(f'Invalid phone number: {to}.')
        
        if not args:
            raise ValueError('You have to send at least one template variable.')
        
        args_str = ';'.join(str(arg) for arg in args)
        
        if self.use_celery:
            send_sms_with_template_task.delay(text=args_str, to=to, body_id=body_id, username=self.username, password=self.password, _method=self.method, _type=self.type)
            return True  # Queued but not sent. At least not yet
        response = self.sms.send_by_base_number(args_str, to, body_id)
        
        if self.method == 'rest' and (not isinstance(response, dict) or not response.get('RetStatus', False) or response.get('StrRetStatus', None) != 'Ok'):
            logger.error(f'There was a problem sending this message. {response}')
            return False
        
        value = response.get('Value', '11') if self.method == 'rest' else response
        status = self._send_with_template_status(value)
        
        if status:
            self._update_cache(self.sender, to, f'Message was sent with template => Template ID: {body_id} | Args: {args}', value)
            return True
        else:
            logger.error('There was a problem sending this message.')
            return False
    
    async def send_with_template_async(self, body_id: int, to: str, *args):
        """
            Arranges the arguments and sends them with body_id to the endpoint.
            Message will be built and delivered to the recipient phone number by provider.
            
            Args:
                body_id (int): Message template ID.
                to (str): The recipient phone number.
                *args: Arguments passed to the template. Should have ordered the same way they are specified in the provider dashboard.
            
            Returns:
                True if the message was sent successfully False otherwise.
        """
        if not to.strip() or not self.validate_contacts(to):
            raise ValueError(f'Invalid phone number: {to}.')
        
        if not args:
            raise ValueError('You have to send at least one template variable.')
        
        args_str = ';'.join(str(arg) for arg in args)
        response = await self.sms.send_by_base_number(args_str, to, body_id)
        
        if self.method == 'rest' and (not isinstance(response, dict) or not response.get('RetStatus', False) or response.get('StrRetStatus', None) != 'Ok'):
            logger.error(f'There was a problem sending this message. {response}')
            return False
        
        value = response.get('Value', '11') if self.method == 'rest' else response
        status = self._send_with_template_status(value)
        
        if status:
            self._update_cache(self.sender, to, f'Message was sent with template => Template ID: {body_id} | Args: {args}', value)
            return True
        else:
            logger.error('There was a problem sending this message.')
            return False
        
    def warn_admin(self):
        """
            Checks the credit, and if warn_on_low_credit is set to true, sends warning on low credit.
        """
        
        # The option is disabled
        if not self.warn_on_low_credit or not self.admin:
            return False
        
        # Not critical yet
        if self.credit > 20:
            cache.set(self._cache_key_warn, False)  # Resets the cache if
            return False
        
        # Checking cache to see if we warned the admin before
        if cache.get(self._cache_key_warn):
            # Already warned
            return False
        
        # Updates cache to warned
        cache.set(self._cache_key_warn, True)
        
        return True
