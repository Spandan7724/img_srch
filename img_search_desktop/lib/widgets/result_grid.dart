// lib/widgets/result_grid.dart
import 'package:flutter/material.dart';
import '../services/api.dart';
import '../services/websocket_service.dart';

class ResultGrid extends StatelessWidget {
  /// Search results returned by the backend.
  final List<Item> items;

  /// Whether to show the "No results" placeholder when [items] is empty.
  /// Pass `false` while the launcher is collapsed to avoid stray pixels.
  final bool showPlaceholder;
  
  /// Current indexing status for displaying progress
  final IndexingStatusData indexingStatus;

  const ResultGrid({
    Key? key, 
    required this.items, 
    this.showPlaceholder = true,
    required this.indexingStatus,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    // ── Show indexing progress if indexing is in progress ─────────────────
    if (items.isEmpty && indexingStatus.status == IndexingStatus.indexing) {
      return showPlaceholder 
          ? Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  CircularProgressIndicator(
                    color: Colors.orange,
                    value: indexingStatus.total > 0 
                        ? indexingStatus.processed / indexingStatus.total 
                        : null,
                  ),
                  const SizedBox(height: 8),
                  Text(
                    "Indexing: ${indexingStatus.processed}/${indexingStatus.total} images",
                    style: const TextStyle(color: Colors.white70, fontSize: 12),
                  ),
                  if (indexingStatus.percentage > 0)
                    Text(
                      "${indexingStatus.percentage.toStringAsFixed(1)}%",
                      style: const TextStyle(color: Colors.white60, fontSize: 10),
                    ),
                ],
              ),
            )
          : const SizedBox.shrink();
    }
    
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
          child: Column(
            children: [
              Expanded(child: Image.network(it.fullUrl, fit: BoxFit.cover)),
              Text(
                "${(it.score * 100).toStringAsFixed(1)}%",
                style: const TextStyle(color: Colors.white70, fontSize: 12),
              ),
            ],
          ),
        );
      },
    );
  }
}
