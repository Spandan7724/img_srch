import 'package:flutter/material.dart';

class SearchBar extends StatelessWidget {
  final ValueChanged<String> onSubmitted;
  final VoidCallback onClear;
  final VoidCallback onFolderPressed;

  const SearchBar({
    super.key,
    required this.onSubmitted,
    required this.onClear,
    required this.onFolderPressed,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(10),
      child: Row(
        children: [
          Expanded(
            child: TextField(
              style: const TextStyle(color: Colors.white),
              decoration: InputDecoration(
                hintText: "Type to search images...",
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
            icon: const Icon(Icons.folder, color: Colors.white),
            onPressed: onFolderPressed,
          ),
        ],
      ),
    );
  }
}
