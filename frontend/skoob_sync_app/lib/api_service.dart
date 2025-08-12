import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;

class ApiService {
  static const String _baseUrl = 'https://projeto-skoob-automator-production.up.railway.app';

  Future<String> syncSkoobProgress({
    required String? skoobUser,
    required String? skoobPass,
    required String? readwiseToken,
    required String bookTitle,
    required int statusId,
  }) async {
    final Uri syncUri = Uri.parse('$_baseUrl/sync');
    
    final Map<String, dynamic> body = {
      'skoob_user': skoobUser,
      'skoob_pass': skoobPass,
      'readwise_token': readwiseToken,
      'book_title': bookTitle,
      'status_id': statusId,
    };

    try {
      final response = await http.post(
        syncUri,
        headers: {'Content-Type': 'application/json; charset=UTF-8'},
        body: json.encode(body),
      );

      final result = json.decode(utf8.decode(response.bodyBytes));
      
      print('Status Code da Sincronização: ${response.statusCode}');
      print('Resposta da Sincronização: $result');

      if (response.statusCode == 200 && result['status'] == 'success') {
        return result['message'];
      } else {
        throw Exception(result['message'] ?? 'Ocorreu um erro desconhecido na API.');
      }
    } on SocketException {
      throw Exception('Não foi possível conectar ao servidor. Verifique a sua internet.');
    } catch (e) {
      print('Erro capturado no ApiService: $e');
      throw Exception(e.toString().replaceAll('Exception: ', ''));
    }
  }
}
