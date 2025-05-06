import 'dart:convert';
import 'package:http/http.dart' as http;

class Item {
  final String path, fullUrl;
  final double score;
  Item(this.path, this.fullUrl, this.score);
  factory Item.fromJson(Map<String, dynamic> j) =>
      Item(j['path'], j['full_url'], (j['score'] as num).toDouble());
}

class Api {
  static const _base = 'http://127.0.0.1:8000';

  static Future<List<Item>> search(String q) async {
    final res = await http.post(
      Uri.parse("$_base/search/"),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'query': q}),
    );
    if (res.statusCode != 200) return [];
    final list = jsonDecode(res.body) as List;
    return list.map((e) => Item.fromJson(e)).toList();
  }

  static Future<void> openImage(String path) async {
    await http.post(
      Uri.parse("$_base/open-image/"),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'path': path}),
    );
  }

  static Future<bool> indexFolder(String folder) async {
    final res = await http.post(
      Uri.parse("$_base/folders"),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'folders': [folder],
      }),
    );
    return res.statusCode == 200;
  }

  static Future<void> updateImages() async {
    await http.post(Uri.parse("$_base/update-images/"));
  }
}
