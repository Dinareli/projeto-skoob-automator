// //api_service.dart
// import 'dart:convert';
// import 'dart:io';
// import 'package:http/http.dart' as http;

// class ApiService {
//   static const String _baseUrl = 'https://projeto-skoob-automator-production.up.railway.app';

//   Future<String> syncSkoobProgress({
//     required String? skoobUser,
//     required String? skoobPass,
//     required String? readwiseToken,
//     required String bookTitle,
//     required int statusId,
//   }) async {
//     final Uri syncUri = Uri.parse('$_baseUrl/sync');
    
//     final Map<String, dynamic> body = {
//       'skoob_user': skoobUser,
//       'skoob_pass': skoobPass,
//       'readwise_token': readwiseToken,
//       'book_title': bookTitle,
//       'status_id': statusId,
//     };

//     try {
//       final response = await http.post(
//         syncUri,
//         headers: {'Content-Type': 'application/json; charset=UTF-8'},
//         body: json.encode(body),
//       );

//       final result = json.decode(utf8.decode(response.bodyBytes));
      
//       print('Status Code da Sincronização: ${response.statusCode}');
//       print('Resposta da Sincronização: $result');

//       if (response.statusCode == 200 && result['status'] == 'success') {
//         return result['message'];
//       } else {
//         throw Exception(result['message'] ?? 'Ocorreu um erro desconhecido na API.');
//       }
//     } on SocketException {
//       throw Exception('Não foi possível conectar ao servidor. Verifique a sua internet.');
//     } catch (e) {
//       print('Erro capturado no ApiService: $e');
//       throw Exception(e.toString().replaceAll('Exception: ', ''));
//     }
//   }
// }

import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'package:flutter/foundation.dart';

class ApiService {
  static const String _baseUrl = 'https://projeto-skoob-automator-production.up.railway.app';
  static const int _timeoutSeconds = 90;
  static const int _maxRetries = 2;

  // Headers padrão para todas as requisições
  Map<String, String> get _defaultHeaders => {
    'Content-Type': 'application/json; charset=UTF-8',
    'Accept': 'application/json',
    'User-Agent': 'SkoobSync-Flutter/2.0',
  };

  /// Testa a conectividade com a API
  Future<Map<String, dynamic>> testConnection() async {
    try {
      final response = await http.get(
        Uri.parse('$_baseUrl/health'),
        headers: _defaultHeaders,
      ).timeout(
        const Duration(seconds: 10),
      );

      if (response.statusCode == 200) {
        return {
          'success': true,
          'data': json.decode(response.body),
        };
      } else {
        return {
          'success': false,
          'error': 'API retornou status ${response.statusCode}',
        };
      }
    } catch (e) {
      return {
        'success': false,
        'error': 'Erro de conexão: ${e.toString()}',
      };
    }
  }

  /// Executa uma requisição HTTP com retry automático
  Future<http.Response> _makeRequestWithRetry(
    Future<http.Response> Function() requestFunction,
    {int attempt = 1}
  ) async {
    try {
      final response = await requestFunction().timeout(
        const Duration(seconds: _timeoutSeconds),
      );
      
      // Log da resposta para debug
      if (kDebugMode) {
        print('📡 API Response [${response.statusCode}]: ${response.body.substring(0, response.body.length > 200 ? 200 : response.body.length)}...');
      }
      
      return response;
    } catch (e) {
      if (kDebugMode) {
        print('❌ Tentativa $attempt falhou: $e');
      }
      
      // Se não é a última tentativa e é um erro de rede, tenta novamente
      if (attempt < _maxRetries && 
          (e is SocketException || 
           e is HttpException || 
           e.toString().contains('timeout'))) {
        
        final delaySeconds = attempt * 2; // Delay progressivo
        if (kDebugMode) {
          print('⏳ Aguardando ${delaySeconds}s antes da próxima tentativa...');
        }
        
        await Future.delayed(Duration(seconds: delaySeconds));
        return _makeRequestWithRetry(requestFunction, attempt: attempt + 1);
      }
      
      rethrow; // Se não pode tentar novamente, relança o erro
    }
  }

  /// Valida os dados de entrada antes de enviar para a API
  Map<String, String> _validateSyncData({
    required String? skoobUser,
    required String? skoobPass,
    required String? readwiseToken,
    required String bookTitle,
    required int statusId,
  }) {
    final errors = <String>[];

    if (skoobUser == null || skoobUser.trim().isEmpty) {
      errors.add('Email do Skoob é obrigatório');
    } else if (!skoobUser.contains('@')) {
      errors.add('Email do Skoob parece inválido');
    }

    if (skoobPass == null || skoobPass.trim().isEmpty) {
      errors.add('Senha do Skoob é obrigatória');
    } else if (skoobPass.length < 3) {
      errors.add('Senha do Skoob muito curta');
    }

    if (readwiseToken == null || readwiseToken.trim().isEmpty) {
      errors.add('Token do Readwise é obrigatório');
    } else if (readwiseToken.length < 10) {
      errors.add('Token do Readwise parece inválido');
    }

    if (bookTitle.trim().isEmpty) {
      errors.add('Título do livro é obrigatório');
    } else if (bookTitle.trim().length < 2) {
      errors.add('Título do livro muito curto');
    }

    if (statusId < 1 || statusId > 5) {
      errors.add('Status ID deve estar entre 1 e 5');
    }

    if (errors.isNotEmpty) {
      throw ValidationException(errors.join('; '));
    }

    return {
      'skoob_user': skoobUser!.trim(),
      'skoob_pass': skoobPass!.trim(),
      'readwise_token': readwiseToken!.trim(),
      'book_title': bookTitle.trim(),
      'status_id': statusId.toString(),
    };
  }

  /// Método principal para sincronização do progresso
  Future<SyncResult> syncSkoobProgress({
    required String? skoobUser,
    required String? skoobPass,
    required String? readwiseToken,
    required String bookTitle,
    required int statusId,
  }) async {
    if (kDebugMode) {
      print('🚀 Iniciando sincronização para: "$bookTitle"');
    }

    try {
      // Valida os dados
      final validatedData = _validateSyncData(
        skoobUser: skoobUser,
        skoobPass: skoobPass,
        readwiseToken: readwiseToken,
        bookTitle: bookTitle,
        statusId: statusId,
      );

      final syncUri = Uri.parse('$_baseUrl/sync');
      
      // Monta o body da requisição
      final body = {
        'skoob_user': validatedData['skoob_user']!,
        'skoob_pass': validatedData['skoob_pass']!,
        'readwise_token': validatedData['readwise_token']!,
        'book_title': validatedData['book_title']!,
        'status_id': int.parse(validatedData['status_id']!),
      };

      if (kDebugMode) {
        print('📤 Enviando dados: ${body.keys.join(', ')}');
      }

      // Faz a requisição com retry
      final response = await _makeRequestWithRetry(() {
        return http.post(
          syncUri,
          headers: _defaultHeaders,
          body: json.encode(body),
        );
      });

      // Decodifica a resposta
      final Map<String, dynamic> result;
      try {
        final responseBody = utf8.decode(response.bodyBytes);
        result = json.decode(responseBody) as Map<String, dynamic>;
      } catch (e) {
        throw ApiException('Resposta da API inválida: ${e.toString()}');
      }

      if (kDebugMode) {
        print('📊 Status da sincronização: ${response.statusCode}');
        print('📋 Resposta: ${result['status']} - ${result['message']}');
      }

      // Processa a resposta baseada no status code
      if (response.statusCode == 200 && result['status'] == 'success') {
        return SyncResult.success(
          message: result['message'] ?? 'Sincronização realizada com sucesso!',
          details: result['details'],
        );
      } else {
        // Trata diferentes tipos de erro
        String errorMessage = result['message'] ?? 'Erro desconhecido';
        
        switch (response.statusCode) {
          case 400:
            throw ValidationException(errorMessage);
          case 401:
            throw AuthenticationException(errorMessage);
          case 408:
            throw TimeoutException(errorMessage);
          case 500:
            throw ServerException(errorMessage);
          default:
            throw ApiException('Erro HTTP ${response.statusCode}: $errorMessage');
        }
      }

    } on ValidationException {
      rethrow;
    } on AuthenticationException {
      rethrow;
    } on TimeoutException {
      rethrow;
    } on ServerException {
      rethrow;
    } on ApiException {
      rethrow;
    } on SocketException {
      throw ConnectionException('Sem conexão com a internet. Verifique sua rede.');
    } on HttpException {
      throw ConnectionException('Erro de rede. Tente novamente.');
    } catch (e) {
      if (kDebugMode) {
        print('🚨 Erro não tratado: $e');
      }
      
      String errorMessage = e.toString();
      if (errorMessage.contains('timeout')) {
        throw TimeoutException('A operação demorou muito tempo. Tente novamente.');
      } else if (errorMessage.contains('connection')) {
        throw ConnectionException('Erro de conexão. Verifique sua internet.');
      } else {
        throw ApiException('Erro inesperado: ${errorMessage.replaceAll('Exception: ', '')}');
      }
    }
  }
}

/// Resultado da operação de sincronização
class SyncResult {
  final bool isSuccess;
  final String message;
  final Map<String, dynamic>? details;
  final String? error;

  SyncResult._({
    required this.isSuccess,
    required this.message,
    this.details,
    this.error,
  });

  factory SyncResult.success({
    required String message,
    Map<String, dynamic>? details,
  }) {
    return SyncResult._(
      isSuccess: true,
      message: message,
      details: details,
    );
  }

  factory SyncResult.error({
    required String error,
  }) {
    return SyncResult._(
      isSuccess: false,
      message: error,
      error: error,
    );
  }

  @override
  String toString() {
    return 'SyncResult(isSuccess: $isSuccess, message: $message)';
  }
}

/// Exceções customizadas
abstract class SkoobSyncException implements Exception {
  final String message;
  const SkoobSyncException(this.message);
  
  @override
  String toString() => message;
}

class ValidationException extends SkoobSyncException {
  const ValidationException(super.message);
}

class AuthenticationException extends SkoobSyncException {
  const AuthenticationException(super.message);
}

class ConnectionException extends SkoobSyncException {
  const ConnectionException(super.message);
}

class TimeoutException extends SkoobSyncException {
  const TimeoutException(super.message);
}

class ServerException extends SkoobSyncException {
  const ServerException(super.message);
}

class ApiException extends SkoobSyncException {
  const ApiException(super.message);
}