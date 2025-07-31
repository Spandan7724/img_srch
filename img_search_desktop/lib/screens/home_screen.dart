// lib/screens/home_screen.dart

import 'package:flutter/material.dart' hide SearchBar;
import 'package:window_manager/window_manager.dart';
import '../widgets/search_bar.dart';
import '../widgets/result_grid.dart';
import '../services/api.dart';
import '../services/websocket_service.dart';
import 'package:file_picker/file_picker.dart';
import 'dart:async';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});
  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  List<Item> results = [];
  bool expanded = false;
  
  // WebSocket and indexing status
  final WebSocketService _webSocketService = WebSocketService();
  StreamSubscription<IndexingStatusData>? _statusSubscription;
  IndexingStatusData _indexingStatus = IndexingStatusData.idle();

  @override
  void initState() {
    super.initState();
    _webSocketService.connect();
    _statusSubscription = _webSocketService.statusStream.listen((status) {
      setState(() {
        _indexingStatus = status;
      });
      
      // Auto-collapse window when indexing is completed
      if (status.status == IndexingStatus.completed) {
        Future.delayed(const Duration(seconds: 2), () {
          if (results.isEmpty) {
            toggleWindowSize(false);
          }
        });
      }
    });
  }

  @override
  void dispose() {
    _statusSubscription?.cancel();
    _webSocketService.dispose();
    super.dispose();
  }

  void toggleWindowSize(bool expand) {
    final height = expand ? 300.0 : 80.0;
    windowManager.setSize(Size(600, height));
  }

  Future<void> doSearch(String query) async {
    setState(() {
      results = [];
      // Reset indexing status when user starts searching
      if (_indexingStatus.status == IndexingStatus.completed) {
        _indexingStatus = IndexingStatusData.idle();
      }
    });
    toggleWindowSize(true);
    final items = await Api.search(query);
    setState(() => results = items);
  }

  Future<void> pickFolder() async {
    String? path = await FilePicker.platform.getDirectoryPath();
    if (path == null) return;
    
    setState(() {
      results = [];
      _indexingStatus = IndexingStatusData.idle();
    });
    
    final ok = await Api.indexFolder(path);
    if (ok) {
      await Api.updateImages();
      // Note: The WebSocket will handle status updates and UI changes
      // No need to manually collapse the window here
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black.withOpacity(0.85),
      body: Stack(
        children: [
          Column(
            children: [
              SearchBar(
                onSubmitted: doSearch,
                onClear: () {
                  setState(() {
                    results = [];
                    // Reset indexing status when clearing
                    if (_indexingStatus.status == IndexingStatus.completed) {
                      _indexingStatus = IndexingStatusData.idle();
                    }
                  });
                  toggleWindowSize(false);
                },
                onFolderPressed: pickFolder,
                indexingStatus: _indexingStatus,
              ),
              Expanded(child: ResultGrid(
                items: results, 
                showPlaceholder: expanded,
                indexingStatus: _indexingStatus,
              )),
            ],
          ),
          // Draggable “handle” in top-left corner
          Positioned(
            left: 0,
            top: 0,
            child: DragToMoveArea(child: SizedBox(width: 40, height: 40)),
          ),
        ],
      ),
    );
  }
}
