import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/dossier_model.dart';

class ApiService {
  String baseUrl;

  ApiService({this.baseUrl = 'http://localhost:8000'});

  Future<DossierModel> analyzeClaim({String? claim, String? url}) async {
    final endpoint = Uri.parse('$baseUrl/analyze');
    
    final payload = <String, dynamic>{};
    if (claim != null && claim.trim().isNotEmpty) {
      payload['claim'] = claim.trim();
    }
    if (url != null && url.trim().isNotEmpty) {
      payload['url'] = url.trim();
    }

    if (payload.isEmpty) {
      throw Exception('Either claim text or URL must be provided');
    }

    try {
      final response = await http.post(
        endpoint,
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: jsonEncode(payload),
      ).timeout(const Duration(seconds: 45));

      if (response.statusCode == 200) {
        final Map<String, dynamic> body = jsonDecode(utf8.decode(response.bodyBytes));
        return DossierModel.fromJson(body);
      } else {
        throw Exception('API error (${response.statusCode}): ${response.body}');
      }
    } catch (e) {
      throw Exception('Failed to communicate with TruthTrace backend: $e');
    }
  }
}
