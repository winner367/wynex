import json
import websocket
import time
import threading
import logging
from typing import Dict, List, Any, Callable, Optional, Union

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DerivAPI:
    """API class for interacting with Deriv's WebSocket API"""
    
    def __init__(self, app_id: str, endpoint: str = "wss://ws.binaryws.com/websockets/v3"):
        """
        Initialize the Deriv API
        
        Args:
            app_id: Deriv application ID
            endpoint: WebSocket endpoint
        """
        self.app_id = app_id
        self.endpoint = endpoint
        self.ws = None
        self.connected = False
        
        # Message handling
        self.callback_registry = {}
        self.request_id_counter = 1
        self.request_map = {}
        
        # User accounts
        self.accounts = []
        self.active_account = None
        
        # Subscriptions
        self.active_subscriptions = {}
        
        # Threading
        self.heartbeat_thread = None
        self.running = False
        
    def connect(self) -> bool:
        """
        Connect to Deriv WebSocket
        
        Returns:
            True if connection successful
        """
        try:
            # Close existing connection if any
            if self.ws:
                self.ws.close()
                
            # Create new WebSocket connection
            self.ws = websocket.create_connection(self.endpoint)
            
            # Authorize if token is available
            auth_response = self.send({"app_id": self.app_id})
            
            if 'error' in auth_response:
                logger.error(f"Connection error: {auth_response['error']['message']}")
                return False
                
            self.connected = True
            
            # Start heartbeat
            self.start_heartbeat()
            
            # Start message processing thread
            self.running = True
            threading.Thread(target=self.message_loop, daemon=True).start()
            
            logger.info("Connected to Deriv WebSocket API")
            return True
            
        except Exception as e:
            logger.error(f"Connection error: {str(e)}")
            self.connected = False
            return False
            
    def connect_with_token(self, token: str) -> bool:
        """
        Connect and authorize with an access token
        
        Args:
            token: Deriv OAuth access token
            
        Returns:
            True if connection and authorization successful
        """
        if not self.connect():
            return False
            
        # Authorize with token
        auth_response = self.send({
            "authorize": token,
            "app_id": self.app_id
        })
        
        if 'error' in auth_response:
            logger.error(f"Authorization error: {auth_response['error']['message']}")
            return False
            
        # Store authorization details
        if 'authorize' in auth_response:
            auth_data = auth_response['authorize']
            self.active_account = auth_data
            
            # Fetch account list
            self.get_account_list()
            
            return True
            
        return False
        
    def disconnect(self):
        """Disconnect from Deriv WebSocket"""
        self.running = False
        
        # Cancel all active subscriptions
        for req_id in list(self.active_subscriptions.keys()):
            self.send({"forget": req_id})
            
        self.active_subscriptions = {}
        
        # Clean up the connection
        if self.ws:
            try:
                self.ws.close()
            except:
                pass
            self.ws = None
            
        self.connected = False
        logger.info("Disconnected from Deriv WebSocket API")
        
    def start_heartbeat(self):
        """Start the heartbeat thread"""
        if self.heartbeat_thread and self.heartbeat_thread.is_alive():
            return
            
        def heartbeat_task():
            while self.connected and self.running:
                try:
                    self.send({"ping": 1}, wait_response=False)
                    time.sleep(30)  # Send ping every 30 seconds
                except:
                    # Heartbeat failed, connection may be lost
                    break
                    
        self.heartbeat_thread = threading.Thread(target=heartbeat_task, daemon=True)
        self.heartbeat_thread.start()
        
    def message_loop(self):
        """Process incoming messages in a separate thread"""
        while self.running and self.connected and self.ws:
            try:
                message = self.ws.recv()
                
                if not message:
                    continue
                    
                response = json.loads(message)
                self.handle_response(response)
                
            except websocket.WebSocketConnectionClosedException:
                logger.error("WebSocket connection closed")
                self.connected = False
                break
            except Exception as e:
                logger.error(f"Error in message loop: {str(e)}")
                time.sleep(1)  # Prevent tight loop in case of errors
                
    def handle_response(self, response: Dict[str, Any]):
        """
        Handle a response from the WebSocket
        
        Args:
            response: WebSocket response dictionary
        """
        # Check for request ID
        req_id = response.get('req_id')
        if req_id:
            # Check if we have a stored callback
            if req_id in self.request_map:
                request_info = self.request_map.pop(req_id)
                request_info['result'] = response
                request_info['event'].set()
        
        # Check for subscription responses
        msg_type = response.get('msg_type')
        
        # Call registered callbacks for this message type
        if msg_type in self.callback_registry:
            for callback in self.callback_registry[msg_type]:
                try:
                    callback(response)
                except Exception as e:
                    logger.error(f"Error in callback for {msg_type}: {str(e)}")
                    
    def send(self, request: Dict[str, Any], wait_response: bool = True, timeout: int = 10) -> Dict[str, Any]:
        """
        Send a request to Deriv WebSocket API
        
        Args:
            request: Request dictionary
            wait_response: Whether to wait for a response
            timeout: Timeout in seconds
            
        Returns:
            Response dictionary
        """
        if not self.connected or not self.ws:
            if not self.connect():
                return {"error": {"message": "Not connected"}}
                
        # Add request ID
        req_id = self.request_id_counter
        self.request_id_counter += 1
        
        request['req_id'] = req_id
        
        # Prepare for response
        if wait_response:
            event = threading.Event()
            self.request_map[req_id] = {
                'event': event,
                'result': None
            }
            
        # Send request
        try:
            self.ws.send(json.dumps(request))
        except Exception as e:
            logger.error(f"Send error: {str(e)}")
            if wait_response and req_id in self.request_map:
                del self.request_map[req_id]
            return {"error": {"message": str(e)}}
            
        # Wait for response if required
        if wait_response:
            if event.wait(timeout):
                return self.request_map[req_id]['result']
            else:
                # Timeout
                if req_id in self.request_map:
                    del self.request_map[req_id]
                return {"error": {"message": "Request timed out"}}
        else:
            return {"success": True}
            
    def register_callback(self, msg_type: str, callback: Callable[[Dict[str, Any]], None]):
        """
        Register a callback for a specific message type
        
        Args:
            msg_type: Message type to listen for
            callback: Function to call with the response
        """
        if msg_type not in self.callback_registry:
            self.callback_registry[msg_type] = []
            
        self.callback_registry[msg_type].append(callback)
        
    def unregister_callback(self, msg_type: str, callback: Callable[[Dict[str, Any]], None]):
        """
        Unregister a callback
        
        Args:
            msg_type: Message type
            callback: Callback function to remove
        """
        if msg_type in self.callback_registry:
            if callback in self.callback_registry[msg_type]:
                self.callback_registry[msg_type].remove(callback)
                
    def get_account_list(self) -> List[Dict[str, Any]]:
        """
        Get list of user accounts
        
        Returns:
            List of account dictionaries
        """
        response = self.send({
            "account_list": 1
        })
        
        if 'error' in response:
            logger.error(f"Error getting account list: {response['error']['message']}")
            return []
            
        if 'account_list' in response:
            self.accounts = response['account_list']
            return self.accounts
            
        return []
        
    def switch_account(self, loginid: str) -> bool:
        """
        Switch to a different account
        
        Args:
            loginid: Account login ID
            
        Returns:
            True if successful
        """
        # Get login token for the account
        response = self.send({
            "account_list": 1,
            "account_type": "trading"
        })
        
        if 'error' in response:
            logger.error(f"Error getting account list: {response['error']['message']}")
            return False
            
        login_token = None
        
        if 'account_list' in response:
            for account in response['account_list']:
                if account.get('loginid') == loginid:
                    login_token = account.get('token')
                    break
        
        if not login_token:
            logger.error(f"Could not find login token for account {loginid}")
            return False
            
        # Switch account
        response = self.send({
            "authorize": login_token,
            "app_id": self.app_id
        })
        
        if 'error' in response:
            logger.error(f"Error switching account: {response['error']['message']}")
            return False
            
        if 'authorize' in response:
            self.active_account = response['authorize']
            return True
            
        return False
        
    def get_account_info(self) -> Dict[str, Any]:
        """
        Get information about the current account
        
        Returns:
            Account information dictionary
        """
        if not self.active_account:
            return {}
            
        return {
            'id': self.active_account.get('loginid', 'Unknown'),
            'name': self.active_account.get('fullname', 'Unknown'),
            'email': self.active_account.get('email', 'Unknown'),
            'balance': self.active_account.get('balance', 0.0),
            'currency': self.active_account.get('currency', 'USD'),
            'is_demo': self.active_account.get('is_virtual', True)
        }
        
    def get_active_symbols(self) -> List[Dict[str, Any]]:
        """
        Get list of active symbols/markets
        
        Returns:
            List of symbol dictionaries
        """
        response = self.send({
            "active_symbols": "brief",
            "product_type": "basic"
        })
        
        if 'error' in response:
            logger.error(f"Error getting active symbols: {response['error']['message']}")
            return []
            
        if 'active_symbols' in response:
            return response['active_symbols']
            
        return []
        
    def buy_contract(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Buy a contract
        
        Args:
            parameters: Contract parameters
            
        Returns:
            Buy response
        """
        # Ensure required parameters
        required_params = ['amount', 'basis', 'contract_type', 'symbol', 'duration', 'duration_unit']
        
        for param in required_params:
            if param not in parameters:
                return {"error": {"message": f"Missing required parameter: {param}"}}
                
        # Add app_id
        parameters['app_id'] = self.app_id
        
        # Send buy request
        buy_request = {
            "buy": 1,
            "price": parameters['amount'],
            "parameters": parameters
        }
        
        response = self.send(buy_request)
        return response
        
    def get_ticks(self, symbol: str, callback: Callable[[Dict[str, Any]], None]) -> str:
        """
        Subscribe to tick data for a symbol
        
        Args:
            symbol: Symbol to get ticks for
            callback: Callback function for tick data
            
        Returns:
            Subscription ID or empty string on error
        """
        # Register callback
        self.register_callback('tick', callback)
        
        # Subscribe to ticks
        response = self.send({
            "ticks": symbol
        })
        
        if 'error' in response:
            logger.error(f"Error subscribing to ticks: {response['error']['message']}")
            self.unregister_callback('tick', callback)
            return ""
            
        if 'subscription' in response:
            subscription_id = response['subscription']['id']
            self.active_subscriptions[subscription_id] = 'tick'
            return subscription_id
            
        return ""
        
    def forget(self, subscription_id: str) -> bool:
        """
        Cancel a subscription
        
        Args:
            subscription_id: Subscription ID to cancel
            
        Returns:
            True if successful
        """
        response = self.send({
            "forget": subscription_id
        })
        
        if 'error' in response:
            logger.error(f"Error cancelling subscription: {response['error']['message']}")
            return False
            
        if subscription_id in self.active_subscriptions:
            del self.active_subscriptions[subscription_id]
            
        return response.get('forget') == 1

    def get_available_balances(self) -> Dict[str, float]:
        """
        Get available balances for all currencies
        
        Returns:
            Dictionary mapping currency codes to available balances
        """
        if not self.connected:
            return {}
            
        # Get account list to fetch all available accounts
        accounts = self.get_account_list()
        balances = {}
        
        for account in accounts:
            currency = account.get('currency', 'USD')
            balance = float(account.get('balance', 0))
            
            # Add to balances, combining if currency already exists
            if currency in balances:
                balances[currency] += balance
            else:
                balances[currency] = balance
                
        return balances


class MockBrokerAPI:
    """Mock broker API for testing and development"""
    
    def __init__(self, debug: bool = False):
        """Initialize mock broker API"""
        self.debug = debug
        self.connected = True
        self.accounts = [
            {
                'loginid': 'CR123456',
                'currency': 'USD',
                'balance': 1000.00,
                'is_virtual': True
            },
            {
                'loginid': 'CR789012',
                'currency': 'EUR',
                'balance': 850.00,
                'is_virtual': True
            }
        ]
        self.active_account = self.accounts[0]
        
    def connect(self) -> bool:
        """
        Connect to mock broker
        
        Returns:
            Always True
        """
        self.connected = True
        return True
        
    def connect_with_token(self, token: str) -> bool:
        """
        Connect with token
        
        Args:
            token: Token (ignored)
            
        Returns:
            Always True
        """
        self.connected = True
        return True
        
    def disconnect(self):
        """Disconnect from mock broker"""
        self.connected = False
        
    def get_account_list(self) -> List[Dict[str, Any]]:
        """
        Get mock account list
        
        Returns:
            List of mock accounts
        """
        return self.accounts
        
    def switch_account(self, loginid: str) -> bool:
        """
        Switch to different account
        
        Args:
            loginid: Account to switch to
            
        Returns:
            True if account found
        """
        for account in self.accounts:
            if account['loginid'] == loginid:
                self.active_account = account
                return True
                
        return False
        
    def get_account_info(self) -> Dict[str, Any]:
        """
        Get mock account info
        
        Returns:
            Mock account info
        """
        return {
            'id': self.active_account['loginid'],
            'name': 'Demo User',
            'email': 'demo@example.com',
            'balance': self.active_account['balance'],
            'currency': self.active_account['currency'],
            'is_demo': self.active_account['is_virtual']
        }
        
    def get_active_symbols(self) -> List[Dict[str, Any]]:
        """
        Get mock symbols
        
        Returns:
            List of mock symbols
        """
        return [
            {"symbol": "R_10", "display_name": "Volatility 10 Index"},
            {"symbol": "R_25", "display_name": "Volatility 25 Index"},
            {"symbol": "R_50", "display_name": "Volatility 50 Index"},
            {"symbol": "R_75", "display_name": "Volatility 75 Index"},
            {"symbol": "R_100", "display_name": "Volatility 100 Index"}
        ]

    def get_available_balances(self) -> Dict[str, float]:
        """
        Get available balances for all currencies (mock implementation)
        
        Returns:
            Dictionary mapping currency codes to available balances
        """
        balances = {}
        for account in self.accounts:
            currency = account.get('currency', 'USD')
            balance = float(account.get('balance', 0))
            
            if currency in balances:
                balances[currency] += balance
            else:
                balances[currency] = balance
                
        return balances


def create_broker_api(broker_type: str, app_id: str = None, debug: bool = False):
    """
    Factory function to create a broker API instance
    
    Args:
        broker_type: Type of broker ("deriv" or "mock")
        app_id: App ID for Deriv API
        debug: Whether to enable debug mode
        
    Returns:
        Broker API instance
    """
    if broker_type.lower() == "deriv":
        if not app_id:
            raise ValueError("App ID is required for Deriv API")
            
        return DerivAPI(app_id=app_id)
    else:
        return MockBrokerAPI(debug=debug)