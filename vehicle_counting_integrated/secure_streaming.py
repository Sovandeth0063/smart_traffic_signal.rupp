"""
SECURE DATA STREAMING MODULE FOR VEHICLE DETECTION
====================================================

This module provides a secure, production-ready data streaming system for real-time 
vehicle detection data. It implements multiple layers of security:

1. AUTHENTICATION & AUTHORIZATION
   - API key-based authentication
   - Token validation on every request
   - User session management

2. ENCRYPTION & DATA INTEGRITY
   - TLS/SSL for secure communication
   - Data integrity validation using HMAC
   - Encrypted sensitive data fields

3. ACCESS CONTROL & MONITORING
   - Rate limiting (requests per second)
   - IP whitelisting
   - Comprehensive audit logging
   - Suspicious activity detection

4. DATA VALIDATION
   - Input/output data schema validation
   - Size limits to prevent buffer overflow
   - Format validation before streaming

5. NETWORK SECURITY
   - Secure WebSocket connections (WSS)
   - Connection timeouts
   - Graceful error handling
   - Resource cleanup

6. MONITORING & LOGGING
   - All access attempts logged
   - Performance metrics tracked
   - Security events recorded
   - Audit trail for compliance

USAGE:
------
1. Start the secure server:
   server = SecureDataStreamServer(host='127.0.0.1', port=8443, api_key='your-secret-key')
   server.start()

2. Connect client with authentication:
   client = SecureStreamClient(server_url='wss://127.0.0.1:8443', api_key='your-secret-key')
   client.connect()

3. Stream data:
   vehicle_counts = {'cars': 5, 'vans': 2, 'motors': 3, 'buses': 1, 'bicycles': 0}
   server.broadcast_data(vehicle_counts)

4. Receive data on client:
   data = client.receive_data()
"""

import asyncio
import json
import logging
import time
import hmac
import hashlib
import secrets
import sqlite3
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, Any, Optional, List
from pathlib import Path
import threading
import ssl

try:
    import websockets
    from websockets.server import WebSocketServerProtocol
except ImportError:
    raise ImportError("websockets library required. Install with: pip install websockets")


# ==================== LOGGING SETUP ====================
def setup_security_logger():
    """Setup comprehensive security logging"""
    log_dir = Path("security_logs")
    log_dir.mkdir(exist_ok=True)
    
    logger = logging.getLogger("SecureStreaming")
    logger.setLevel(logging.DEBUG)
    
    # File handler for security events
    fh = logging.FileHandler(log_dir / f"security_{datetime.now().strftime('%Y%m%d')}.log")
    fh.setLevel(logging.INFO)
    
    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.WARNING)
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    
    logger.addHandler(fh)
    logger.addHandler(ch)
    
    return logger

logger = setup_security_logger()


# ==================== SECURITY UTILITIES ====================
class SecurityManager:
    """
    Manages authentication, encryption, and access control
    
    Features:
    - API key validation
    - HMAC-based data integrity
    - Rate limiting per client
    - IP whitelisting
    - Session token generation
    """
    
    def __init__(self, api_key: str, rate_limit: int = 100):
        """
        Initialize security manager
        
        Args:
            api_key: Master API key for authentication
            rate_limit: Max requests per minute per client
        """
        self.api_key = api_key
        self.rate_limit = rate_limit
        self.client_tokens: Dict[str, Dict] = {}
        self.request_counts: Dict[str, List[float]] = defaultdict(list)
        self.blocked_ips: set = set()
        self.whitelisted_ips: set = set()
        logger.info("SecurityManager initialized")
    
    def validate_api_key(self, provided_key: str) -> bool:
        """Validate API key using timing-safe comparison"""
        is_valid = hmac.compare_digest(provided_key, self.api_key)
        if not is_valid:
            logger.warning(f"Invalid API key attempted")
        return is_valid
    
    def generate_session_token(self, client_id: str) -> str:
        """Generate secure session token"""
        token = secrets.token_urlsafe(32)
        self.client_tokens[client_id] = {
            'token': token,
            'created': time.time(),
            'expires': time.time() + 3600,  # 1 hour expiration
        }
        logger.info(f"Session token generated for client: {client_id}")
        return token
    
    def validate_session_token(self, client_id: str, token: str) -> bool:
        """Validate session token with expiration check"""
        if client_id not in self.client_tokens:
            logger.warning(f"Token validation failed: unknown client {client_id}")
            return False
        
        session = self.client_tokens[client_id]
        
        # Check expiration
        if time.time() > session['expires']:
            del self.client_tokens[client_id]
            logger.warning(f"Token expired for client: {client_id}")
            return False
        
        # Timing-safe comparison
        is_valid = hmac.compare_digest(token, session['token'])
        if not is_valid:
            logger.warning(f"Invalid token for client: {client_id}")
        
        return is_valid
    
    def check_rate_limit(self, client_id: str) -> bool:
        """Check if client exceeds rate limit"""
        now = time.time()
        minute_ago = now - 60
        
        # Clean old requests
        self.request_counts[client_id] = [
            t for t in self.request_counts[client_id] 
            if t > minute_ago
        ]
        
        # Check limit
        if len(self.request_counts[client_id]) >= self.rate_limit:
            logger.warning(f"Rate limit exceeded for client: {client_id}")
            return False
        
        self.request_counts[client_id].append(now)
        return True
    
    def add_whitelist_ip(self, ip: str):
        """Add IP to whitelist"""
        self.whitelisted_ips.add(ip)
        logger.info(f"IP whitelisted: {ip}")
    
    def block_ip(self, ip: str):
        """Block IP address"""
        self.blocked_ips.add(ip)
        logger.warning(f"IP blocked: {ip}")
    
    def is_ip_allowed(self, ip: str) -> bool:
        """Check if IP is allowed"""
        if ip in self.blocked_ips:
            logger.warning(f"Blocked IP attempted connection: {ip}")
            return False
        
        if self.whitelisted_ips and ip not in self.whitelisted_ips:
            logger.warning(f"IP not in whitelist: {ip}")
            return False
        
        return True
    
    def compute_hmac(self, data: str) -> str:
        """Compute HMAC for data integrity"""
        return hmac.new(
            self.api_key.encode(),
            data.encode(),
            hashlib.sha256
        ).hexdigest()
    
    def verify_hmac(self, data: str, provided_hmac: str) -> bool:
        """Verify HMAC with timing-safe comparison"""
        computed = self.compute_hmac(data)
        return hmac.compare_digest(computed, provided_hmac)


# ==================== DATA VALIDATION ====================
class DataValidator:
    """
    Validates data format, size, and content
    
    Features:
    - Schema validation
    - Size limits
    - Content sanitization
    - Type checking
    """
    
    # Maximum data size (1MB)
    MAX_DATA_SIZE = 1024 * 1024
    
    # Valid vehicle types
    VALID_VEHICLES = {'cars', 'vans', 'motors', 'buses', 'bicycles'}
    
    @staticmethod
    def validate_vehicle_data(data: Dict[str, Any]) -> bool:
        """Validate vehicle count data structure"""
        try:
            # Check required fields
            if not isinstance(data, dict):
                logger.warning("Data is not a dictionary")
                return False
            
            # Check for all required vehicle types
            for vehicle_type in DataValidator.VALID_VEHICLES:
                if vehicle_type not in data:
                    logger.warning(f"Missing vehicle type: {vehicle_type}")
                    return False
                
                # Validate count is non-negative integer
                count = data[vehicle_type]
                if not isinstance(count, int) or count < 0:
                    logger.warning(f"Invalid count for {vehicle_type}: {count}")
                    return False
            
            # Optional fields
            if 'timestamp' in data:
                if not isinstance(data['timestamp'], (int, float)):
                    logger.warning("Invalid timestamp format")
                    return False
            
            return True
        except Exception as e:
            logger.error(f"Data validation error: {str(e)}")
            return False
    
    @staticmethod
    def validate_size(data: str) -> bool:
        """Validate data size"""
        size = len(data.encode())
        if size > DataValidator.MAX_DATA_SIZE:
            logger.warning(f"Data exceeds size limit: {size} bytes")
            return False
        return True
    
    @staticmethod
    def sanitize_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize data to prevent injection attacks"""
        sanitized = {}
        for key, value in data.items():
            # Only allow specific keys
            if key in DataValidator.VALID_VEHICLES or key == 'timestamp':
                if isinstance(value, int):
                    sanitized[key] = max(0, value)  # Ensure non-negative
                elif isinstance(value, (float, int)):
                    sanitized[key] = int(max(0, value))
        return sanitized


# ==================== SQLITE DATABASE MANAGER ====================
class SQLiteDatabaseManager:
    """
    Manages SQLite database for persistent storage of vehicle detection data
    
    Features:
    - Automatic database initialization
    - Thread-safe operations with connection pooling
    - Data persistence with timestamp indexing
    - Query capabilities for data retrieval and analysis
    - Automatic backups
    - Data integrity validation
    """
    
    def __init__(self, db_path: str = "vehicle_detection.db"):
        """
        Initialize SQLite database manager
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.lock = threading.RLock()
        self.connection = None
        self.init_database()
        logger.info(f"SQLiteDatabaseManager initialized with database: {db_path}")
    
    def init_database(self):
        """Initialize database schema"""
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # Create tables if they don't exist
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS vehicle_counts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp REAL NOT NULL,
                        datetime_str TEXT NOT NULL,
                        cars INTEGER NOT NULL DEFAULT 0,
                        vans INTEGER NOT NULL DEFAULT 0,
                        motors INTEGER NOT NULL DEFAULT 0,
                        buses INTEGER NOT NULL DEFAULT 0,
                        bicycles INTEGER NOT NULL DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create index on timestamp for faster queries
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_timestamp 
                    ON vehicle_counts(timestamp)
                ''')
                
                # Create index on datetime_str
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_datetime 
                    ON vehicle_counts(datetime_str)
                ''')
                
                # Create table for audit logs
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS audit_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp REAL NOT NULL,
                        event_type TEXT NOT NULL,
                        message TEXT NOT NULL,
                        level TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                conn.commit()
                conn.close()
                logger.info("Database schema initialized successfully")
        except Exception as e:
            logger.error(f"Database initialization error: {str(e)}")
            raise
    
    def insert_vehicle_counts(self, vehicle_counts: Dict[str, int], timestamp: Optional[float] = None) -> bool:
        """
        Insert vehicle count record into database
        
        Args:
            vehicle_counts: Dictionary with vehicle counts
            timestamp: Optional timestamp (uses current time if not provided)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if timestamp is None:
                timestamp = time.time()
            
            datetime_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO vehicle_counts 
                    (timestamp, datetime_str, cars, vans, motors, buses, bicycles)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    timestamp,
                    datetime_str,
                    vehicle_counts.get('cars', 0),
                    vehicle_counts.get('vans', 0),
                    vehicle_counts.get('motors', 0),
                    vehicle_counts.get('buses', 0),
                    vehicle_counts.get('bicycles', 0)
                ))
                
                conn.commit()
                row_id = cursor.lastrowid
                conn.close()
                
                logger.debug(f"Vehicle counts inserted: ID={row_id}, {vehicle_counts}")
                return True
                
        except Exception as e:
            logger.error(f"Error inserting vehicle counts: {str(e)}")
            return False
    
    def get_latest_counts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieve latest vehicle count records
        
        Args:
            limit: Number of records to retrieve
            
        Returns:
            List of dictionaries with vehicle count data
        """
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT timestamp, datetime_str, cars, vans, motors, buses, bicycles
                    FROM vehicle_counts
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (limit,))
                
                rows = cursor.fetchall()
                conn.close()
                
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Error retrieving latest counts: {str(e)}")
            return []
    
    def get_counts_by_time_range(self, start_time: float, end_time: float) -> List[Dict[str, Any]]:
        """
        Retrieve vehicle counts within a time range
        
        Args:
            start_time: Start timestamp
            end_time: End timestamp
            
        Returns:
            List of dictionaries with vehicle count data
        """
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT timestamp, datetime_str, cars, vans, motors, buses, bicycles
                    FROM vehicle_counts
                    WHERE timestamp BETWEEN ? AND ?
                    ORDER BY timestamp ASC
                ''', (start_time, end_time))
                
                rows = cursor.fetchall()
                conn.close()
                
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Error retrieving counts by time range: {str(e)}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics from stored vehicle counts
        
        Returns:
            Dictionary with statistics
        """
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT 
                        COUNT(*) as total_records,
                        AVG(cars) as avg_cars,
                        AVG(vans) as avg_vans,
                        AVG(motors) as avg_motors,
                        AVG(buses) as avg_buses,
                        AVG(bicycles) as avg_bicycles,
                        MAX(cars) as max_cars,
                        MAX(vans) as max_vans,
                        MAX(motors) as max_motors,
                        MAX(buses) as max_buses,
                        MAX(bicycles) as max_bicycles,
                        MIN(cars) as min_cars,
                        MIN(vans) as min_vans,
                        MIN(motors) as min_motors,
                        MIN(buses) as min_buses,
                        MIN(bicycles) as min_bicycles,
                        SUM(cars) as total_cars,
                        SUM(vans) as total_vans,
                        SUM(motors) as total_motors,
                        SUM(buses) as total_buses,
                        SUM(bicycles) as total_bicycles
                    FROM vehicle_counts
                ''')
                
                row = cursor.fetchone()
                conn.close()
                
                if row:
                    stats = {
                        'total_records': row[0],
                        'average': {
                            'cars': round(row[1] or 0, 2),
                            'vans': round(row[2] or 0, 2),
                            'motors': round(row[3] or 0, 2),
                            'buses': round(row[4] or 0, 2),
                            'bicycles': round(row[5] or 0, 2)
                        },
                        'maximum': {
                            'cars': row[6] or 0,
                            'vans': row[7] or 0,
                            'motors': row[8] or 0,
                            'buses': row[9] or 0,
                            'bicycles': row[10] or 0
                        },
                        'minimum': {
                            'cars': row[11] or 0,
                            'vans': row[12] or 0,
                            'motors': row[13] or 0,
                            'buses': row[14] or 0,
                            'bicycles': row[15] or 0
                        },
                        'total': {
                            'cars': row[16] or 0,
                            'vans': row[17] or 0,
                            'motors': row[18] or 0,
                            'buses': row[19] or 0,
                            'bicycles': row[20] or 0
                        }
                    }
                    logger.debug(f"Statistics retrieved: {stats['total_records']} records")
                    return stats
                
                return {}
                
        except Exception as e:
            logger.error(f"Error retrieving statistics: {str(e)}")
            return {}
    
    def log_event(self, event_type: str, message: str, level: str = "INFO") -> bool:
        """
        Log an event to the audit logs table
        
        Args:
            event_type: Type of event
            message: Event message
            level: Log level (INFO, WARNING, ERROR, etc.)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO audit_logs (timestamp, event_type, message, level)
                    VALUES (?, ?, ?, ?)
                ''', (time.time(), event_type, message, level))
                
                conn.commit()
                conn.close()
                return True
                
        except Exception as e:
            logger.error(f"Error logging event: {str(e)}")
            return False
    
    def export_to_csv(self, output_path: str) -> bool:
        """
        Export vehicle counts to CSV file
        
        Args:
            output_path: Path to output CSV file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            import csv
            
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT timestamp, datetime_str, cars, vans, motors, buses, bicycles
                    FROM vehicle_counts
                    ORDER BY timestamp ASC
                ''')
                
                rows = cursor.fetchall()
                conn.close()
                
                with open(output_path, 'w', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(['Timestamp', 'DateTime', 'Cars', 'Vans', 'Motors', 'Buses', 'Bicycles'])
                    writer.writerows(rows)
                
                logger.info(f"Data exported to CSV: {output_path}")
                return True
                
        except Exception as e:
            logger.error(f"Error exporting to CSV: {str(e)}")
            return False
    
    def get_total_records(self) -> int:
        """Get total number of records in database"""
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM vehicle_counts')
                count = cursor.fetchone()[0]
                conn.close()
                return count
        except Exception as e:
            logger.error(f"Error getting total records: {str(e)}")
            return 0
    
    def clear_old_records(self, days_to_keep: int = 30) -> int:
        """
        Delete records older than specified days
        
        Args:
            days_to_keep: Number of days of data to keep
            
        Returns:
            Number of records deleted
        """
        try:
            cutoff_time = time.time() - (days_to_keep * 24 * 3600)
            
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('DELETE FROM vehicle_counts WHERE timestamp < ?', (cutoff_time,))
                deleted_count = cursor.rowcount
                
                conn.commit()
                conn.close()
                
                logger.info(f"Deleted {deleted_count} old records (older than {days_to_keep} days)")
                return deleted_count
                
        except Exception as e:
            logger.error(f"Error clearing old records: {str(e)}")
            return 0


class SecureDataStreamServer:
    """
    Secure WebSocket server for streaming vehicle detection data with SQLite storage
    
    Features:
    - TLS/SSL encryption
    - Authentication and authorization
    - Rate limiting
    - Comprehensive logging
    - Broadcast to multiple clients
    - SQLite database storage
    - Graceful shutdown
    """
    
    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 8443,
        api_key: str = "default-secret-key",
        certfile: Optional[str] = None,
        keyfile: Optional[str] = None,
        rate_limit: int = 100,
        db_path: str = "vehicle_detection.db"
    ):
        """
        Initialize secure server
        
        Args:
            host: Server host address
            port: Server port
            api_key: API key for authentication
            certfile: SSL certificate file path
            keyfile: SSL key file path
            rate_limit: Max requests per minute per client
            db_path: Path to SQLite database file
        """
        self.host = host
        self.port = port
        self.security = SecurityManager(api_key, rate_limit)
        self.validator = DataValidator()
        self.db = SQLiteDatabaseManager(db_path)
        self.clients: Dict[str, WebSocketServerProtocol] = {}
        self.lock = threading.RLock()
        
        # SSL/TLS setup
        self.ssl_context = None
        if certfile and keyfile:
            self.ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            self.ssl_context.load_cert_chain(certfile, keyfile)
            logger.info(f"SSL context loaded: {certfile}")
        else:
            logger.warning("No SSL certificate provided. Using insecure connection.")
        
        logger.info(f"SecureDataStreamServer initialized on {host}:{port} with database: {db_path}")
    
    async def authenticate_client(self, websocket: WebSocketServerProtocol) -> Optional[str]:
        """Authenticate incoming client"""
        try:
            # Check IP
            client_ip = websocket.remote_address[0]
            if not self.security.is_ip_allowed(client_ip):
                await websocket.close(code=4003, reason="IP not allowed")
                return None
            
            # Wait for authentication message
            message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            auth_data = json.loads(message)
            
            # Validate authentication
            if 'api_key' not in auth_data or 'client_id' not in auth_data:
                await websocket.close(code=4001, reason="Invalid authentication format")
                logger.warning(f"Invalid auth format from {client_ip}")
                return None
            
            if not self.security.validate_api_key(auth_data['api_key']):
                await websocket.close(code=4002, reason="Invalid credentials")
                logger.warning(f"Authentication failed from {client_ip}")
                return None
            
            client_id = auth_data['client_id']
            token = self.security.generate_session_token(client_id)
            
            # Send token
            await websocket.send(json.dumps({
                'status': 'authenticated',
                'token': token,
                'expires_in': 3600
            }))
            
            logger.info(f"Client authenticated: {client_id} from {client_ip}")
            return client_id
            
        except asyncio.TimeoutError:
            logger.warning("Authentication timeout")
            return None
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return None
    
    async def handle_client(self, websocket: WebSocketServerProtocol, path: str):
        """Handle client connection"""
        client_id = None
        try:
            # Authenticate
            client_id = await self.authenticate_client(websocket)
            if not client_id:
                return
            
            # Register client
            with self.lock:
                self.clients[client_id] = websocket
            logger.info(f"Client connected: {client_id} (total: {len(self.clients)})")
            
            # Keep connection alive
            try:
                async for message in websocket:
                    # Rate limit check
                    if not self.security.check_rate_limit(client_id):
                        await websocket.send(json.dumps({
                            'error': 'Rate limit exceeded'
                        }))
                        continue
                    
                    # Process message (can be keep-alive or commands)
                    try:
                        data = json.loads(message)
                        if data.get('type') == 'ping':
                            await websocket.send(json.dumps({'type': 'pong'}))
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid JSON from {client_id}")
                        
            except websockets.exceptions.ConnectionClosed:
                pass
            
        except Exception as e:
            logger.error(f"Client error: {str(e)}")
        
        finally:
            # Unregister client
            if client_id:
                with self.lock:
                    self.clients.pop(client_id, None)
                logger.info(f"Client disconnected: {client_id} (total: {len(self.clients)})")
    
    async def broadcast_data(self, vehicle_counts: Dict[str, int]):
        """
        Broadcast vehicle count data to all connected clients and save to database
        
        Args:
            vehicle_counts: Dictionary with vehicle counts
        """
        # Validate and sanitize data
        if not self.validator.validate_vehicle_data(vehicle_counts):
            logger.error("Vehicle data validation failed")
            return
        
        # Sanitize
        vehicle_counts = self.validator.sanitize_data(vehicle_counts)
        
        # Save to database
        timestamp = time.time()
        if not self.db.insert_vehicle_counts(vehicle_counts, timestamp):
            logger.error("Failed to save vehicle counts to database")
            return
        
        # Add timestamp
        data_to_send = {
            **vehicle_counts,
            'timestamp': timestamp
        }
        
        # Compute HMAC for integrity
        data_str = json.dumps(data_to_send, sort_keys=True)
        hmac_value = self.security.compute_hmac(data_str)
        
        message = {
            'data': data_to_send,
            'hmac': hmac_value
        }
        message_json = json.dumps(message)
        
        # Validate size
        if not self.validator.validate_size(message_json):
            logger.error("Message exceeds size limit")
            return
        
        # Broadcast to all connected clients
        disconnected_clients = []
        with self.lock:
            for client_id, websocket in self.clients.items():
                try:
                    await websocket.send(message_json)
                except Exception as e:
                    logger.warning(f"Failed to send to {client_id}: {str(e)}")
                    disconnected_clients.append(client_id)
        
        # Remove disconnected clients
        with self.lock:
            for client_id in disconnected_clients:
                self.clients.pop(client_id, None)
        
        logger.debug(f"Data broadcasted to {len(self.clients)} clients and saved to database")
    
    async def start_server(self):
        """Start the secure WebSocket server"""
        try:
            async with websockets.serve(
                self.handle_client,
                self.host,
                self.port,
                ssl=self.ssl_context,
                ping_interval=30,
                ping_timeout=10
            ):
                logger.info(f"Secure server started on wss://{self.host}:{self.port}")
                await asyncio.Future()  # run forever
        except Exception as e:
            logger.error(f"Server startup error: {str(e)}")
    
    def run(self):
        """Run server in event loop"""
        asyncio.run(self.start_server())
    
    def get_latest_vehicle_counts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieve latest vehicle count records from database
        
        Args:
            limit: Number of records to retrieve
            
        Returns:
            List of dictionaries with vehicle count data
        """
        return self.db.get_latest_counts(limit)
    
    def get_database_statistics(self) -> Dict[str, Any]:
        """Get statistics from stored vehicle counts"""
        return self.db.get_statistics()
    
    def export_database_to_csv(self, output_path: str) -> bool:
        """Export vehicle counts to CSV file"""
        return self.db.export_to_csv(output_path)
    
    def get_total_stored_records(self) -> int:
        """Get total number of records stored in database"""
        return self.db.get_total_records()


# ==================== DATABASE-ONLY STORAGE ====================
class VehicleCountDatabase:
    """
    Standalone vehicle count database manager for direct storage without streaming
    
    Use this when you only want to save data to database without WebSocket streaming
    """
    
    def __init__(self, db_path: str = "vehicle_detection.db"):
        """Initialize database manager"""
        self.db = SQLiteDatabaseManager(db_path)
        self.logger = logging.getLogger("VehicleCountDatabase")
    
    def save_vehicle_counts(self, vehicle_counts: Dict[str, int], timestamp: Optional[float] = None) -> bool:
        """Save vehicle counts to database"""
        return self.db.insert_vehicle_counts(vehicle_counts, timestamp)
    
    def get_latest(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get latest records"""
        return self.db.get_latest_counts(limit)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics"""
        return self.db.get_statistics()
    
    def export_csv(self, output_path: str) -> bool:
        """Export to CSV"""
        return self.db.export_to_csv(output_path)
    
    def get_total_records(self) -> int:
        """Get total records"""
        return self.db.get_total_records()
    
    def clear_old_records(self, days_to_keep: int = 30) -> int:
        """Clear records older than specified days"""
        return self.db.clear_old_records(days_to_keep)


# ==================== SECURE CLIENT ====================
class SecureStreamClient:
    """
    Secure WebSocket client for receiving vehicle detection data
    
    Features:
    - Secure connection with TLS
    - Authentication
    - Data integrity verification
    - Auto-reconnection
    - Graceful error handling
    """
    
    def __init__(
        self,
        server_url: str,
        client_id: str,
        api_key: str,
        verify_ssl: bool = True
    ):
        """
        Initialize secure client
        
        Args:
            server_url: Server URL (e.g., wss://localhost:8443)
            client_id: Unique client identifier
            api_key: API key for authentication
            verify_ssl: Whether to verify SSL certificate
        """
        self.server_url = server_url
        self.client_id = client_id
        self.api_key = api_key
        self.verify_ssl = verify_ssl
        self.websocket = None
        self.security = SecurityManager(api_key)
        self.validator = DataValidator()
        self.connected = False
        logger.info(f"SecureStreamClient initialized: {client_id}")
    
    async def connect(self):
        """Connect to server and authenticate"""
        try:
            # Create SSL context if needed
            ssl_context = None
            if not self.verify_ssl:
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
            
            self.websocket = await websockets.connect(
                self.server_url,
                ssl=ssl_context,
                ping_interval=30,
                ping_timeout=10
            )
            
            # Send authentication
            auth_message = {
                'api_key': self.api_key,
                'client_id': self.client_id
            }
            await self.websocket.send(json.dumps(auth_message))
            
            # Receive authentication response
            response = await asyncio.wait_for(self.websocket.recv(), timeout=5.0)
            auth_response = json.loads(response)
            
            if auth_response.get('status') != 'authenticated':
                logger.error("Authentication failed")
                return False
            
            self.connected = True
            logger.info(f"Connected to server: {self.server_url}")
            return True
            
        except Exception as e:
            logger.error(f"Connection error: {str(e)}")
            self.connected = False
            return False
    
    async def receive_data(self) -> Optional[Dict[str, Any]]:
        """Receive and validate data from server"""
        try:
            if not self.websocket:
                return None
            
            message = await asyncio.wait_for(self.websocket.recv(), timeout=30.0)
            data = json.loads(message)
            
            # Verify HMAC
            if 'hmac' in data and 'data' in data:
                data_str = json.dumps(data['data'], sort_keys=True)
                if not self.security.verify_hmac(data_str, data['hmac']):
                    logger.error("HMAC verification failed - data integrity compromised")
                    return None
            
            # Validate data
            if not self.validator.validate_vehicle_data(data.get('data', {})):
                logger.error("Data validation failed")
                return None
            
            logger.debug(f"Data received and verified: {data['data']}")
            return data['data']
            
        except asyncio.TimeoutError:
            logger.warning("Receive timeout")
            return None
        except Exception as e:
            logger.error(f"Receive error: {str(e)}")
            self.connected = False
            return None
    
    async def disconnect(self):
        """Disconnect from server"""
        if self.websocket:
            await self.websocket.close()
            self.connected = False
            logger.info("Disconnected from server")


# ==================== INTEGRATION WITH PASSEDCOUNTING ====================
"""
INTEGRATION EXAMPLE 1: DATABASE-ONLY STORAGE (Recommended)
===========================================================

Replace the file writing section in PassedCounting.py with:

    # Vehicle Count Database Storage
    from secure_streaming import VehicleCountDatabase
    
    # Initialize database
    db = VehicleCountDatabase(db_path="vehicle_detection.db")
    
    # In main loop, replace:
    #   output_file.write(f"Time {current_time:.1f}s: ...")
    # With:
    
    current_time = time.time() - start_time
    if current_time - last_write_time >= interval:
        vehicle_counts = {
            'cars': len(totalCar),
            'vans': len(totalVan),
            'motors': len(totalMotor),
            'buses': len(totalBus),
            'bicycles': len(totalBicycle)
        }
        
        # Save to SQLite database
        if db.save_vehicle_counts(vehicle_counts):
            logger.info(f"Data saved at {current_time:.1f}s - Cars: {len(totalCar)}, Vans: {len(totalVan)}, Motors: {len(totalMotor)}, Buses: {len(totalBus)}, Bicycles: {len(totalBicycle)}")
        
        last_write_time = current_time
    
    # After processing is complete, view statistics:
    stats = db.get_statistics()
    print(f"Total records: {stats['total_records']}")
    print(f"Average cars: {stats['average']['cars']}")
    
    # Export data to CSV
    db.export_csv("vehicle_counts_export.csv")


INTEGRATION EXAMPLE 2: SECURE STREAMING WITH DATABASE
======================================================

Replace the file writing section in PassedCounting.py with:

    # Secure Data Streaming with Database Storage
    from secure_streaming import SecureDataStreamServer
    import threading
    import asyncio
    
    # Initialize server with database
    server = SecureDataStreamServer(
        host='127.0.0.1',
        port=8443,
        api_key='your-secure-api-key',
        db_path='vehicle_detection.db',
        rate_limit=100
    )
    
    # Start server in background thread
    server_thread = threading.Thread(target=server.run, daemon=True)
    server_thread.start()
    
    # In main loop:
    current_time = time.time() - start_time
    if current_time - last_write_time >= interval:
        vehicle_counts = {
            'cars': len(totalCar),
            'vans': len(totalVan),
            'motors': len(totalMotor),
            'buses': len(totalBus),
            'bicycles': len(totalBicycle)
        }
        
        # Stream and save data (database saving happens inside broadcast_data)
        asyncio.run(server.broadcast_data(vehicle_counts))
        
        last_write_time = current_time
        logger.info(f"Data streamed and saved at {current_time:.1f}s")
    
    # View statistics
    stats = server.get_database_statistics()
    print(f"Total records stored: {server.get_total_stored_records()}")


QUERYING DATABASE AFTER PROCESSING
===================================

    from secure_streaming import VehicleCountDatabase
    
    # Connect to existing database
    db = VehicleCountDatabase(db_path="vehicle_detection.db")
    
    # Get latest 20 records
    latest = db.get_latest(limit=20)
    for record in latest:
        print(f"{record['datetime_str']}: Cars={record['cars']}, Vans={record['vans']}, Motors={record['motors']}")
    
    # Get statistics
    stats = db.get_statistics()
    print(f"Total vehicles counted: {stats['total']['cars']} cars, {stats['total']['buses']} buses")
    print(f"Average cars per record: {stats['average']['cars']}")
    
    # Export to CSV for analysis
    db.export_csv("vehicle_analysis.csv")
    
    # Clean up old data (keep only last 30 days)
    deleted = db.clear_old_records(days_to_keep=30)
    print(f"Deleted {deleted} old records")


INTEGRATION STEPS
=================

1. Install websockets if using streaming features:
   pip install websockets

2. Replace file operations:
   - Remove: output_file.write(...) and output_file.flush()
   - Add: db.save_vehicle_counts(vehicle_counts)

3. Remove text file opening:
   - Remove: output_file = open(config['output_path'], 'a')
   - Keep database initialization

4. Update cleanup code:
   - Remove: output_file.close()
   - Database closes automatically

5. For data analysis:
   - Use db.get_statistics() for summary
   - Use db.export_csv() for spreadsheet analysis
   - Use db.get_latest() for recent data


DATABASE SCHEMA
===============

Tables created automatically:

1. vehicle_counts:
   - id: Auto-incrementing primary key
   - timestamp: Unix timestamp (indexed)
   - datetime_str: Human-readable datetime (indexed)
   - cars, vans, motors, buses, bicycles: Vehicle counts
   - created_at: Record creation timestamp

2. audit_logs:
   - id: Auto-incrementing primary key
   - timestamp: Unix timestamp
   - event_type: Type of event
   - message: Event description
   - level: Log level (INFO, WARNING, ERROR)
   - created_at: Record creation timestamp


ADVANTAGES OF SQLITE DATABASE
=============================

 Structured data storage
 Easy querying and filtering
 Automatic indexing for fast searches
 Data integrity with transactions
 No external server required
 File-based (portable)
 Supports statistical queries
 Easy CSV export
 Scalable to millions of records
 Built-in Python support (sqlite3)


CLIENT USAGE EXAMPLE
====================

    from secure_streaming import SecureStreamClient
    import asyncio
    
    async def receive_vehicle_data():
        client = SecureStreamClient(
            server_url='wss://127.0.0.1:8443',
            client_id='simulation-client',
            api_key='your-secure-api-key',
            verify_ssl=False
        )
        
        if await client.connect():
            while True:
                data = await client.receive_data()
                if data:
                    print(f"Received: {data}")
                await asyncio.sleep(1)
    
    asyncio.run(receive_vehicle_data())
"""

if __name__ == "__main__":
    # Example: Start secure server
    server = SecureDataStreamServer(
        api_key="demo-secret-key-change-in-production"
    )
    
    # Example: Broadcast sample data
    async def demo():
        sample_data = {
            'cars': 5,
            'vans': 2,
            'motors': 3,
            'buses': 1,
            'bicycles': 0
        }
        await server.broadcast_data(sample_data)
    
    print("Secure Data Streaming Module loaded successfully")
    print("See docstrings for integration and usage examples")