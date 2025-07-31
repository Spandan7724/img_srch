import 'dart:async';
import 'dart:convert';
import 'package:web_socket_channel/web_socket_channel.dart';

enum IndexingStatus {
  idle,
  indexing,
  completed,
  error,
}

class IndexingStatusData {
  final IndexingStatus status;
  final String? folder;
  final String? currentFile;
  final int processed;
  final int total;
  final double percentage;
  final int totalIndexed;
  final String? message;
  final String? error;

  IndexingStatusData({
    required this.status,
    this.folder,
    this.currentFile,
    this.processed = 0,
    this.total = 0,
    this.percentage = 0.0,
    this.totalIndexed = 0,
    this.message,
    this.error,
  });

  factory IndexingStatusData.idle() => IndexingStatusData(status: IndexingStatus.idle);
}

class WebSocketService {
  static const String _wsUrl = 'ws://127.0.0.1:8000/ws';
  WebSocketChannel? _channel;
  StreamSubscription? _subscription;
  
  final StreamController<IndexingStatusData> _statusController = 
      StreamController<IndexingStatusData>.broadcast();
  
  Stream<IndexingStatusData> get statusStream => _statusController.stream;
  
  bool _isConnected = false;
  bool get isConnected => _isConnected;
  
  Timer? _reconnectTimer;

  void connect() {
    _connectWithRetry();
  }

  void _connectWithRetry() {
    try {
      _channel = WebSocketChannel.connect(Uri.parse(_wsUrl));
      _isConnected = true;
      
      _subscription = _channel!.stream.listen(
        (data) {
          _handleMessage(data);
        },
        onError: (error) {
          print('WebSocket error: $error');
          _handleDisconnection();
        },
        onDone: () {
          print('WebSocket disconnected');
          _handleDisconnection();
        },
      );
      
      print('WebSocket connected');
    } catch (e) {
      print('WebSocket connection failed: $e');
      _scheduleReconnect();
    }
  }

  void _handleMessage(dynamic data) {
    try {
      final Map<String, dynamic> message = jsonDecode(data);
      final String type = message['type'] ?? '';
      
      IndexingStatusData statusData;
      
      switch (type) {
        case 'indexing_started':
          statusData = IndexingStatusData(
            status: IndexingStatus.indexing,
            folder: message['folder'],
            message: 'Indexing started...',
          );
          break;
          
        case 'indexing_progress':
          statusData = IndexingStatusData(
            status: IndexingStatus.indexing,
            folder: message['folder'],
            currentFile: message['current_file'],
            processed: message['processed'] ?? 0,
            total: message['total'] ?? 0,
            percentage: (message['percentage'] ?? 0.0).toDouble(),
          );
          break;
          
        case 'indexing_completed':
          statusData = IndexingStatusData(
            status: IndexingStatus.completed,
            folder: message['folder'],
            totalIndexed: message['total_indexed'] ?? 0,
            message: message['message'] ?? 'Indexing completed',
          );
          break;
          
        case 'indexing_error':
          statusData = IndexingStatusData(
            status: IndexingStatus.error,
            folder: message['folder'],
            error: message['error'],
          );
          break;
          
        default:
          return; // Ignore unknown message types
      }
      
      _statusController.add(statusData);
    } catch (e) {
      print('Error parsing WebSocket message: $e');
    }
  }

  void _handleDisconnection() {
    _isConnected = false;
    _subscription?.cancel();
    _channel = null;
    _scheduleReconnect();
  }

  void _scheduleReconnect() {
    _reconnectTimer?.cancel();
    _reconnectTimer = Timer(const Duration(seconds: 5), () {
      print('Attempting to reconnect WebSocket...');
      _connectWithRetry();
    });
  }

  void disconnect() {
    _reconnectTimer?.cancel();
    _subscription?.cancel();
    _channel?.sink.close();
    _isConnected = false;
  }

  void dispose() {
    disconnect();
    _statusController.close();
  }
}