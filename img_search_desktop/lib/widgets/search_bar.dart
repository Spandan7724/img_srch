import 'package:flutter/material.dart';
import '../services/websocket_service.dart';

class SearchBar extends StatelessWidget {
  final ValueChanged<String> onSubmitted;
  final VoidCallback onClear;
  final VoidCallback onFolderPressed;
  final IndexingStatusData indexingStatus;

  const SearchBar({
    super.key,
    required this.onSubmitted,
    required this.onClear,
    required this.onFolderPressed,
    required this.indexingStatus,
  });

  @override
  Widget build(BuildContext context) {
    // Determine placeholder text based on indexing status
    String placeholderText;
    switch (indexingStatus.status) {
      case IndexingStatus.indexing:
        placeholderText = "Indexing in progress...";
        break;
      case IndexingStatus.completed:
        placeholderText = "Indexing complete - Type to search images";
        break;
      case IndexingStatus.error:
        placeholderText = "Indexing failed - Type to search images";
        break;
      default:
        placeholderText = "Type to search images...";
        break;
    }
    
    // Determine folder icon color based on indexing status
    Color folderIconColor;
    switch (indexingStatus.status) {
      case IndexingStatus.completed:
        folderIconColor = Colors.green;
        break;
      case IndexingStatus.indexing:
        folderIconColor = Colors.orange;
        break;
      case IndexingStatus.error:
        folderIconColor = Colors.red;
        break;
      default:
        folderIconColor = Colors.white;
        break;
    }

    return Padding(
      padding: const EdgeInsets.all(10),
      child: Row(
        children: [
          Expanded(
            child: TextField(
              style: const TextStyle(color: Colors.white),
              decoration: InputDecoration(
                hintText: placeholderText,
                hintStyle: TextStyle(color: Colors.white60),
                filled: true,
                fillColor: Colors.black54,
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(4),
                  borderSide: BorderSide.none,
                ),
              ),
              onSubmitted: onSubmitted,
              onChanged: (v) {
                if (v.isEmpty) onClear();
              },
            ),
          ),
          const SizedBox(width: 8),
          IconButton(
            icon: Icon(Icons.folder, color: folderIconColor),
            onPressed: onFolderPressed,
          ),
        ],
      ),
    );
  }
}
