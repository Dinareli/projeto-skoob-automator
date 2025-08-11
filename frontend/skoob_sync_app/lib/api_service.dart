import 'package:http/http.dart' as http;
import 'dart:convert';

class ApiService {
  final String baseUrl = 'https://projeto-skoob-automator-production.up.railway.app';

  Future<String> syncSkoobProgress({
    required String skoobUser,
    required String skoobPass,
    required String readwiseToken,
    required String bookTitle,
    required int statusId,
  }) async {
    // Monta o corpo exatamente como a API espera
    final Map<String, dynamic> body = {
      "skoob_user": skoobUser,
      "skoob_pass": skoobPass,
      "readwise_token": readwiseToken,
      "book_title": bookTitle,
      "status_id": statusId,
    };

    print("🔍 Enviando para API: $body"); // Debug

    final response = await http.post(
  Uri.parse('https://projeto-skoob-automator-production.up.railway.app/sync'),
  headers: {
    'Content-Type': 'application/x-www-form-urlencoded',
  },
  body: {
    'skoob_user': skoobUser,
    'skoob_pass': skoobPass,
    'readwise_token': readwiseToken,
    'book_title': bookTitle,
    'status_id': statusId.toString(),
  },
);

    print("📡 Status: ${response.statusCode}");
    print("📦 Resposta: ${response.body}");

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      return data['message'] ?? 'Sincronização concluída com sucesso.';
    } else {
      final data = jsonDecode(response.body);
      throw Exception(data['error'] ?? 'Erro desconhecido.');
    }
  }
}
