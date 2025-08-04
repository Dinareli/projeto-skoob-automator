import 'dart:convert';
import 'dart:io'; // Para exceções de rede como 'SocketException'
import 'package:http/http.dart' as http;

class ApiService {
  // URL base da sua API no Railway.
  static const String _baseUrl = 'https://projeto-skoob-automator-production.up.railway.app';

  /// Envia os dados para a API para sincronizar o progresso do livro.
  Future<String> syncSkoobProgress({
    required String? skoobUser,
    required String? skoobPass,
    required String? readwiseToken,
    required String bookTitle,
    required int statusId,
  }) async {
    // Monta a URL completa, incluindo o endpoint /sync
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

      // Usar utf8.decode para garantir que caracteres especiais (acentos) sejam lidos corretamente.
      final result = json.decode(utf8.decode(response.bodyBytes));
      
      print('Status Code: ${response.statusCode}');
      print('Response Body: $result');

      if (response.statusCode == 200 && result['status'] == 'success') {
        return result['message']; // Retorna a mensagem de sucesso da API.
      } else {
        // Lança um erro com a mensagem de erro vinda da API.
        throw Exception(result['message'] ?? 'Ocorreu um erro desconhecido na API.');
      }
    } on SocketException {
      // Erro específico para quando o app não consegue se conectar à internet.
      throw Exception('Não foi possível conectar ao servidor. Verifique sua internet.');
    } catch (e) {
      // Pega qualquer outro erro (como o de parsing do JSON) e o relança de forma limpa.
      print('Erro capturado no ApiService: $e');
      throw Exception(e.toString().replaceAll('Exception: ', ''));
    }
  }
}