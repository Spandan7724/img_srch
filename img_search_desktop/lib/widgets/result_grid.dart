// lib/widgets/result_grid.dart
import 'package:flutter/material.dart';
import '../services/api.dart';

class ResultGrid extends StatelessWidget {
  /// Search results returned by the backend.
  final List<Item> items;

  /// Whether to show the “No results” placeholder when [items] is empty.
  /// Pass `false` while the launcher is collapsed to avoid stray pixels.
  final bool showPlaceholder;

  const ResultGrid({Key? key, required this.items, this.showPlaceholder = true})
    : super(key: key);

  @override
  Widget build(BuildContext context) {
    // ── Empty state ───────────────────────────────────────────────────────
    if (items.isEmpty) {
      return showPlaceholder
          ? Center(
            child: Text("No results", style: TextStyle(color: Colors.white60)),
          )
          : const SizedBox.shrink(); // render nothing when placeholder hidden
    }

    // ── Grid of thumbnails ────────────────────────────────────────────────
    return GridView.builder(
      padding: const EdgeInsets.all(4),
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 5,
        mainAxisSpacing: 4,
        crossAxisSpacing: 4,
        childAspectRatio: 1,
      ),
      itemCount: items.length,
      itemBuilder: (_, i) {
        final it = items[i];
        return GestureDetector(
          onTap: () => Api.openImage(it.path),
          child: Container(
            children: [

              ),
            ],
          ),
        );
      },
    );
  }
}
