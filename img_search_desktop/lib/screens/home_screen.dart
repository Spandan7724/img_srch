// lib/screens/home_screen.dart

import 'package:flutter/material.dart' hide SearchBar;
import 'package:window_manager/window_manager.dart';
import '../widgets/search_bar.dart';
import '../widgets/result_grid.dart';
import '../services/api.dart';
import 'package:file_picker/file_picker.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({Key? key}) : super(key: key);
  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  List<Item> results = [];
  bool expanded = false;

  void toggleWindowSize(bool expand) {
    final height = expand ? 300.0 : 80.0;
    windowManager.setSize(Size(600, height));
  }

  Future<void> doSearch(String query) async {
    setState(() => results = []);
    toggleWindowSize(true);
    final items = await Api.search(query);
    setState(() => results = items);
  }

  Future<void> pickFolder() async {
    String? path = await FilePicker.platform.getDirectoryPath();
    if (path == null) return;
    setState(() => results = []);
    final ok = await Api.indexFolder(path);
    if (ok) {
      await Api.updateImages();
      await Future.delayed(const Duration(seconds: 1));
      toggleWindowSize(false);
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
                  setState(() => results = []);
                  toggleWindowSize(false);
                },
                onFolderPressed: pickFolder,
              ),
              Expanded(child: ResultGrid(items: results, showPlaceholder: expanded)),
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
